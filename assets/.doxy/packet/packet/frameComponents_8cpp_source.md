

# File frameComponents.cpp

[**File List**](files.md) **>** [**DynamicPacketCodec**](dir_3b1e16a071e0cb7dba7bed78c84278d9.md) **>** [**src**](dir_0e3c0571c94c2f89fbf113628d83e1ea.md) **>** [**frameComponents.cpp**](frameComponents_8cpp.md)

[Go to the documentation of this file](frameComponents_8cpp.md)


```C++
#include "frameComponents.h"
#include "baseClasses.h"

// const FRAME COMPONENT

const_Component::const_Component(uint32_t value, uint8_t size, const uint8_t priority) : Component(size, priority)
{
    this->value = (0xFFFFFFFF >> (32 - size)) & value;
}

void const_Component::encode(uint8_t* packet)
{
    bitWriter(value, packet);
}

uint8_t const_Component::decode(uint8_t* packet)
{
    uint32_t dataBits = 0;
    bitReader(&dataBits, packet);
    bitReset(packet);

    if (dataBits == value)
    {
        return 0;
    }
    else
    {
        return 1;
    }
}

// empty FRAME COMPONENT

empty_Component::empty_Component(uint8_t size) : Component(size, 0) {}

void empty_Component::encode(uint8_t* packet) {}

uint8_t empty_Component::decode(uint8_t* packet)
{
    return 0;
}

// parity FRAME COMPONENT

parity_Component::parity_Component(const uint8_t priority) : Component(1, priority) {}

void parity_Component::encode(uint8_t* packet)
{
    uint8_t parityBit = 0;
    for (uint8_t bytePos = 0; bytePos < this->packet->getByteSize(); bytePos++)
    {
        uint8_t count = 0;
        for (uint8_t bitPos = 0; bitPos < 8; bitPos++)
        {
            if (packet[bytePos] & (1 << bitPos))
            {
                count++;
            }
        }
        parityBit ^= (count % 2 != 0);
    }

    bitWriter(parityBit, packet);
}

uint8_t parity_Component::decode(uint8_t* packet)
{
    uint8_t count = 0;
    for (uint8_t bytePos = 0; bytePos < this->packet->getByteSize(); bytePos++)
    {
        for (uint8_t bitPos = 0; bitPos < 8; bitPos++)
        {
            if (packet[bytePos] & (1 << bitPos))
            {
                count++;
            }
        }
    }
    bitReset(packet);

    return (count % 2);
}

// cobs FRAME COMPONENT

cobs_Component::cobs_Component(uint8_t markerByte, uint8_t size, const uint8_t priority) : Component(size, priority)
{
    this->markerByte = markerByte;
}

void cobs_Component::encode(uint8_t* packet)
{
    uint8_t cobsByte = 0;
    for (uint8_t bytePos = 1; bytePos < this->packet->getByteSize(); bytePos++)
    {
        if (packet[bytePos] == markerByte)
        {
            packet[bytePos] = 0;
            if (cobsByte == 0)
            {
                bitWriter(bytePos, packet);
            }
            else
            {
                packet[cobsByte] = bytePos;
            }
            cobsByte = bytePos;
        }
    }
}

uint8_t cobs_Component::decode(uint8_t* packet)
{
    uint32_t tmp1 = 0;
    uint32_t tmp2 = 0;
    bitReader(&tmp2, packet);
    bitReset(packet);
    while (tmp2 != 0x00)
    {
        if(tmp2 == tmp1) // Cyclic
        {
            return 1;
        }
        else if(tmp2 < tmp1) // Backwards
        {
            return 1;
        }
        else if(tmp2 >= this->packet->getByteSize()) // Out-of-range
        {
            return 1;
        }
        tmp1 = tmp2;
        tmp2 = packet[tmp1];
        packet[tmp1] = markerByte;
    }
    return 0;
}
```


