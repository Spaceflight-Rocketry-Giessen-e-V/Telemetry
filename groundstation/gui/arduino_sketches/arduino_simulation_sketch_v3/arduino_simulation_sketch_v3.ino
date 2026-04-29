#include <Arduino.h>
#include <math.h>

// =====================================================================
//  CONFIG — Tune these for your rocket model
// =====================================================================

const float TARGET_APOGEE    = 1500.0;  // [m]   desired apogee AGL  (800 – 3000)
const float ROCKET_MASS_DRY  = 2.5;    // [kg]  dry mass
const float PROPELLANT_MASS  = 0.6;    // [kg]  propellant mass
const float MOTOR_BURN_TIME  = 3.2;    // [s]   burn duration
const float ROCKET_DIAMETER  = 0.075;  // [m]   airframe diameter
const float DRAG_COEFF       = 0.45;   // [-]   subsonic Cd

const float DROGUE_TERMINAL  = 25.0;   // [m/s] descent speed under drogue
const float MAIN_TERMINAL    = 5.5;    // [m/s] descent speed under main chute

const float BATTERY_FULL     = 8.40;   // [V]
const float BATTERY_MIN      = 5.40;   // [V]

// Launch site (Giessen area)
const float LAT_LAUNCH       = 49.8108889;
const float LON_LAUNCH       = 8.8547290;
const float LAT_LAND         = 49.8131689;
const float LON_LAND         = 8.8499197;

float parachute_heights[4]   = {100, 150, 200, 250};  // [m] main-chute altitude presets

const int HZ_FLIGHT          = 8;

// =====================================================================
//  Telemetry variables
// =====================================================================
uint8_t temperature;
uint8_t subsystem_status = 0;
uint8_t flight_mode      = 0;
uint8_t low_power_mode   = 0;
uint8_t status_events;

float acceleration;
float height_pressure;
float height_gnss;
float lat_gnss;
float lon_gnss;
float battery_voltage;
float rssi;
int   time_since_last_packet;

// =====================================================================
//  Internal state
// =====================================================================
enum FlightPhase { PAD, BOOST, COAST, DROGUE_DESCENT, MAIN_DESCENT, LANDED };
FlightPhase phase = PAD;

float velocity        = 0.0;
float height          = 0.0;
float apogee_reached  = 0.0;
float mass            = 0.0;
float main_altitude   = 200.0;

float MOTOR_THRUST    = 0.0;
float REF_AREA        = 0.0;

unsigned long boost_start    = 0;
unsigned long last_send_time = 0;
unsigned long last_sim_time  = 0;
unsigned long landed_time    = 0;
unsigned long send_interval  = 15000UL;

// =====================================================================
//  ISA atmosphere
// =====================================================================
float air_density(float alt) {
  const float T0 = 288.15, L = 0.0065, P0 = 101325.0, R = 287.05, g0 = 9.80665;
  float T = T0 - L * alt;
  if (T < 216.65) T = 216.65;
  float P = P0 * pow(T / T0, g0 / (L * R));
  return P / (R * T);
}

float ambient_temp_c(float alt) {
  float T = 288.15 - 0.0065 * alt;
  if (T < 216.65) T = 216.65;
  return T - 273.15;
}

// =====================================================================
//  Noise helper (zero-mean, approximate Gaussian via sum of uniforms)
// =====================================================================
float noise(float sigma) {
  float u = (float)random(-1000, 1001) / 1000.0;
  float v = (float)random(-1000, 1001) / 1000.0;
  return sigma * (u + v) * 0.5;
}

// =====================================================================
//  Compute motor thrust to reach TARGET_APOGEE
// =====================================================================
void compute_motor_thrust() {
  REF_AREA = M_PI * pow(ROCKET_DIAMETER / 2.0, 2);
  float v_bo   = sqrt(2.0 * 9.80665 * TARGET_APOGEE) * 1.35;
  float m_avg  = ROCKET_MASS_DRY + PROPELLANT_MASS * 0.5;
  MOTOR_THRUST = m_avg * (v_bo / MOTOR_BURN_TIME + 9.80665);
  MOTOR_THRUST += 0.5 * air_density(200.0) * DRAG_COEFF * REF_AREA * pow(v_bo * 0.5, 2);
}

