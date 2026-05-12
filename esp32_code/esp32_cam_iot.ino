"""
Código Arduino para ESP32 + CAM
Compila con PlatformIO o Arduino IDE
Placa: ESP32 Wrover Module
"""

#include <Arduino.h>
#include <WiFi.h>
#include <esp_camera.h>
#include <WebServer.h>
#include <PubSubClient.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// ─── CONFIGURACIÓN DE PINES ───────────────────────────

// Camera
#define PWDN_GPIO_NUM    32
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27
#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22

// ADC Sensores
#define ADC_PH_PIN       35   // ADC1_CH7 - UIUZMAR pH
#define ADC_EC_PIN       34   // ADC1_CH6 - Sensor EC (resistencia)
#define ADC_TDS_PIN      39   // ADC1_CH3 - Sensor TDS

// Actuadores
#define RELAY_RIEGO_PIN  12   // GPIO12 - Válvula riego
#define RELAY_OZONO_PIN  14   // GPIO14 - Bomba ozono

// Temperatura (1-Wire)
#define TEMP_PIN         13   // GPIO13 - DS18B20

// ─── VARIABLES GLOBALES ───────────────────────────

WiFiClient espClient;
PubSubClient mqttClient(espClient);
WebServer webServer(8074);
OneWire oneWire(TEMP_PIN);
DallasTemperature sensors(&oneWire);

// IDs y configuración
const char* ESP32_ID = "CAX21-MAIN";
const char* SSID = "CASTUO_NETWORK";
const char* PASSWORD = "SabiondaSoberana2024";
const char* MQTT_SERVER = "localhost";
const int MQTT_PORT = 1883;

// Calibración de sensores
struct SensorCalibration {
  float ph_offset = 0.0;      // Ajuste de pH
  float ph_scale = 1.0;       // Factor de escala pH
  float ec_offset = 0.0;      // Ajuste EC
  float ec_scale = 1.0;       // Factor EC
  float tds_offset = 0.0;     // Ajuste TDS
  float tds_scale = 1.0;      // Factor TDS
} calibration;

// Estado de actuadores
struct ActuatorState {
  bool riego_on = false;
  bool ozono_on = false;
  unsigned long riego_start_time = 0;
  unsigned long ozono_start_time = 0;
  int riego_duration_max = 300;  // 5 min máximo
  int ozono_duration_max = 120;  // 2 min máximo
} actuator_state;

// ─── SETUP CÁMARA ───────────────────────────────

void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sda = SIOD_GPIO_NUM;
  config.pin_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 10;
  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }
  Serial.println("✅ Camera initialized");
}

// ─── SETUP MQTT ───────────────────────────────

void setupMQTT() {
  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setCallback(onMQTTMessage);
}

void reconnectMQTT() {
  int attempts = 0;
  while (!mqttClient.connected() && attempts < 3) {
    Serial.print("Connecting to MQTT...");
    if (mqttClient.connect(ESP32_ID)) {
      Serial.println("✅ Connected!");
      // Suscribirse a control commands
      mqttClient.subscribe("castuo/control/riego");
      mqttClient.subscribe("castuo/control/ozono");
    } else {
      delay(500);
      attempts++;
    }
  }
}

void onMQTTMessage(char* topic, byte* payload, unsigned int length) {
  String message = String((char*)payload).substring(0, length);
  Serial.printf("MQTT: %s = %s\n", topic, message.c_str());
  
  if (String(topic) == "castuo/control/riego") {
    if (message == "on") {
      activateRiego(60);  // 1 min si sin duración
    } else {
      deactivateRiego();
    }
  } else if (String(topic) == "castuo/control/ozono") {
    if (message == "on") {
      activateOzono(30);
    } else {
      deactivateOzono();
    }
  }
}

// ─── LECTURA DE SENSORES ───────────────────────────

float readPH() {
  int raw = analogRead(ADC_PH_PIN);
  float voltage = (raw / 4095.0) * 3.3;
  float ph = (voltage - 2.5) / 0.18;  // Fórmula típica UIUZMAR
  return (ph * calibration.ph_scale) + calibration.ph_offset;
}

float readEC() {
  int raw = analogRead(ADC_EC_PIN);
  float voltage = (raw / 4095.0) * 3.3;
  // EC sensor: típicamente 0-2000 µS/cm
  float ec = (voltage / 3.3) * 2000.0;
  return (ec * calibration.ec_scale) + calibration.ec_offset;
}

float readTDS() {
  int raw = analogRead(ADC_TDS_PIN);
  float voltage = (raw / 4095.0) * 3.3;
  // TDS = (voltage / 3.3) * 1000 ppm (aproximado)
  float tds = (voltage / 3.3) * 1000.0;
  return (tds * calibration.tds_scale) + calibration.tds_offset;
}

float readTemperature() {
  sensors.requestTemperatures();
  return sensors.getTempCByIndex(0);
}

float readWiFiSignal() {
  return WiFi.RSSI();  // dBm
}

// ─── CONTROL DE ACTUADORES ───────────────────────────

void activateRiego(int duration_seconds) {
  if (duration_seconds > actuator_state.riego_duration_max) {
    duration_seconds = actuator_state.riego_duration_max;
  }
  digitalWrite(RELAY_RIEGO_PIN, HIGH);
  actuator_state.riego_on = true;
  actuator_state.riego_start_time = millis();
  Serial.printf("💧 RIEGO ON (duration: %ds)\n", duration_seconds);
}

void deactivateRiego() {
  digitalWrite(RELAY_RIEGO_PIN, LOW);
  actuator_state.riego_on = false;
  Serial.println("💧 RIEGO OFF");
}

