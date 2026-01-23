#include "../Packet.h"

// The received data packet (usually with nonzero values)
uint8_t packet[16] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xEE, 0x00 };      

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

Packet::decode(packet, &temperature_int, &subsystem_status, &flight_mode, &low_power_mode, &status_events, &acceleration, &height_pressure, &height_gnss, &lat_gnss, &lon_gnss, &battery_voltage, &rssi);

// The data components can now be used.