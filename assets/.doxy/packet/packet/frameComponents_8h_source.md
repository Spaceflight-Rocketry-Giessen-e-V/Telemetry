

# File frameComponents.h

[**File List**](files.md) **>** [**DynamicPacketCodec**](dir_3b1e16a071e0cb7dba7bed78c84278d9.md) **>** [**include**](dir_d3910b10d935f2681f2ee83ac211d5ad.md) **>** [**frameComponents.h**](frameComponents_8h.md)

[Go to the documentation of this file](frameComponents_8h.md)


```C++
#pragma once
#include "baseClasses.h"

class const_Component : public Component
{
public:
    const_Component(uint32_t value, uint8_t size, const uint8_t priority = 0);
    void encode(uint8_t* packet) override;
    uint8_t decode(uint8_t* packet) override;
protected:
    uint32_t value;
};

class empty_Component : public Component
{
public:
    empty_Component(uint8_t size);
    void encode(uint8_t* packet) override;
    uint8_t decode(uint8_t* packet) override;
};

class parity_Component : public Component
{
public:
    parity_Component(const uint8_t priority = 1);
    void encode(uint8_t* packet) override;
    uint8_t decode(uint8_t* packet) override;
};

class cobs_Component : public Component
{
public:
    cobs_Component(uint8_t markerByte, uint8_t size, const uint8_t priority = 127);
    void encode(uint8_t* packet) override;
    uint8_t decode(uint8_t* packet) override;
protected:
    uint8_t markerByte;
    uint8_t size;
};
```


