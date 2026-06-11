/*
    Packet - Library for encoding and decoding telemetry packets for the ASCENT III telemetry system.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#ifndef Packet_h
#define Packet_h

#include "Arduino.h"

class Packet
{
    public:

        static void Encode(uint8_t* packet, float temperature, uint8_t subsystem_status, uint8_t flight_mode, uint8_t low_power_mode, uint8_t status_events, float acceleration, float height_pressure, float height_gnss, float lat_gnss, float lon_gnss, float battery_voltage);

        static void Decode(uint8_t* packet, uint8_t* temperature, uint8_t* subsystem_status, uint8_t* flight_mode, uint8_t* low_power_mode, uint8_t* status_events, float* acceleration, float* height_pressure, float* height_gnss, float* lat_gnss, float* lon_gnss, float* battery_voltage, float* rssi);

        static void encodeFrame(uint8_t *packet, uint8_t packetIdentifier);
        static uint8_t decodeFrame(uint8_t *packet, uint8_t *packetIdentifier);

        static void encodeCommand(u_int8_t input, uint8_t *output);
        static void decodeCommand(u_int8_t input, uint8_t *output);
}; 

#endif
