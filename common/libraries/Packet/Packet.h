#pragma once
#include <vector>
#include "component.h"
#include "dataComponents.h"
#include "frameComponents.h"

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
