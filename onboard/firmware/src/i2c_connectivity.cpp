#include "i2c_connectivity.h"

Subsystem::Subsystem(uint8_t i2cAddress, uint8_t pinLed, uint8_t* subsystemStatus, uint8_t** uint8List, uint8_t uint8Count, float** floatList, uint8_t floatCount)
{
    _i2cAddress = i2cAddress;
    _pinLed = pinLed;
    _stateLed = 0;
    _subsystemStatus = subsystemStatus;
    *_subsystemStatus = 4;
    _uint8List = uint8List;
    _uint8Count = uint8Count;
    _floatList = floatList;
    _floatCount = floatCount;
}

void Subsystem::connectionCheck()
{
    Wire.beginTransmission(_i2cAddress);
    uint8_t i2cStatus = (Wire.endTransmission() != 0);
    *_subsystemStatus = i2cStatus * 4; // Success -> 0, Failure -> 4
}

void Subsystem::dataGet()
{
    if(*_subsystemStatus != 4)
    {
        const uint8_t byteCount = _uint8Count * 8 + _floatCount * 32;
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
    if(*_subsystemStatus == 0)
    {
        digitalWrite(_pinLed, 1 - _stateLed);
        _stateLed = 1 - _stateLed;
    }
    else if(*_subsystemStatus >= 1 && *_subsystemStatus <= 3)
    {
        digitalWrite(_pinLed, HIGH);
        _stateLed = 1;
    }
    else if(*_subsystemStatus == 4)
    {
        digitalWrite(_pinLed, LOW);
        _stateLed = 0;
    }
}

uint8_t Subsystem::statusGet()
{
    return *_subsystemStatus;
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
        if(subsystemsList[i]->statusGet() == 4)
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