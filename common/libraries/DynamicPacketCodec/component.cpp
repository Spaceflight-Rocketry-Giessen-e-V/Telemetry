#include "component.h"

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