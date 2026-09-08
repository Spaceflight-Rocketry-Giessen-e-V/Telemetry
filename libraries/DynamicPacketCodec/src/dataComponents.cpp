#include "dataComponents.h"

// uint8_t DATA COMPONENT //

uint8_t_Component::uint8_t_Component(uint8_t* value, uint8_t size, const uint8_t min, const uint8_t max, const uint8_t priority) : Component(size, priority)
{
	this->value = value;
	this->min = min;
	this->max = max;
	resolution = (max - min) / (pow(2, size) - 1);
}

void uint8_t_Component::encode(uint8_t* packet)
{
	*value = *value < min ? min : *value;
	*value = *value > max ? max : *value;

	uint32_t dataBits = (uint32_t)((*value - min) / resolution);

	bitWriter(dataBits, packet);
}

uint8_t uint8_t_Component::decode(uint8_t* packet)
{
	uint32_t dataBits = 0;
	bitReader(&dataBits, packet);

	*value = (uint8_t)dataBits * resolution + min;

	return 0;
}

// float DATA COMPONENT //

float_Component::float_Component(float* value, uint8_t size, const float min, const float max, const uint8_t priority) : Component(size, priority)
{
	this->value = value;
	this->min = min;
	this->max = max;
	resolution = (max - min) / (pow(2, size) - 1);
}

void float_Component::encode(uint8_t* packet)
{
	*value = *value < min ? min : *value;
	*value = *value > max ? max : *value;

	uint32_t dataBits = (uint32_t)((*value - min) / resolution);

	bitWriter(dataBits, packet);
}

uint8_t float_Component::decode(uint8_t* packet)
{
	uint32_t dataBits = 0;
	bitReader(&dataBits, packet);

	*value = (float)dataBits * resolution + min;

	return 0;
}

// char DATA COMPONENT

char_Component::char_Component(uint8_t* value, const uint8_t priority) : Component(5, priority)
{
	this->value = value;
}

void char_Component::encode(uint8_t* packet)
{
	uint32_t dataBits = 0;

	if (*value >= 'A' && *value <= 'Z')
	{
		dataBits = *value - 'A' + 1;
	}
	else if (*value >= 'a' && *value <= 'z')
	{
		dataBits = *value - 'a' + 1;
	}

	bitWriter(dataBits, packet);
}

uint8_t char_Component::decode(uint8_t* packet)
{
	uint32_t dataBits = 0;
	bitReader(&dataBits, packet);

	if (dataBits > 0)
	{
		*value = dataBits - 1 + 'a';
	}
	else
	{
		*value = 0;
	}

	return 0;
}