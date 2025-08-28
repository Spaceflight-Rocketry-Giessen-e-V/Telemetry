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

        
        uint8_t set_Address_mode(uint8_t address);
        
        uint8_t set_RSSI_Mode(uint8_t RSSI);

        uint8_t set_Packet_Length(uint8_t length);

        uint8_t set_Packet_Timeout(uint8_t time);

        uint8_t set_CRC_Mode(uint8_t CRC);

        uint8_t set_LED_Control(uint8_t LED);

        uint8_t set_Channel(uint8_t channel);



        uint8_t read_Address_mode(uint8_t* result);

        uint8_t read_RSSI_Mode(uint8_t* result);

        uint8_t read_Packet_Length(uint8_t* result);

        uint8_t read_Packet_Timeout(uint16_t* result);

        uint8_t read_CRC_Mode(uint8_t* result);

        uint8_t read_LED_Control(uint8_t* result);

        uint8_t read_Voltage(float* result);

        uint8_t read_Signal_Strength(float* result);

        uint8_t read_Temperature(int8_t* result);

        uint8_t read_Non_Voltile_Memory(float* result);

        uint8_t read_Memory_Byte(uint8_t address, uint8_t* result);


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

        uint16_t serial_Wait(uint32_t delay_microsecond);
        void serial_Flush();

        uint8_t enter_Config();
        uint8_t exit_Config();
        uint8_t send_Config_Command(uint8_t command);
        unit8_t write_Memory_Byte(uint8_t memory_address, uint8_t value);
};

#endif
