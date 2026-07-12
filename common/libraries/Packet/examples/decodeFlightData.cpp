#include "../Packet.h"

// The received data packet (usually with nonzero values)
uint8_t packet[13] = { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xEE, 0x00 };

float acceleration;
float heightPressure;
uint8_t flightEvents;
float latitude;
float longitude;
float rssi;

uint8_t packet_identifier;
Packet::decodeFrame(packet, &packet_identifier)

if(packet_identifier == 0)
{
    Packet::decodeFlightData(packet, &acceleration, &heightPressure, &flightEvents, &latitude, &longitude, &rssi);
}