#include <Arduino.h>
#include <math.h>

// ===================== Telemetry =====================
uint8_t temperature;
uint8_t subsystem_status = 0;
uint8_t flight_mode = 0;
uint8_t low_power_mode = 0;
uint8_t status_events;

float acceleration;           // g
float height_pressure;
float height_gnss;
float lat_gnss;
float lon_gnss;
float battery_voltage;
float rssi;
int time_since_last_packet;

// ===================== Constants =====================
const float g = 9.81;
const int hz = 8;
const float battery_start = 8.4;
const float battery_min = 5.4;
const float APOGEE_LIMIT = 9000.0;

// GPS (Giessen)
const float lat_start = 49.8108889;
const float lon_start = 8.8547290;
const float lat_end   = 49.8131689;
const float lon_end   = 8.8499197;

float parachute_heights[4] = {50, 100, 150, 200};

// ===================== Flight =====================
enum FlightPhase { BOOST, COAST, DESCENT };
FlightPhase phase;

float velocity = 0.0;   // m/s
float height = 0.0;
float main_altitude = 50;

unsigned long boost_start = 0;
unsigned long last_send_time = 0;
unsigned long send_interval = 15000;

// ===================== Helpers =====================
char normalize_cmd(char c) {
  return (c >= 'A' && c <= 'Z') ? c + 32 : c;
}

void send_telemetry() {
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
}

void reset_flight() {
  velocity = 0;
  height = 0;
  phase = BOOST;
  boost_start = millis();
  battery_voltage = battery_start;
  temperature = 0;
  status_events = 4; // Armed
}

// ===================== Arduino =====================
void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(A0));
}

void loop() {
  unsigned long now = millis();

  // ===================== Commands =====================
  while (Serial.available()) {
    char cmd = normalize_cmd(Serial.read());
    switch (cmd) {
      case 'l': low_power_mode = 1; break;
      case 'm': low_power_mode = 0; break;

      case 'f':
        flight_mode = 1;
        send_interval = 1000 / hz;
        reset_flight();
        break;

      case 'g':
        flight_mode = 0;
        send_interval = 15000;
        break;

      case 'a': case 'b': case 'c': case 'd':
        main_altitude = parachute_heights[cmd - 'a'];
        status_events = cmd - 'a';
        break;

      case 'q':
        status_events = 9; // drogue command
        phase = DESCENT;
        break;

      case 'r':
        status_events = 12; // main command
        velocity *= 0.25;
        break;

      case 'p':
        send_telemetry();
        break;
    }
  }

  // ===================== Flight Simulation =====================
  if (flight_mode) {
    float dt = 0.05;

    // ---------- BOOST (≈4s) ----------
    if (phase == BOOST) {
      status_events = 5;
      acceleration = 5.2;
      velocity += acceleration * g * dt;
      height += velocity * dt;

      if (millis() - boost_start > 4000) {
        phase = COAST;
        status_events = 6;
      }
    }

    // ---------- COAST ----------
    else if (phase == COAST) {
      float drag = 0.002 * velocity * velocity;
      acceleration = -drag / g;
      velocity += acceleration * g * dt;
      height += velocity * dt;

      if (velocity <= 0 || height >= APOGEE_LIMIT) {
        height = min(height, APOGEE_LIMIT);
        velocity = 0;
        phase = DESCENT;
        status_events = 7;
      }
    }

    // ---------- DESCENT ----------
    else if (phase == DESCENT) {
      float terminal = (height > main_altitude) ? -55.0 : -8.0;
      float dv = terminal - velocity;
      velocity += dv * 0.5;
      height += velocity * dt;

      acceleration = dv / g;

      if (height <= main_altitude && status_events != 10) {
        status_events = 10;
      }

      if (height <= 0) {
        height = 0;
        velocity = 0;
        status_events = 13;
        reset_flight();
      }
    }

    // ---------- Telemetry ----------
    height_pressure = height_gnss = height;

    acceleration += random(-2, 3) / 100.0;
    battery_voltage -= 0.0001;
    if (battery_voltage < battery_min) battery_voltage = battery_min;

    temperature = (height > 7000) ? 1 : 0;

    float t = height / APOGEE_LIMIT;
    lat_gnss = lat_start + t * (lat_end - lat_start);
    lon_gnss = lon_start + t * (lon_end - lon_start);

    rssi = -40 - height * 0.02;
    time_since_last_packet = 1000 / hz;
  }

  // ===================== Standby =====================
  else {
    acceleration = 0;
    height_pressure = height_gnss = 0;
    battery_voltage = battery_start;
    temperature = 0;
    rssi = -45;
    time_since_last_packet = 15000;
  }

  // ===================== Send Telemetry =====================
  if (now - last_send_time >= send_interval) {
    send_telemetry();
    last_send_time = now;
  }

  delay(10);
}
