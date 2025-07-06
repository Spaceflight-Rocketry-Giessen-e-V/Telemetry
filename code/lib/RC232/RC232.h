/*
    RC232.h - Library for using Radiocrafts RC232 RF modules.
    Created by ..., xx.xx.2025.
    Spaceflight Rocketry Giessen e.V.
    Licence...
*/

#ifndef RC232_h
#define RC232_h

#include "Arduino.h"

class RC232
{
    public:
        RC232();
        void begin(uint32_t baud_module, uint32_t baud_ttl, uint32_t baud_header);

    private:
        uint8_t ledpin1;
        uint8_t ledpin2;
        uint8_t ledpin3;
        uint8_t ledpin4;
        uint8_t ledpin5;
        uint8_t ledpin6;
        uint8_t ledpin7;
        uint8_t ledpin8;
        uint8_t d1pin;
        uint8_t d2pin;
        uint8_t d3pin;
        uint8_t armpin;
        uint8_t slppin;
        uint8_t rstpin;
        uint8_t ctspin;
        uint8_t cfgpin;
        uint8_t rtspin;
        uint32_t baud_module;
        uint32_t baud_ttl;
        uint32_t baud_header;
        HardwareSerial* SerialModule;
        HardwareSerial* SerialTTL;
        HardwareSerial* SerialHeader;
        uint16_t serial_wait(HardwareSerial* SerialTmp, uint32_t delay_microsecond);
        uint8_t enter_config_mode();
        uint8_t exit_config_mode();
};

#endif
