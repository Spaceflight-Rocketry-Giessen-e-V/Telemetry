/*
    RC1780HP.h - Library for using Radiocrafts RC1780HP RF modules.
    Created by ..., xx.xx.2025.
    Spaceflight Rocketry Giessen e.V.
    Licence...
*/

#ifndef RC1780HP_h
#define RC1780HP_h

#include "Arduino.h"

class RC1780HP
{
    public:
        RC1780HP(HardwareSerial* serialModule, uint8_t cfgpin, uint8_t rstpin, uint8_t ctspin, uint8_t rtspin);

        void begin(uint32_t baud_module);
        
        void reset();

        uint8_t setChannel(uint8_t channel);
        
        uint8_t setAddress_mode(uint8_t address);

        uint8_t readVoltage(float* result);

        uint8_t readRSSI(float* result);

        uint8_t readTemperature(int8_t* result);

        uint8_t readNon_Voltile_Memory(float* result);

        uint8_t readMemoryByte(uint8_t address, uint8_t* result);       // Private oder Public?

        

    private:
        uint8_t _rstpin;
        uint8_t _ctspin;
        uint8_t _cfgpin;
        uint8_t _rtspin;
        uint32_t _baud_module;
        HardwareSerial* serialModule;
        uint8_t _channel;
        uint8_t _output_power;
        uint8_t _destination_address;

        uint16_t serialWait(uint32_t delay_microsecond);
        void serialFlush();

        uint8_t enterConfig();
        uint8_t exitConfig();
        uint8_t sendConfigCommand(uint8_t command);
        unit8_t writeMemoryByte(uint8_t memory_address, uint8_t value);
};

#endif
