#include "i2c_connectivity.h"

Subsystem::Subsystem(uint8_t i2cAddress, uint8_t pinLed, uint8_t* subsystemStatus, uint8_t** uint8List, uint8_t uint8Count, float** floatList, uint8_t floatCount)
{
    _i2cAddress = i2cAddress;
    _pinLed = pinLed;
    _stateLed = 0;
    _subsystemState = subsystemStatus;
    *_subsystemState = 0;
    _uint8List = uint8List;
    _uint8Count = uint8Count;
    _floatList = floatList;
    _floatCount = floatCount;
}

void Subsystem::connectionCheck()
{
    Wire.beginTransmission(_i2cAddress);
    uint8_t i2cStatus = (Wire.endTransmission() == 0);
    *_subsystemState = i2cStatus; // Success -> 1, Failure -> 0
}

void Subsystem::dataGet()
{
    if(*_subsystemState != 0)
    {
        const uint8_t byteCount = _uint8Count * 1 + _floatCount * 4;
        Wire.requestFrom(_i2cAddress, byteCount);
        uint8_t receivedBytes[byteCount];
        for(uint8_t i = 0; i < byteCount; i++)
        {
            receivedBytes[i] = Wire.read();
        }
        uint8_t bytePointer = 0;
        for(uint8_t i = 0; i < _uint8Count; i++)
        {
            *_uint8List[i] = receivedBytes[bytePointer];
            bytePointer += 1;
        }
        for(uint8_t i = 0; i < _floatCount; i++)
        {
            *_floatList[i] = bytesToFloat(&receivedBytes[bytePointer]);
            bytePointer += 4;
        }
    }
}

void Subsystem::ledUpdate()
{
    if(*_subsystemState == 1)
    {
        digitalWrite(_pinLed, 1 - _stateLed);
        _stateLed = 1 - _stateLed;
    }
    else if(*_subsystemState == 2 || *_subsystemState == 3)
    {
        digitalWrite(_pinLed, HIGH);
        _stateLed = 1;
    }
    else if(*_subsystemState == 0)
    {
        digitalWrite(_pinLed, LOW);
        _stateLed = 0;
    }
}

uint8_t Subsystem::statusGet()
{
    return *_subsystemState;
}

float Subsystem::bytesToFloat(uint8_t* bytes)
{
    uint32_t combinedBytes = ((uint32_t)bytes[4] << 24) | ((uint32_t)bytes[3] << 16) | ((uint32_t)bytes[2] << 8) | ((uint32_t)bytes[1]);
    float result = *(float*)&combinedBytes;
    return result;
}

void subsystemsConnCheck(Subsystem** subsystemsList, uint8_t subsystemsCount)
{
    for(uint8_t i = 0; i < subsystemsCount; i++)
    {
        if(subsystemsList[i]->statusGet() == 0)
        {
            subsystemsList[i]->connectionCheck();
        }
    }
}

void subsystemsDataGet(Subsystem** subsystemsList, uint8_t subsystemsCount)
{
    for(uint8_t i = 0; i < subsystemsCount; i++)
    {
        subsystemsList[i]->dataGet();
    }
}

void subsystemsLedUpdate(Subsystem** subsystemsList, uint8_t subsystemsCount)
{
    for(uint8_t i = 0; i < subsystemsCount; i++)
    {
        subsystemsList[i]->ledUpdate();
    }
}