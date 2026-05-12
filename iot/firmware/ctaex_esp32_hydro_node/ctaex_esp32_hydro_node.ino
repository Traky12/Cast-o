/**
 * CTAEX hidro — telemetría MQTT hacia CASTÚO / n8n (prototipo).
 * - Ajustar pines, calibración pH/EC y factor lux→PAR en campo.
 * - Control local de riego: solo como demostración; en producción usar límites de tiempo,
 *   sensores de nivel y política OT (no sustituye revisión agronómica).
 */
#if __has_include("secrets.h")
#include "secrets.h"
#endif
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <BH1750.h>
#include <DHT.h>

// Copiar desde secrets.h (gitignored) o definir en build flags
#ifndef WIFI_SSID
#define WIFI_SSID "CAMBIA_SSID"
#endif
#ifndef WIFI_PASS
#define WIFI_PASS "CAMBIA_PASS"
#endif
#ifndef MQTT_HOST
#define MQTT_HOST "192.168.1.50"
#endif
#ifndef MQTT_PORT
#define MQTT_PORT 1883
#endif
#ifndef MQTT_USER
#define MQTT_USER ""
#endif
#ifndef MQTT_PASS
#define MQTT_PASS ""
#endif
#ifndef BED_ID
#define BED_ID "B01"
#endif

#define DHTPIN 4
#define DHTTYPE DHT22
#define PIN_PH 34
#define PIN_EC 35
#define PIN_RIEGO 25
#define PIN_ORP 36
#define CO2_RX 16
#define CO2_TX 17

const unsigned long TELEMETRY_MS = 60000;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
DHT dht(DHTPIN, DHTTYPE);
BH1750 lightMeter;
HardwareSerial co2Serial(2);

static char topicTelemetry[64];
static char topicCommand[64];
static char topicWaterEvent[72];

float readAvgVolts(int pin) {
  uint32_t acc = 0;
  for (int i = 0; i < 16; i++) {
    acc += analogRead(pin);
    delay(2);
  }
  return (acc / 16.0f) * (3.3f / 4095.0f);
}

/** ORP estimado (mV): calibrar con hoja de datos del módulo/sonda; signo y ganancia varían. */
float orpMvFromAdcVolts(float v) {
  return (2.5f - v) * 1000.0f;
}

float readPhVolts() {
  uint32_t acc = 0;
  for (int i = 0; i < 16; i++) {
    acc += analogRead(PIN_PH);
    delay(2);
  }
  float v = (acc / 16.0f) * (3.3f / 4095.0f);
  return v;
}

float voltsToPh(float v) {
  // Calibración de dos puntos en campo (buffer pH4 / pH7 típico)
  const float neutralV = 1.65f;
  const float slope = -3.3f;
  return 7.0f + (neutralV - v) * slope;
}

float readEcMs() {
  uint32_t acc = 0;
  for (int i = 0; i < 16; i++) {
    acc += analogRead(PIN_EC);
    delay(2);
  }
  float v = (acc / 16.0f) * (3.3f / 4095.0f);
  // Placeholder: mapear V → mS/cm con calibración K=1 y temperatura de solución
  return v * 2.0f;
}

uint8_t mh19Checksum(const uint8_t* p) {
  uint8_t s = 0;
  for (int i = 1; i < 8; i++) s += p[i];
  return (uint8_t)(0xFF - s + 1);
}

int readCo2Ppm() {
  while (co2Serial.available()) co2Serial.read();
  uint8_t cmd[9] = {0xFF, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
  cmd[8] = mh19Checksum(cmd);
  co2Serial.write(cmd, 9);
  delay(120);
  uint8_t buf[9];
  unsigned long t0 = millis();
  int n = 0;
  while (millis() - t0 < 200 && n < 9) {
    if (co2Serial.available()) buf[n++] = co2Serial.read();
  }
  if (n < 9) return -1;
  if (buf[0] == 0xFF && buf[1] == 0x86) {
    int ppm = (int)buf[2] * 256 + (int)buf[3];
    return ppm;
  }
  return -1;
}

void setupPins() {
  pinMode(PIN_RIEGO, OUTPUT);
  digitalWrite(PIN_RIEGO, LOW);
}

void connectWifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void connectMqtt() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  while (!mqtt.connected()) {
    String cid = String("ctaex-") + BED_ID;
    bool ok;
    if (strlen(MQTT_USER) > 0) {
      ok = mqtt.connect(cid.c_str(), MQTT_USER, MQTT_PASS);
    } else {
      ok = mqtt.connect(cid.c_str());
    }
    if (ok) break;
    delay(2000);
  }
}

