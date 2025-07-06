/*
    RC232.h - Library for using Radiocrafts RC232 RF modules.
    Created by ..., xx.xx.2025.
    Licence...
*/

#ifndef RC232_h
#define RC232_h

#include "Arduino.h"

class RC232
{
    public:
        RC232();
        void begin();

    private:
        int ledpin1;
        int ledpin2;
        int ledpin3;
        int ledpin4;
        int ledpin5;
        int ledpin6;
        int ledpin7;
        int ledpin8;
        HardwareSerial SerialModule;
        HardwareSerial SerialTTL;
        HardwareSerial SerialHeader;
        int serial_module_wait(uint32_t delay_microsecond);
        int serial_ttl_wait(uint32_t delay_microsecond);
        int serial_header_wait(uint32_t delay_microsecond);
};

#endif
