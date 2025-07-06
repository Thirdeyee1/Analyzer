#include <Wire.h>
#include <Arduino.h>

#define LSM6DS3_ADDR 0x6A
#define CTRL1_XL 0x10
#define OUTX_L_A 0x28

const int numSamples = 500;
float magBuffer[numSamples];
int sampleIndex = 0;

unsigned long lastPrintTime = 0;
int sampleCount = 0;

void setup() {
  Serial.begin(1000000);  // ✅ FAST BAUD
  Wire.begin();

  // Set accelerometer: 833Hz, ±2g
  Wire.beginTransmission(LSM6DS3_ADDR);
  Wire.write(CTRL1_XL);
  Wire.write(0xA0);  // ODR = 833Hz, FS = ±2g
  Wire.endTransmission();
}

void loop() {
  int16_t ax_raw, ay_raw, az_raw;

  // Read accel registers (6 bytes)
  Wire.beginTransmission(LSM6DS3_ADDR);
  Wire.write(OUTX_L_A);
  Wire.endTransmission(false);
  Wire.requestFrom(LSM6DS3_ADDR, 6);
  if (Wire.available() == 6) {
    ax_raw = Wire.read() | (Wire.read() << 8);
    ay_raw = Wire.read() | (Wire.read() << 8);
    az_raw = Wire.read() | (Wire.read() << 8);

    float ax = ax_raw * 0.061 / 1000.0;
    float ay = ay_raw * 0.061 / 1000.0;
    float az = az_raw * 0.061 / 1000.0;

    float mag = sqrt(ax * ax + ay * ay + az * az);
    magBuffer[sampleIndex] = mag;
    sampleIndex++;

    // ✅ Output compact CSV line
    Serial.print(ax, 3); Serial.print(',');
    Serial.print(ay, 3); Serial.print(',');
    Serial.print(az, 3); Serial.print(',');
    Serial.println(mag, 3);

    sampleCount++;

    // Compute RMS + P2P every 500 samples
    if (sampleIndex == numSamples) {
      float sumSq = 0, maxVal = magBuffer[0], minVal = magBuffer[0];
      for (int i = 0; i < numSamples; i++) {
        float v = magBuffer[i];
        sumSq += v * v;
        if (v > maxVal) maxVal = v;
        if (v < minVal) minVal = v;
      }
      float rms = sqrt(sumSq / numSamples);
      float p2p = maxVal - minVal;

      Serial.print("RMS,");
      Serial.print(rms, 3); Serial.print(",");
      Serial.println(p2p, 3);

      sampleIndex = 0;
    }

    // Optional debug FPS
    if (millis() - lastPrintTime >= 1000) {
      Serial.print("FPS: ");
      Serial.println(sampleCount);
      sampleCount = 0;
      lastPrintTime = millis();
    }
  }
}
