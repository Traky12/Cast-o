/*
 * Extensión opcional: Auto-tuning PID (requiere PID_AutoTune de br3ttb).
 * Incluir en pid_control.ino si tienes la librería instalada.
 *
 * #include <PID_AutoTune_v0.h>
 * PID_ATune aTune(&Input, &Output);
 * byte ATuneModeRemember = 0;
 * double aTuneStep = 50, aTuneNoise = 1;
 * unsigned int aTuneLookBack = 20;
 *
 * En loop(), si ATuneModeRemember != 0:
 *   byte val = aTune.Runtime();
 *   if (val == 1) { Kp = aTune.GetKp(); Ki = aTune.GetKi(); Kd = aTune.GetKd();
 *                   myPID.SetTunings(Kp,Ki,Kd); ATuneModeRemember = 0; }
 * else: myPID.Compute();
 *
 * Comando serial: START_AUTOTUNE -> aTune.SetControlType(1); ATuneModeRemember = 2;
 */

void startAutoTune() {
  // aTune.SetControlType(1);
  // aTune.SetNoiseBand(aTuneNoise);
  // aTune.SetOutputStep(aTuneStep);
  // aTune.SetLookbackSec(aTuneLookBack);
  // ATuneModeRemember = 2;
}
