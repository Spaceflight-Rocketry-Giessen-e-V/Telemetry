/*
    RC1780HP - Library for using Radiocrafts RC1780HP-RC232 RF modules.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#ifndef RC1780HP_h
#define RC1780HP_h

#include "Arduino.h"

class RC1780HP
{
    public:
        RC1780HP(HardwareSerial* serialModule, uint8_t cfgpin, uint8_t rstpin, uint8_t ctspin, uint8_t rtspin);

        void begin(uint32_t baud_module);

        void serial_Flush();

        uint8_t ping();
        
        uint8_t hard_reset();

        uint8_t soft_Reset();

        uint8_t memory_Reset();

        // Set functions
        
        uint8_t set_RSSI_Mode(uint8_t value);

        uint8_t set_Packet_Timeout(uint8_t value);

        uint8_t set_Packet_End_Character(uint8_t value);
        
        uint8_t set_Address_Mode(uint8_t value);

        uint8_t set_CRC_Mode(uint8_t value);

        uint8_t set_LED_Control(uint8_t value);

        // Read functions

        uint8_t read_RSSI_Mode(uint8_t* result);

        uint8_t read_Packet_Timeout(uint8_t* result);

        uint8_t read_Packet_End_Character(uint8_t* result);

        uint8_t read_Address_Mode(uint8_t* result);

        uint8_t read_CRC_Mode(uint8_t* result);

        uint8_t read_LED_Control(uint8_t* result);

        uint8_t read_Voltage(float* result);

        uint8_t read_Signal_Strength(float* result);

        uint8_t read_Temperature(int8_t* result);

        // uint8_t read_Non_Voltile_Memory(float* result);

        // Test modes

        uint8_t rf_Test_Mode(uint16_t time);  

    private:
        uint8_t _rstpin;
        uint8_t _ctspin;
        uint8_t _cfgpin;
        uint8_t _rtspin;
        uint32_t _baud_module;
        HardwareSerial* serialModule;

        uint16_t serial_Wait(uint32_t delay_microsecond);

        uint8_t enter_Config();
        uint8_t exit_Config();
        uint8_t send_Config_Command(uint8_t command);
        uint8_t read_Memory_Byte(uint8_t address, uint8_t* result);
        uint8_t write_Memory_Byte(uint8_t memory_address, uint8_t value);
};

#endif
