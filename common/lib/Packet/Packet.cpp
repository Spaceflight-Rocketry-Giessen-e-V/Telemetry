/*
    Packet - Library for encoding and decoding telemetry packets for the ASCENT II telemetry system.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Packet.h"

void Packet::encode(uint8_t* packet, uint8_t address, uint8_t flight_mode, uint8_t low_power_mode, uint8_t subsystem_status, uint8_t status_events, float acceleration, float height_pressure, float height_gnss, float lat_gnss, float lon_gnss, float battery_voltage)
{

}

void Packet::decode(uint8_t packet, uint8_t* address, uint8_t* flight_mode, uint8_t* low_power_mode, uint8_t* subsystem_status, uint8_t* status_events, float* acceleration, float* height_pressure, float* height_gnss, float* lat_gnss, float* lon_gnss, float* battery_voltage, float* rssi)
{

}
