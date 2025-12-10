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

// Flight simulation parameters
const float flight_duration = 20.0; // seconds
const float update_interval = 0.125; // seconds per loop, deprecated
const int steps = flight_duration / update_interval;

int step_counter = 0;

// GPS start/end
const float lat_start = 49.81088894936561;
const float lon_start = 8.854729095663512;
const float lat_end = 49.81316897842152;
const float lon_end = 8.849919720355352;

// Heights and battery
const float height_max = 300.0; // meters
const float battery_start = 10.0; // volts
const float battery_end = 6.0;    // volts

void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(A0));
}

void loop() {
  float t = (float)step_counter / steps; // normalized time 0..1

  // Telemetry values
  temperature = random(20, 90);
  subsystem_status = random(0, 8);
  flight_mode = random(0, 2);
  low_power_mode = random(0, 2);

  // Flight events increase from 0 → 15
  status_events = (uint8_t)(t * 15.0);

  acceleration = random(-1000L, 2000L) / 100.0; //-20 to 20 g
  Serial.println(acceleration);

  // Linear interpolation for height, GPS, battery
  height_pressure = height_gnss = t * height_max;

  // Battery cycles: rise to start for next loop
  battery_voltage = battery_start + t * (battery_end - battery_start);

  lat_gnss = lat_start + t * (lat_end - lat_start);
  lon_gnss = lon_start + t * (lon_end - lon_start);

  rssi = random(-100, -30);
  time_since_last_packet = 125 + random(0, 3);

  // Print telemetry
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

  // Update step
  step_counter++;
  if(step_counter > steps) step_counter = 0; // loop flight

  delay(time_since_last_packet);
}
