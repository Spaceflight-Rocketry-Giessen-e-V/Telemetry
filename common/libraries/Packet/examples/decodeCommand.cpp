#include "../Packet.h"

uint8_t packet = 'q';
uint8_t command;

Packet::decodeCommand(packet, &command);