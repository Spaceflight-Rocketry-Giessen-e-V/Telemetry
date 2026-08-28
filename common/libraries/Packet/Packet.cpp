#include "packet.h"

Packet::Packet()
{
	bitSize = 0;
}

uint8_t Packet::getBitSize() const
{
	return bitSize;
}

uint8_t Packet::getByteSize() const
{
	return (bitSize - 1) / 8 + 1;
}

void Packet::addComponent(Component* newComponent)
{
	uint8_t i;
	for (i = 0; (i < components.size()) && (components[i]->priority <= newComponent->priority); i++);

	components.insert(components.begin() + i, newComponent);
	components[i]->bitPosition = bitSize;
	bitSize = bitSize + components[i]->size;
}

uint8_t* Packet::encode()
{
	uint8_t* packet = (uint8_t*)calloc(getByteSize(), 8);
	for (uint8_t i = 0; i < components.size(); i++)
	{
		components[i]->encode(packet);
	}
	return packet;
}

void Packet::decode(uint8_t* packet)
{
	for (uint8_t i = components.size(); i > 0; i--)
	{
		if (components[i - 1]->decode(packet) != 0)
		{
			break; // Error (parity, cobs, ...)
		}
		components[i - 1]->bitReset(packet);
	}
}