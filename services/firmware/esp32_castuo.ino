/**
 * CASTÚO-SYSTEM™ v3.1 — Firmware ESP32-S3-CAM (CTAEX Completo)
 * Board:   Waveshare ESP32-S3-CAM-OV5640
 * IDE:     Arduino IDE 2.x
 * Core:    https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
 * Board:   Waveshare ESP32-S3-CAM  (Tools → Board → ESP32 Arduino)
 * Upload:  USB CDC On Boot (Native USB)  |  Port: /dev/ttyACM0 (Linux) / COMx (Windows)
 *
 * Sensores integrados:
 *   DHT22       → GPIO 4   (temp + humedad aire)
 *   KY-018 LDR  → GPIO 34  (luz ambiental)
 *   pH analógico→ GPIO 35  (Atlas Scientific o módulo ADS)
 *   DR.METER    → GPIO 36  (humedad suelo)
 *   OV5640      → Waveshare S3-CAM pinout (MJPEG stream + captura)
 *   Relé 1      → GPIO 5   (bomba riego)
 *   Relé 2      → GPIO 18  (ventilador)
 *   Relé 3      → GPIO 19  (luces LED)
 *
 * MQTT-TLS: mqtt.ctaex.es:8883
 * Topics:
 *   castuo/ctaex/sensor01        → telemetría (publicar)
 *   castuo/ctaex/camera          → metadatos de captura (publicar)
 *   castuo/ctaex/control/sensor01→ comandos relé + captura (suscribir)
 *   castuo/ctaex/control/ack     → confirmaciones (publicar)
 *   castuo/ctaex/status          → estado online/offline (publicar)
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include <ArduinoOTA.h>
#include <esp_task_wdt.h>
#include <time.h>

// ── Credenciales WiFi (define en secrets.h o con build flags) ────────────────
#ifndef WIFI_SSID
  #define WIFI_SSID     "tu_wifi"
#endif
#ifndef WIFI_PASS
  #define WIFI_PASS     "tu_contraseña_wifi"
#endif

// ── MQTT CTAEX ───────────────────────────────────────────────────────────────
const char* mqtt_server   = "mqtt.ctaex.es";
const int   mqtt_port     = 8883;
const char* mqtt_user     = "usuario_ctaex";
const char* mqtt_password = "contraseña_segura";

const char* mqtt_topic_sensors = "castuo/ctaex/sensor01";
const char* mqtt_topic_camera  = "castuo/ctaex/camera";
const char* mqtt_topic_control = "castuo/ctaex/control/sensor01";
const char* mqtt_topic_ack     = "castuo/ctaex/control/ack";
const char* mqtt_topic_status  = "castuo/ctaex/status";

// Certificado CA del broker CTAEX (reemplazar con el certificado real)
const char* mqtt_ca_cert = \
"-----BEGIN CERTIFICATE-----\n"
"MIIDdzCCAl+gAwIBAgIEAgAAuTANBgkqhkiG9w0BAQsFADBaMQswCQYDVQQGEwJJ\n"
"... (reemplazar con certificado CA real de mqtt.ctaex.es) ...\n"
"-----END CERTIFICATE-----\n";

// ── Pinout Waveshare ESP32-S3-CAM OV5640 ─────────────────────────────────────
#define PWDN_GPIO_NUM    -1
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    10
#define SIOD_GPIO_NUM    40
#define SIOC_GPIO_NUM    39
#define Y9_GPIO_NUM      48
#define Y8_GPIO_NUM      11
#define Y7_GPIO_NUM      12
#define Y6_GPIO_NUM      14
#define Y5_GPIO_NUM      16
#define Y4_GPIO_NUM      17
#define Y3_GPIO_NUM      15
#define Y2_GPIO_NUM      13
#define VSYNC_GPIO_NUM    8
#define HREF_GPIO_NUM    47
#define PCLK_GPIO_NUM    42

// ── Sensores ─────────────────────────────────────────────────────────────────
#define DHTPIN           4
#define DHTTYPE          DHT22
#define LDR_PIN         34
#define PH_PIN          35
#define SOIL_PIN        36

// ── Actuadores ───────────────────────────────────────────────────────────────
#define RELAY_1_PIN      5   // bomba riego
#define RELAY_2_PIN     18   // ventilador
#define RELAY_3_PIN     19   // luces LED

// ── Constantes ────────────────────────────────────────────────────────────────
#define WDT_TIMEOUT_S   30
#define SEND_INTERVAL   60000UL   // 60 s entre lecturas
#define NTP_SERVER      "pool.ntp.org"
#define DEVICE_ID       "sensor01"
#define ZONE            "A"

// ── Objetos globales ─────────────────────────────────────────────────────────
DHT dht(DHTPIN, DHTTYPE);
WiFiClientSecure espClient;
PubSubClient client(espClient);
httpd_handle_t  camServer = nullptr;

unsigned long lastSend    = 0;
unsigned long lastMqttTry = 0;

// ── Cámara: handler MJPEG stream ──────────────────────────────────────────────
static esp_err_t streamHandler(httpd_req_t *req) {
  camera_fb_t *fb = nullptr;
  char part[64];
  static const char* BOUND = "\r\n--frame\r\n";
  static const char* CT    = "multipart/x-mixed-replace;boundary=frame";
  static const char* PART  = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

  httpd_resp_set_type(req, CT);
  while (true) {
    fb = esp_camera_fb_get();
    if (!fb) break;
    httpd_resp_send_chunk(req, BOUND, strlen(BOUND));
    size_t hlen = snprintf(part, sizeof(part), PART, fb->len);
    httpd_resp_send_chunk(req, part, hlen);
    httpd_resp_send_chunk(req, (const char*)fb->buf, fb->len);
    esp_camera_fb_return(fb);
  }
  return ESP_OK;
}

static esp_err_t captureHandler(httpd_req_t *req) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) { httpd_resp_send_500(req); return ESP_FAIL; }
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Content-Disposition", "inline; filename=capture.jpg");
  esp_err_t res = httpd_resp_send(req, (const char*)fb->buf, fb->len);
  esp_camera_fb_return(fb);
  return res;
}

void startCameraServer() {
  httpd_config_t cfg = HTTPD_DEFAULT_CONFIG();
  cfg.server_port = 80;
  if (httpd_start(&camServer, &cfg) == ESP_OK) {
    httpd_uri_t s = { "/stream",  HTTP_GET, streamHandler,  nullptr };
    httpd_uri_t c = { "/capture", HTTP_GET, captureHandler, nullptr };
    httpd_register_uri_handler(camServer, &s);
    httpd_register_uri_handler(camServer, &c);
    Serial.printf("[CAM] http://%s/stream\n", WiFi.localIP().toString().c_str());
  }
}

// ── Cámara: captura y publica metadatos ──────────────────────────────────────
void captureAndPublish() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) { Serial.println("[CAM] Error captura"); return; }

  StaticJsonDocument<256> doc;
  doc["sensor_id"]  = DEVICE_ID;
  doc["zone"]       = ZONE;
  doc["image_size"] = fb->len;
  doc["timestamp"]  = (uint32_t)(millis() / 1000);
  doc["url"]        = "http://" + WiFi.localIP().toString() + "/capture";

  char payload[256];
  serializeJson(doc, payload);
  client.publish(mqtt_topic_camera, payload);
  esp_camera_fb_return(fb);
  Serial.printf("[CAM] Captura publicada: %u bytes\n", fb->len);
}

// ── Cámara: init ─────────────────────────────────────────────────────────────
bool initCamera() {
  camera_config_t cfg = {};
  cfg.ledc_channel = LEDC_CHANNEL_0;
  cfg.ledc_timer   = LEDC_TIMER_0;
  cfg.pin_d0 = Y2_GPIO_NUM; cfg.pin_d1 = Y3_GPIO_NUM;
  cfg.pin_d2 = Y4_GPIO_NUM; cfg.pin_d3 = Y5_GPIO_NUM;
  cfg.pin_d4 = Y6_GPIO_NUM; cfg.pin_d5 = Y7_GPIO_NUM;
  cfg.pin_d6 = Y8_GPIO_NUM; cfg.pin_d7 = Y9_GPIO_NUM;
  cfg.pin_xclk     = XCLK_GPIO_NUM;
  cfg.pin_pclk     = PCLK_GPIO_NUM;
  cfg.pin_vsync    = VSYNC_GPIO_NUM;
  cfg.pin_href     = HREF_GPIO_NUM;
  cfg.pin_sscb_sda = SIOD_GPIO_NUM;
  cfg.pin_sscb_scl = SIOC_GPIO_NUM;
  cfg.pin_pwdn     = PWDN_GPIO_NUM;
  cfg.pin_reset    = RESET_GPIO_NUM;
  cfg.xclk_freq_hz = 20000000;
  cfg.pixel_format = PIXFORMAT_JPEG;
  cfg.frame_size   = psramFound() ? FRAMESIZE_UXGA : FRAMESIZE_SVGA;
  cfg.jpeg_quality = 10;
  cfg.fb_count     = 2;

  if (esp_camera_init(&cfg) != ESP_OK) {
    Serial.println("[CAM] Init fallida");
    return false;
  }
  Serial.println("[CAM] OV5640 OK");
  return true;
}

// ── MQTT callback (comandos remotos) ─────────────────────────────────────────
void callback(char* topic, byte* payload, unsigned int length) {
  char buf[length + 1];
  memcpy(buf, payload, length);
  buf[length] = '\0';

  Serial.printf("[MQTT] ← %s: %s\n", topic, buf);

  StaticJsonDocument<256> doc;
  if (deserializeJson(doc, buf) != DeserializationError::Ok) return;

  if (String(topic) == mqtt_topic_control) {
    // Control de relés: {"relay":1,"on":true}
    if (doc.containsKey("relay") && doc.containsKey("on")) {
      int  relay = doc["relay"];
      bool on    = doc["on"];
      int  pin   = (relay == 1) ? RELAY_1_PIN : (relay == 2) ? RELAY_2_PIN : RELAY_3_PIN;
      const char* nombre = (relay == 1) ? "bomba" : (relay == 2) ? "ventilador" : "luces";
      digitalWrite(pin, on ? HIGH : LOW);
      Serial.printf("[RELAY] %d (%s): %s\n", relay, nombre, on ? "ON" : "OFF");

      // ACK
      StaticJsonDocument<128> ack;
      ack["sensor_id"] = DEVICE_ID;
      ack["relay"]     = relay;
      ack["status"]    = on ? "on" : "off";
      char ackBuf[128];
      serializeJson(ack, ackBuf);
      client.publish(mqtt_topic_ack, ackBuf);
    }
    // Captura de imagen: {"capture_image":true}
    if (doc["capture_image"] == true) {
      captureAndPublish();
    }
  }
}

// ── MQTT reconexión ───────────────────────────────────────────────────────────
void mqttReconnect() {
  unsigned long now = millis();
  if (now - lastMqttTry < 5000UL) return;
  lastMqttTry = now;

  Serial.print("[MQTT] Conectando...");
  if (client.connect("ESP32_CASTUO_" DEVICE_ID, mqtt_user, mqtt_password)) {
    Serial.println(" OK");
    client.subscribe(mqtt_topic_control);

    StaticJsonDocument<128> doc;
    doc["sensor_id"] = DEVICE_ID;
    doc["zone"]      = ZONE;
    doc["status"]    = "online";
    doc["ip"]        = WiFi.localIP().toString();
    char buf[128];
    serializeJson(doc, buf);
    client.publish(mqtt_topic_status, buf, /*retain=*/true);
  } else {
    Serial.printf(" rc=%d\n", client.state());
  }
}

