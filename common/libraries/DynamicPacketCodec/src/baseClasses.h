#pragma once
#include "Arduino.h"
#include <vector>

class Packet;
class Component;

class Packet
{
public:
	Packet();
	std::vector<Component*> components;
	uint8_t getBitSize() const;
	uint8_t getByteSize() const;
	void addComponent(Component* newComponent);
	uint8_t* encode();
	void decode(uint8_t* packet);
protected:
	uint8_t bitSize;
};

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
	Packet* packet;
protected:
	void bitWriter(uint32_t dataBits, uint8_t* packet) const;
	void bitReader(uint32_t* dataBits, uint8_t* packet) const;
};
