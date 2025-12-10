#include <Arduino.h>

// Telemetry variables
uint8_t temperature;
uint8_t subsystem_status;
uint8_t flight_mode;
uint8_t low_power_mode;
uint8_t status_events;
float acceleration;
float height_pressure;
float height_gnss;
float lat_gnss;
float lon_gnss;
float battery_voltage;
float rssi;
int time_since_last_packet;


void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(A0)); // Seed random generator
}

void loop() {
  // Generate random telemetry data
  temperature = random(20, 90); // 20°C to 90°C
  subsystem_status = random(0, 8); // 3-bit status
  flight_mode = random(0, 2); // 0 or 1
  low_power_mode = random(0, 2); // 0 or 1
  status_events = random(0, 15);
  acceleration = random(0, 2000) / 100.0; // 0 to 20 m/s²
  height_pressure = random(0, 300) / 10.0; // 0 to 300 m
  height_gnss = random(0, 300) / 10.0;
  lat_gnss = random(-90000000, 90000000) / 1000000.0; // -90 to 90°
  lon_gnss = random(-180000000, 180000000) / 1000000.0; // -180 to 180°
  battery_voltage = random(500, 1200) / 100.0; // 5V to 12V
  rssi = random(-100, -30); // dBm
  time_since_last_packet = random(125, 127); // ms



  Serial.print("temperature > 80 C: ");     Serial.println(temperature);
  Serial.print("subsystem_status: ");      Serial.println(subsystem_status);
  Serial.print("flight_mode: ");           Serial.println(flight_mode);
  Serial.print("low_power_mode: ");        Serial.println(low_power_mode);
  Serial.print("status_events: ");         Serial.println(status_events);
  Serial.print("acceleration: ");          Serial.println(acceleration, 4);
  Serial.print("height_pressure: ");       Serial.println(height_pressure);
  Serial.print("height_gnss: ");           Serial.println(height_gnss);
  Serial.print("lat_gnss: ");              Serial.println(lat_gnss, 7);
  Serial.print("lon_gnss: ");              Serial.println(lon_gnss, 7);
  Serial.print("battery_voltage: ");       Serial.println(battery_voltage);
  Serial.print("rssi: ");                  Serial.println(rssi);
  Serial.print("time_since_last_packet: ");Serial.println(time_since_last_packet);

  delay(125);
}