// =====================================================================
//  Telemetry output — exact protocol, nothing else ever written to Serial
// =====================================================================
void send_telemetry() {
  Serial.print("temperature > 80 C: ");      Serial.println(temperature);
  Serial.print("subsystem_status: ");        Serial.println(subsystem_status);
  Serial.print("flight_mode: ");             Serial.println(flight_mode);
  Serial.print("low_power_mode: ");          Serial.println(low_power_mode);
  Serial.print("status_events: ");           Serial.println(status_events);
  Serial.print("acceleration: ");            Serial.println(acceleration, 4);
  Serial.print("height_pressure: ");         Serial.println(height_pressure);
  Serial.print("height_gnss: ");             Serial.println(height_gnss);
  Serial.print("lat_gnss: ");                Serial.println(lat_gnss, 7);
  Serial.print("lon_gnss: ");                Serial.println(lon_gnss, 7);
  Serial.print("battery_voltage: ");         Serial.println(battery_voltage);
  Serial.print("rssi: ");                    Serial.println(rssi);
  Serial.print("time_since_last_packet: ");  Serial.println(time_since_last_packet);
}

// =====================================================================
//  Reset to armed/pad state
// =====================================================================
void reset_flight() {
  velocity        = 0.0;
  height          = 0.0;
  apogee_reached  = 0.0;
  mass            = ROCKET_MASS_DRY + PROPELLANT_MASS;
  phase           = PAD;
  battery_voltage = BATTERY_FULL;
  temperature     = 0;
  status_events   = 4;  // Armed
  lat_gnss        = LAT_LAUNCH;
  lon_gnss        = LON_LAUNCH;
}

// =====================================================================
//  Physics step
// =====================================================================
void physics_step(float dt) {
  const float g0 = 9.80665;
  float rho  = air_density(height);
  float vsq  = velocity * velocity;
  float drag = 0.5 * rho * DRAG_COEFF * REF_AREA * vsq;
  if (velocity > 0) drag = -drag;

  float burn_elapsed = (millis() - boost_start) / 1000.0;

  switch (phase) {

    case PAD:
      break;

    case BOOST: {
      status_events = 5;
      if (burn_elapsed < MOTOR_BURN_TIME) {
        mass -= (PROPELLANT_MASS / MOTOR_BURN_TIME) * dt;
        if (mass < ROCKET_MASS_DRY) mass = ROCKET_MASS_DRY;
        float net_a  = (MOTOR_THRUST + drag) / mass - g0;
        acceleration = net_a / g0;
        velocity    += net_a * dt;
        height      += velocity * dt;
        if (height < 0) height = 0;
      } else {
        mass          = ROCKET_MASS_DRY;
        phase         = COAST;
        status_events = 6;  // Burnout
      }
      break;
    }

    case COAST: {
      float net_a  = (drag / mass) - g0;
      acceleration = net_a / g0;
      velocity    += net_a * dt;
      height      += velocity * dt;
      if (velocity <= 0.0) {
        apogee_reached = height;
        velocity       = 0.0;
        phase          = DROGUE_DESCENT;
        status_events  = 7;  // Apogee / drogue
      }
      break;
    }

    case DROGUE_DESCENT: {
      float dv   = (-DROGUE_TERMINAL) - velocity;
      velocity  += dv * 3.0 * dt;
      height    += velocity * dt;
      acceleration = (fabs(velocity) * fabs(velocity) * 0.5 * rho * DRAG_COEFF * REF_AREA)
                     / (mass * g0) - 1.0;
      if (acceleration < -1.0) acceleration = -1.0;
      if (height <= main_altitude) {
        phase         = MAIN_DESCENT;
        status_events = 10;  // Main deploy
      }
      break;
    }

    case MAIN_DESCENT: {
      velocity     += ((-MAIN_TERMINAL) - velocity) * 5.0 * dt;
      height       += velocity * dt;
      acceleration  = 0.0;
      if (height <= 0.0) {
        height        = 0.0;
        velocity      = 0.0;
        phase         = LANDED;
        status_events = 13;  // Landed
        landed_time   = millis();
      }
      break;
    }

    case LANDED:
      acceleration = 0.0;
      if (millis() - landed_time > 10000UL) {
        reset_flight();
      }
      break;
  }

  // Sensor noise
  height_pressure = max(0.0f, height + noise(phase == BOOST ? 3.0 : 0.8));
  height_gnss     = max(0.0f, height + noise(1.5));
  acceleration   += noise(phase == BOOST ? 0.08 : 0.02);

  // Onboard temperature flag
  float elec_temp = 30.0 + (phase == BOOST ? 55.0 : phase == COAST ? 10.0 : 2.0);
  temperature = (elec_temp > 80.0 || ambient_temp_c(height) < -20.0) ? 1 : 0;

  // GPS interpolation along flight track
  float frac = (apogee_reached > 0.0)
               ? min(height / apogee_reached, 1.0f)
               : height / max(TARGET_APOGEE, 1.0f);
  lat_gnss = LAT_LAUNCH + frac * (LAT_LAND - LAT_LAUNCH) + noise(0.000005);
  lon_gnss = LON_LAUNCH + frac * (LON_LAND - LON_LAUNCH) + noise(0.000005);

  // Battery
  battery_voltage -= 0.00008;
  if (battery_voltage < BATTERY_MIN) battery_voltage = BATTERY_MIN;

  // RSSI via free-space path loss
  float slant = sqrt(height * height + pow(frac * 300.0, 2));
  if (slant < 1.0) slant = 1.0;
  rssi = -40.0 - 20.0 * log10(slant) + noise(1.5);

  time_since_last_packet = 1000 / HZ_FLIGHT;
}