// ── Leer y publicar sensores ──────────────────────────────────────────────────
void publishSensors() {
  float humidity    = dht.readHumidity();
  float temperature = dht.readTemperature();
  int   ldr         = analogRead(LDR_PIN);
  int   phRaw       = analogRead(PH_PIN);
  int   soilRaw     = analogRead(SOIL_PIN);

  // Conversión pH: ajustar offset/slope según calibración del módulo
  float ph           = map(phRaw, 0, 4095, 0, 1400) / 100.0f;
  // Humedad suelo: 0% = seco (4095), 100% = saturado (~1200)
  float soilMoisture = map(constrain(soilRaw, 1200, 4095), 1200, 4095, 100, 0);

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("[DHT] Error lectura");
    return;
  }

  StaticJsonDocument<512> doc;
  doc["sensor_id"]    = DEVICE_ID;
  doc["zone"]         = ZONE;
  doc["temperature"]  = serialized(String(temperature, 1));
  doc["humidity"]     = serialized(String(humidity, 1));
  doc["ph"]           = serialized(String(ph, 2));
  doc["soil_moisture"]= serialized(String(soilMoisture, 1));
  doc["ldr"]          = ldr;
  doc["rssi"]         = WiFi.RSSI();
  doc["timestamp"]    = (uint32_t)(millis() / 1000);

  char payload[512];
  serializeJson(doc, payload);

  if (client.publish(mqtt_topic_sensors, payload)) {
    Serial.printf("[SENS] → %s\n", payload);
  } else {
    Serial.println("[SENS] Fallo publicación");
  }

  // Alertas automáticas locales
  if (ph < 5.5f || ph > 7.5f) {
    Serial.printf("[ALERT] pH fuera de rango: %.2f\n", ph);
  }
  if (soilMoisture < 30.0f) {
    Serial.println("[ALERT] Humedad suelo baja — activando bomba");
    digitalWrite(RELAY_1_PIN, HIGH);
    delay(5000);
    digitalWrite(RELAY_1_PIN, LOW);
  }
  if (temperature > 30.0f) {
    Serial.println("[ALERT] Temperatura alta — activando ventilador");
    digitalWrite(RELAY_2_PIN, HIGH);
  } else {
    digitalWrite(RELAY_2_PIN, LOW);
  }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n[BOOT] CASTÚO-SYSTEM™ v3.1 — ESP32-S3-CAM CTAEX");

  // Watchdog
  esp_task_wdt_init(WDT_TIMEOUT_S, true);
  esp_task_wdt_add(nullptr);

  // Actuadores
  pinMode(RELAY_1_PIN, OUTPUT); digitalWrite(RELAY_1_PIN, LOW);
  pinMode(RELAY_2_PIN, OUTPUT); digitalWrite(RELAY_2_PIN, LOW);
  pinMode(RELAY_3_PIN, OUTPUT); digitalWrite(RELAY_3_PIN, LOW);

  // Sensores
  dht.begin();
  pinMode(LDR_PIN,  INPUT);
  pinMode(PH_PIN,   INPUT);
  pinMode(SOIL_PIN, INPUT);

  // Cámara
  initCamera();

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("[WiFi] Conectando");
  int t = 0;
  while (WiFi.status() != WL_CONNECTED && t++ < 20) {
    delay(500); Serial.print('.');
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n[WiFi] IP: %s  RSSI: %d dBm\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
    configTime(0, 0, NTP_SERVER);
    startCameraServer();
  } else {
    Serial.println("\n[WiFi] Fallo — AP fallback CASTUO-SETUP");
    WiFi.softAP("CASTUO-SETUP", "castuo123");
  }

  // OTA
  ArduinoOTA.setHostname("castuo-" DEVICE_ID);
  ArduinoOTA.begin();

  // MQTT TLS
  espClient.setCACert(mqtt_ca_cert);
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  client.setBufferSize(1024);
  client.setKeepAlive(30);

  mqttReconnect();
  Serial.println("[BOOT] Listo\n");
}

// ── Loop ──────────────────────────────────────────────────────────────────────
void loop() {
  esp_task_wdt_reset();
  ArduinoOTA.handle();

  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
    delay(2000);
    return;
  }

  if (!client.connected()) mqttReconnect();
  client.loop();

  if (millis() - lastSend >= SEND_INTERVAL) {
    lastSend = millis();
    publishSensors();
  }
}