void activateOzono(int duration_seconds) {
  if (duration_seconds > actuator_state.ozono_duration_max) {
    duration_seconds = actuator_state.ozono_duration_max;
  }
  digitalWrite(RELAY_OZONO_PIN, HIGH);
  actuator_state.ozono_on = true;
  actuator_state.ozono_start_time = millis();
  Serial.printf("💨 OZONO ON (duration: %ds)\n", duration_seconds);
}

void deactivateOzono() {
  digitalWrite(RELAY_OZONO_PIN, LOW);
  actuator_state.ozono_on = false;
  Serial.println("💨 OZONO OFF");
}

// Autoreverso de tiempo límite
void checkActuatorTimeouts() {
  unsigned long now = millis();
  
  if (actuator_state.riego_on && 
      (now - actuator_state.riego_start_time) > (actuator_state.riego_duration_max * 1000)) {
    deactivateRiego();
    Serial.println("⚠️ RIEGO timeout auto-off");
  }
  
  if (actuator_state.ozono_on && 
      (now - actuator_state.ozono_start_time) > (actuator_state.ozono_duration_max * 1000)) {
    deactivateOzono();
    Serial.println("⚠️ OZONO timeout auto-off");
  }
}

// ─── ENDPOINTS HTTP ───────────────────────────

void handleCapture() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    webServer.send(500, "text/plain", "Camera capture failed");
    return;
  }
  
  webServer.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
  webServer.send(200, "image/jpeg", (const char *)fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

void handleStream() {
  WiFiClient client = webServer.client();
  
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: multipart/x-mixed-replace; boundary=frame");
  client.println("Connection: close");
  client.println();
  
  while (true) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      break;
    }
    
    client.print("--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ");
    client.println(fb->len);
    client.println();
    client.write(fb->buf, fb->len);
    client.println();
    
    esp_camera_fb_return(fb);
    
    if (!client.connected()) break;
    delay(10);
  }
}

void handleSensorData() {
  float ph = readPH();
  float ec = readEC();
  float tds = readTDS();
  float temp = readTemperature();
  float rssi = readWiFiSignal();
  
  String json = String("{\
    \"esp32_id\":\"") + ESP32_ID + String("\",\
    \"ph\":") + String(ph) + String(",\
    \"ec\":") + String(ec) + String(",\
    \"tds\":") + String(tds) + String(",\
    \"temperature_c\":") + String(temp) + String(",\
    \"wifi_rssi\":") + String((int)rssi) + String(",\
    \"timestamp\":\"") + String(millis()) + String("\"\
  }");
  
  webServer.send(200, "application/json", json);
}

void handleControl() {
  if (!webServer.hasArg("plain")) {
    webServer.send(400, "text/plain", "No body");
    return;
  }
  
  String body = webServer.arg("plain");
  
  // Simple JSON parsing (para producción usar ArduinoJson)
  if (body.indexOf("\"actuator\":\"riego\"") > -1) {
    if (body.indexOf("\"action\":\"on\"") > -1) {
      activateRiego(60);
    } else {
      deactivateRiego();
    }
  } else if (body.indexOf("\"actuator\":\"ozono\"") > -1) {
    if (body.indexOf("\"action\":\"on\"") > -1) {
      activateOzono(30);
    } else {
      deactivateOzono();
    }
  }
  
  webServer.send(200, "application/json", "{\"status\":\"ok\"}");
}

void handleStatus() {
  String json = String("{\
    \"esp32_id\":\"") + ESP32_ID + String("\",\
    \"uptime_ms\":") + String(millis()) + String(",\
    \"wifi_connected\":") + String(WiFi.isConnected() ? "true" : "false") + String(",\
    \"mqtt_connected\":") + String(mqttClient.connected() ? "true" : "false") + String(",\
    \"riego_on\":") + String(actuator_state.riego_on ? "true" : "false") + String(",\
    \"ozono_on\":") + String(actuator_state.ozono_on ? "true" : "false") + String("\
  }");
  
  webServer.send(200, "application/json", json);
}

// ─── SETUP ───────────────────────────────

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=== ESP32-CAM + IoT Sensors ===");
  
  // GPIO
  pinMode(RELAY_RIEGO_PIN, OUTPUT);
  pinMode(RELAY_OZONO_PIN, OUTPUT);
  digitalWrite(RELAY_RIEGO_PIN, LOW);
  digitalWrite(RELAY_OZONO_PIN, LOW);
  
  // Sensores
  sensors.begin();  // DS18B20
  
  // Cámara
  initCamera();
  
  // WiFi
  WiFi.begin(SSID, PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.isConnected()) {
    Serial.println("\n✅ WiFi Connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n⚠️ WiFi Failed, starting softAP...");
    WiFi.softAP("CASTUO-BACKUP-CAX21", "CastuwConnect2024");
  }
  
  // HTTP Server
  webServer.on("/stream", HTTP_GET, handleStream);
  webServer.on("/capture", HTTP_GET, handleCapture);
  webServer.on("/sensors", HTTP_GET, handleSensorData);
  webServer.on("/control", HTTP_POST, handleControl);
  webServer.on("/status", HTTP_GET, handleStatus);
  webServer.begin();
  Serial.println("✅ HTTP Server started on port 8074");
  
  // MQTT (opcional, no recomendado para video)
  setupMQTT();
  
  Serial.println("=== SETUP COMPLETE ===\n");
}

// ─── LOOP ───────────────────────────────

void loop() {
  webServer.handleClient();
  
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  checkActuatorTimeouts();
  
  // Delay pequeño
  delay(10);
}
