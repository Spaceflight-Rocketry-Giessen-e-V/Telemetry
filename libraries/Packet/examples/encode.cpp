#include "../Packet.h"

uint8_t packet[16] = { 0 };
float temperature = 43;                 // Deg. C
uint8_t subsystem_status = 0b011;
uint8_t flight_mode = 0b1;
uint8_t low_power_mode = 0b1;
uint8_t status_events = 0b0011;
float acceleration = 21.32;             // g
float height_pressure = 2000.2;         // m
float height_gnss = 2363.5;             // m
float lat_gnss = 50.587128;             // Deg.
float lon_gnss = 8.683172;              // Deg.
float battery_voltage = 7.6;            // V
float rssi = -105.123;                  // dB

Packet::encode(packet, temperature, subsystem_status, flight_mode, low_power_mode, status_events, acceleration, height_pressure, height_gnss, lat_gnss, lon_gnss, battery_voltage);

// The 'packet' array can now be transmitted or used otherwise.