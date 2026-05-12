/*
 * CASTUO-SYSTEM™ — Extrusora para bio-compuestos
 * Arduino Mega: MAX6675 (boquilla), DS18B20 (cámara), NEMA 17 + A4988, Relé calentador, LCD I2C
 */
#include <MAX6675.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <AccelStepper.h>
#include <LiquidCrystal_I2C.h>

// Pines
#define THERMOCOUPLE_DO  4
#define THERMOCOUPLE_CS  5
#define THERMOCOUPLE_CLK 6
#define DS18B20_PIN      7
#define STEP_PIN         8
#define DIR_PIN          9
#define RELE_PIN         10

// Sensores
MAX6675 thermocouple(THERMOCOUPLE_CLK, THERMOCOUPLE_CS, THERMOCOUPLE_DO);
OneWire oneWire(DS18B20_PIN);
DallasTemperature ds18b20(&oneWire);
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Variables globales
float target_temp = 200.0;   // Objetivo PLA/cáñamo (°C)
float current_temp_boquilla = 0.0;
float current_temp_camara = 0.0;
bool heating = false;
bool extrusion_active = false;

void setup() {
  Serial.begin(9600);
  pinMode(RELE_PIN, OUTPUT);
  digitalWrite(RELE_PIN, LOW);

  ds18b20.begin();
  stepper.setMaxSpeed(1000);
  stepper.setAcceleration(500);

  lcd.init();
  lcd.backlight();
  lcd.print("Extrusora CASTUO");
  lcd.setCursor(0, 1);
  lcd.print("Iniciando...");
  delay(2000);
}

void loop() {
  current_temp_boquilla = thermocouple.readCelsius();
  ds18b20.requestTemperatures();
  current_temp_camara = ds18b20.getTempCByIndex(0);

  // Control temperatura (banda muerta ±5°C)
  if (current_temp_boquilla < target_temp - 5) {
    digitalWrite(RELE_PIN, HIGH);
    heating = true;
  } else if (current_temp_boquilla > target_temp + 5) {
    digitalWrite(RELE_PIN, LOW);
    heating = false;
  }

  // LCD
  lcd.clear();
  lcd.print("Boq:");
  lcd.print((int)current_temp_boquilla);
  lcd.print((char)223);
  lcd.print("C");
  lcd.setCursor(0, 1);
  lcd.print("Cam:");
  lcd.print((int)current_temp_camara);
  lcd.print((char)223);
  lcd.print("C ");
  lcd.print(heating ? "ON " : "OFF");

  // Motor (solo si temperatura OK y extrusión activa)
  if (extrusion_active && current_temp_boquilla > target_temp - 10) {
    stepper.moveTo(stepper.currentPosition() + 100);
  }
  stepper.run();

  // Salida serial para bridge MQTT (formato fácil de parsear)
  Serial.print("TEMP_B:");
  Serial.println(current_temp_boquilla);
  Serial.print("TEMP_C:");
  Serial.println(current_temp_camara);
  Serial.print("HEAT:");
  Serial.println(heating ? "1" : "0");

  // Comandos por Serial
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("SET_TEMP")) {
      target_temp = cmd.substring(8).toFloat();
    } else if (cmd == "START_EXTRUSION") {
      extrusion_active = true;
    } else if (cmd == "STOP_EXTRUSION") {
      extrusion_active = false;
    }
  }

  delay(500);
}