// =====================================================================
//  Helpers
// =====================================================================
char normalize_cmd(char c) {
  return (c >= 'A' && c <= 'Z') ? c + 32 : c;
}

// =====================================================================
//  Arduino entry points
// =====================================================================
void setup() {
  Serial.begin(115200);
  randomSeed(analogRead(A0));
  compute_motor_thrust();
  reset_flight();
}

void loop() {
  unsigned long now = millis();

  // Command parser
  while (Serial.available()) {
    char cmd = normalize_cmd(Serial.read());
    switch (cmd) {

      case 'l':
        low_power_mode = 1;
        send_interval  = 30000UL;
        break;

      case 'm':
        low_power_mode = 0;
        send_interval  = flight_mode ? (1000UL / HZ_FLIGHT) : 15000UL;
        break;

      case 'f':
        flight_mode    = 1;
        send_interval  = 1000UL / HZ_FLIGHT;
        reset_flight();
        phase          = BOOST;
        boost_start    = millis();
        last_sim_time  = millis();
        status_events  = 5;
        break;

      case 'g':
        flight_mode   = 0;
        send_interval = 15000UL;
        phase         = PAD;
        break;

      case 'a': case 'b': case 'c': case 'd': {
        int idx       = cmd - 'a';
        main_altitude = parachute_heights[idx];
        status_events = idx;
        break;
      }

      case 'q':
        if (flight_mode && phase == COAST) {
          phase         = DROGUE_DESCENT;
          status_events = 9;
        }
        break;

      case 'r':
        if (flight_mode && phase == DROGUE_DESCENT) {
          phase         = MAIN_DESCENT;
          status_events = 12;
          velocity     *= 0.15;
        }
        break;

      case 'p':
        send_telemetry();
        break;
    }
  }

  // Physics update
  if (flight_mode && phase != PAD) {
    unsigned long sim_now = millis();
    float dt = (sim_now - last_sim_time) / 1000.0;
    last_sim_time = sim_now;
    if (dt > 0.05) dt = 0.05;
    if (dt < 0.001) dt = 0.001;
    physics_step(dt);
  }

  // Standby values
  if (!flight_mode) {
    acceleration           = noise(0.01);
    height_pressure        = max(0.0f, noise(0.3));
    height_gnss            = max(0.0f, noise(0.8));
    lat_gnss               = LAT_LAUNCH + noise(0.000003);
    lon_gnss               = LON_LAUNCH + noise(0.000003);
    battery_voltage        = BATTERY_FULL;
    temperature            = 0;
    rssi                   = -45.0 + noise(1.0);
    time_since_last_packet = 15000;
  }

  // Scheduled telemetry
  if (now - last_send_time >= send_interval) {
    send_telemetry();
    last_send_time = now;
  }

  delay(10);
}