void publishTelemetry(JsonDocument& doc) {
  char buf[640];
  size_t n = serializeJson(doc, buf, sizeof(buf));
  if (n == 0 || n >= sizeof(buf)) return;
  mqtt.publish(topicTelemetry, (const uint8_t*)buf, n, false);
}

/** Evento ORP bajo (debounce); el arranque de ozono debe hacerlo relé/PLC vía n8n u otro nodo. */
void maybePublishOrpLow(float orp_mv_est, float orp_adc_v) {
  static unsigned long lastEv = 0;
  if (orp_mv_est >= 600.0f || orp_mv_est < 50.0f) return;
  unsigned long t = millis();
  if (t - lastEv < 300000UL) return;
  lastEv = t;
  StaticJsonDocument<160> d;
  d["alert"] = "orp_low";
  d["orp_mv_est"] = orp_mv_est;
  d["orp_adc_v"] = orp_adc_v;
  d["bed_id"] = BED_ID;
  char b[200];
  size_t n = serializeJson(d, b, sizeof(b));
  if (n > 0 && n < sizeof(b)) {
    mqtt.publish(topicWaterEvent, (const uint8_t*)b, (unsigned int)n, false);
  }
}

void localFailsafeRiego(float ec_ms) {
  // Demo: si EC muy bajo, activar riego un pulso corto (evitar ON continuo)
  static unsigned long lastPulse = 0;
  if (ec_ms < 1.8f && ec_ms > 0.05f) {
    unsigned long now = millis();
    if (now - lastPulse > 120000UL) {
      digitalWrite(PIN_RIEGO, HIGH);
      delay(5000);
      digitalWrite(PIN_RIEGO, LOW);
      lastPulse = now;
    }
  }
}

void setup() {
  Serial.begin(115200);
  setupPins();
  dht.begin();
  Wire.begin();
  lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
  co2Serial.begin(9600, SERIAL_8N1, CO2_RX, CO2_TX);

  snprintf(topicTelemetry, sizeof(topicTelemetry), "castuo/ctaex/%s/telemetry", BED_ID);
  snprintf(topicCommand, sizeof(topicCommand), "castuo/ctaex/%s/command", BED_ID);
  snprintf(topicWaterEvent, sizeof(topicWaterEvent), "castuo/ctaex/%s/water/event", BED_ID);

  connectWifi();
  connectMqtt();
}

void loop() {
  if (!mqtt.connected()) connectMqtt();
  mqtt.loop();

  static unsigned long last = 0;
  unsigned long now = millis();
  if (now - last < TELEMETRY_MS) {
    delay(10);
    return;
  }
  last = now;

  float t = dht.readTemperature();
  float h = dht.readHumidity();
  float lux = lightMeter.readLightLevel();
  float vph = readPhVolts();
  float ph = voltsToPh(vph);
  float ec = readEcMs();
  int co2 = readCo2Ppm();
  float v_orp = readAvgVolts(PIN_ORP);
  float orp_mv_est = orpMvFromAdcVolts(v_orp);

  // Aproximación orientativa (NO es PAR espectrorradiométrico)
  float par_umol_approx = lux * 0.0185f;

  StaticJsonDocument<512> doc;
  doc["node"] = BED_ID;
  doc["bed_id"] = BED_ID;
  doc["action"] = "control_hidro";
  if (!isnan(ph)) doc["ph"] = ph;
  doc["ec_ms"] = ec;
  if (!isnan(t)) doc["temp_c"] = t;
  if (!isnan(h)) doc["hum_pct"] = h;
  doc["co2_ppm"] = co2;
  doc["lux"] = lux;
  doc["par_umol_approx"] = par_umol_approx;
  doc["orp_adc_v"] = v_orp;
  doc["orp_mv_est"] = orp_mv_est;
  doc["uptime_ms"] = now;

  publishTelemetry(doc);
  maybePublishOrpLow(orp_mv_est, v_orp);

  localFailsafeRiego(ec);
}
