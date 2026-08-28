#pragma once
#include "component.h"

class uint8_t_Component : public Component
{
public:
	uint8_t_Component(uint8_t* value, uint8_t size, const uint8_t min, const uint8_t max, const uint8_t priority = 0);
	void encode(uint8_t* packet) override;
	uint8_t decode(uint8_t* packet) override;
protected:
	uint8_t* value;
	uint8_t min;
	uint8_t max;
	uint8_t resolution;
};

class float_Component : public Component
{
public:
	float_Component(float* value, uint8_t size, const float min, const float max, const uint8_t priority = 0);
	void encode(uint8_t* packet) override;
	uint8_t decode(uint8_t* packet) override;
protected:
	float* value;
	float min;
	float max;
	float resolution;
};

class char_Component : public Component
{
public:
	char_Component(uint8_t* value, const uint8_t priority = 0);
	void encode(uint8_t* packet) override;
	uint8_t decode(uint8_t* packet) override;
protected:
	uint8_t* value;
};