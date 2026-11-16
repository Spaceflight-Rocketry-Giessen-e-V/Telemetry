

# File dataComponents.h

[**File List**](files.md) **>** [**DynamicPacketCodec**](dir_3b1e16a071e0cb7dba7bed78c84278d9.md) **>** [**include**](dir_d3910b10d935f2681f2ee83ac211d5ad.md) **>** [**dataComponents.h**](dataComponents_8h.md)

[Go to the documentation of this file](dataComponents_8h.md)


```C++
#pragma once
#include "baseClasses.h"

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
```


