#pragma once
#include "component.h"

class const_Component : public Component
{
public:
	const_Component(uint32_t value, uint8_t size, const uint8_t priority = 0);
	void encode(uint8_t* packet) override;
	uint8_t decode(uint8_t* packet) override;
protected:
	uint32_t value;
};

class empty_Component : public const_Component
{
public:
	empty_Component(uint8_t size);
};

class parity_Component : public Component
{
public:
	parity_Component(Packet *packet, const uint8_t priority = 1);
	void encode(uint8_t* packet) override;
	uint8_t decode(uint8_t* packet) override;
protected:
	Packet *packet;
};

class cobs_Component : public Component
{
public:
	cobs_Component(uint8_t markerByte, uint8_t size, Packet* packet, const uint8_t priority = 127);
	void encode(uint8_t* packet) override;
	uint8_t decode(uint8_t* packet) override;
protected:
	uint8_t markerByte;
	uint8_t size;
	Packet* packet;
};