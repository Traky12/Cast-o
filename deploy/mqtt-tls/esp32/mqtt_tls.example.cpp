// Fragmento orientativo: ESP32 + WiFiClientSecure + PubSubClient (TLS 8883).
// Incrustar PEM de ca.crt (y opcionalmente client.crt/client.key si activas mTLS en Mosquitto).
// No versionar claves reales.

#include <WiFiClientSecure.h>
#include <PubSubClient.h>

WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);

// Sustituir por PEM real (ca.crt)
static const char CA_CERT[] PROGMEM = R"PEM(
-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----
)PEM";

void setupMqttTls() {
  espClient.setCACert(CA_CERT);
  // mTLS opcional:
  // espClient.setCertificate(client_crt_pem);
  // espClient.setPrivateKey(client_key_pem);
  mqttClient.setServer("mqtt.tu-dominio.example", 8883);
}
