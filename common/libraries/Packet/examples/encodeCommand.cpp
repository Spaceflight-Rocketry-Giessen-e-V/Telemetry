#include "../Packet.h"

uint8_t command = 'q';
uint8_t packet;

Packet::encodeCommand(command, &packet);
// The 'packet' byte can now be transmitted or used otherwise.