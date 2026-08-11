#include "../Packet.h"

uint8_t packet[12] = { 0 };

float acceleration = 13.22;
float heightPressure = 2000.2;
uint8_t flightEvents = 13;
float latitude = 50.587128;
float longitude = 8.683172;

Packet::encodeFlightData(packet, acceleration, heightPressure, flightEvents, latitude, longitude);
Packet::encodeFrame(packet, 0);
// The 'packet' array can now be transmitted or used otherwise.