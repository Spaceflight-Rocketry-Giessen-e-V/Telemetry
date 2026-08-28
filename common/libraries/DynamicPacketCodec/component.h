#pragma once

class Packet;

class Component
{
public:
	Component(uint8_t size, const uint8_t priority = 0);
	virtual void encode(uint8_t* packet) = 0;
	virtual uint8_t decode(uint8_t* packet) = 0;
	void bitReset(uint8_t* packet) const;
	uint8_t size;
	uint8_t bitPosition;
	uint8_t priority;
protected:
	void bitWriter(uint32_t dataBits, uint8_t* packet) const;
	void bitReader(uint32_t* dataBits, uint8_t* packet) const;
};