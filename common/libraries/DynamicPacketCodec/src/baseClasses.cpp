#include "baseClasses.h"

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

// BASE COMPONENT //

Component::Component(uint8_t size, const uint8_t priority)
{
	this->size = size;
	this->priority = priority;
}

void Component::bitWriter(uint32_t dataBits, uint8_t* packet) const
{
	dataBits = dataBits & (0xFFFFFFFF >> (32 - size));
	uint8_t tempRemainingSize = size;
	uint8_t tempBytePosition = bitPosition / 8;
	uint8_t tempBitPosition = bitPosition % 8;
	while (true)
	{
		uint8_t bitsInByte = 8 - tempBitPosition;
		if (bitsInByte >= tempRemainingSize)
		{
			packet[tempBytePosition] &= ((0xFF << bitsInByte) | (0xFF >> tempRemainingSize));
			packet[tempBytePosition] |= (dataBits & (0x000000FF >> (8 - tempRemainingSize))) << (bitsInByte - tempRemainingSize);
			break;
		}
		else
		{
			packet[tempBytePosition] &= (0xFF << bitsInByte);
			packet[tempBytePosition] |= (dataBits & ((0x000000FF >> tempBitPosition) << (tempRemainingSize - bitsInByte))) >> (tempRemainingSize - bitsInByte);
			tempRemainingSize = tempRemainingSize - bitsInByte;
			tempBytePosition = tempBytePosition + 1;
			tempBitPosition = 0;
		}
	}
}

void Component::bitReader(uint32_t* dataBits, uint8_t* packet) const
{
	uint8_t tempRemainingSize = size;
	uint8_t tempBytePosition = bitPosition / 8;
	uint8_t tempBitPosition = bitPosition % 8;
	while (true)
	{
		uint8_t bitsInByte = 8 - tempBitPosition;
		if (bitsInByte >= tempRemainingSize)
		{
			*dataBits |= ((packet[tempBytePosition] & ((0x000000FF >> (8 - tempRemainingSize)) << (bitsInByte - tempRemainingSize))) >> (bitsInByte - tempRemainingSize));
			break;
		}
		else
		{
			*dataBits |= (packet[tempBytePosition] & (0x000000FF >> tempBitPosition)) << (tempRemainingSize - bitsInByte);
			tempRemainingSize = tempRemainingSize - bitsInByte;
			tempBytePosition = tempBytePosition + 1;
			tempBitPosition = 0;
		}
	}
}

void Component::bitReset(uint8_t* packet) const
{
	bitWriter(0, packet);
}