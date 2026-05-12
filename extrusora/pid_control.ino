/*
 * CASTUO-SYSTEM™ — Control PID para extrusora (±1°C)
 * Requiere: PID_v1 (https://github.com/br3ttb/Arduino-PID-Library)
 * Pines: MAX6675 (4,5,6), DS18B20 (7), STEP(8), DIR(9), RELE(10), FAN(11)
 */
#include <MAX6675.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <AccelStepper.h>
#include <PID_v1.h>

#define THERMOCOUPLE_DO  4
#define THERMOCOUPLE_CS  5
#define THERMOCOUPLE_CLK 6
#define DS18B20_PIN      7
#define STEP_PIN         8
#define DIR_PIN          9
#define RELE_PIN         10
#define FAN_PIN          11

MAX6675 thermocouple(THERMOCOUPLE_CLK, THERMOCOUPLE_CS, THERMOCOUPLE_DO);
OneWire oneWire(DS18B20_PIN);
DallasTemperature ds18b20(&oneWire);
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

double Setpoint, Input, Output;
double Kp = 2.0, Ki = 0.05, Kd = 0.1;
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);

float current_temp_boquilla = 0.0;
float current_temp_camara = 0.0;
unsigned long lastPIDCompute = 0;
const int PIDInterval = 100;
bool extrusion_active = false;

void setup() {
  Serial.begin(9600);
  pinMode(RELE_PIN, OUTPUT);
  pinMode(FAN_PIN, OUTPUT);
  digitalWrite(RELE_PIN, LOW);
  digitalWrite(FAN_PIN, LOW);

  ds18b20.begin();
  stepper.setMaxSpeed(1000);
  stepper.setAcceleration(500);

  Setpoint = 200.0;
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(0, 255);
  myPID.SetSampleTime(PIDInterval);
  delay(2000);
}

void loop() {
  current_temp_boquilla = thermocouple.readCelsius();
  ds18b20.requestTemperatures();
  current_temp_camara = ds18b20.getTempCByIndex(0);
  Input = (double)current_temp_boquilla;

  if (millis() - lastPIDCompute >= (unsigned long)PIDInterval) {
    myPID.Compute();
    analogWrite(RELE_PIN, (int)Output);

    if (current_temp_boquilla > 210.0)
      digitalWrite(FAN_PIN, HIGH);
    else if (current_temp_boquilla < 190.0)
      digitalWrite(FAN_PIN, LOW);

    lastPIDCompute = millis();
  }

  if (extrusion_active && current_temp_boquilla > Setpoint - 10.0)
    stepper.moveTo(stepper.currentPosition() + 100);
  stepper.run();

  Serial.print("Boquilla:");
  Serial.print(current_temp_boquilla);
  Serial.print(", Camara:");
  Serial.print(current_temp_camara);
  Serial.print(", PID Output:");
  Serial.print(Output);
  Serial.print(", Setpoint:");
  Serial.println(Setpoint);

  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("SET_TEMP")) {
      Setpoint = cmd.substring(8).toFloat();
      if (Setpoint > 210.0)      { Kp = 1.8; Ki = 0.03; Kd = 0.08; }
      else if (Setpoint < 190.0) { Kp = 2.0; Ki = 0.05; Kd = 0.1;  }
      else                       { Kp = 2.2; Ki = 0.04; Kd = 0.12; }
      myPID.SetTunings(Kp, Ki, Kd);
    } else if (cmd.startsWith("SET_PID")) {
      int i = cmd.indexOf(' ', 7);
      int j = cmd.indexOf(' ', i + 1);
      if (i > 0 && j > 0) {
        Kp = cmd.substring(7, i).toFloat();
        Ki = cmd.substring(i + 1, j).toFloat();
        Kd = cmd.substring(j + 1).toFloat();
        myPID.SetTunings(Kp, Ki, Kd);
      }
    } else if (cmd == "START_EXTRUSION") {
      extrusion_active = true;
    } else if (cmd == "STOP_EXTRUSION") {
      extrusion_active = false;
    }
  }
  delay(10);
}
