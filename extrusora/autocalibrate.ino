/*
 * Auto-calibración PID cada 24h (Relay Feedback / Ziegler-Nichols).
 * Incluir en pid_control.ino o compilar con PID_v1 + PID_AutoTune_v0.
 * Arduino Mega: EEPROM sin commit (AVR escribe directo).
 */
#if defined(ARDUINO_AVR_MEGA2560) || defined(ARDUINO_AVR_UNO)
#include <EEPROM.h>
#endif

// Direcciones EEPROM para Kp, Ki, Kd (double = 8 bytes)
#define EEPROM_KP  0
#define EEPROM_KI  8
#define EEPROM_KD  16
#define EEPROM_MAGIC 24
#define EEPROM_MAGIC_VAL 0xCA  // CASTUO

unsigned long lastAutoTune = 0;
const unsigned long autoTuneInterval = 24UL * 3600 * 1000;  // 24 h

void loadPIDParameters() {
#if defined(ARDUINO_AVR_MEGA2560) || defined(ARDUINO_AVR_UNO)
  if (EEPROM.read(EEPROM_MAGIC) != EEPROM_MAGIC_VAL) return;
  double kp, ki, kd;
  EEPROM.get(EEPROM_KP, kp);
  EEPROM.get(EEPROM_KI, ki);
  EEPROM.get(EEPROM_KD, kd);
  if (kp > 0.0 && kp < 10.0) {
    Kp = kp; Ki = ki; Kd = kd;
    myPID.SetTunings(Kp, Ki, Kd);
    Serial.print("PID cargado desde EEPROM: Kp="); Serial.print(Kp);
    Serial.print(" Ki="); Serial.print(Ki); Serial.print(" Kd="); Serial.println(Kd);
  }
#endif
}

void savePIDParameters(double kp, double ki, double kd) {
#if defined(ARDUINO_AVR_MEGA2560) || defined(ARDUINO_AVR_UNO)
  EEPROM.put(EEPROM_KP, kp);
  EEPROM.put(EEPROM_KI, ki);
  EEPROM.put(EEPROM_KD, kd);
  EEPROM.write(EEPROM_MAGIC, EEPROM_MAGIC_VAL);
  Serial.println("PID guardado en EEPROM.");
#endif
}

// Llamar desde setup(): loadPIDParameters();
// En loop(), cada 24h:
//   if (millis() - lastAutoTune >= autoTuneInterval) {
//     startAutoTune();  // Ver PID_AutoTune: aTune.Runtime() hasta val!=0
//     lastAutoTune = millis();
//   }
// Tras auto-tune: savePIDParameters(aTune.GetKp(), aTune.GetKi(), aTune.GetKd());
// Y publicar por Serial: AUTOTUNE:Kp=1.8,Ki=0.03,Kd=0.08 (para mqtt_autotune.py)
