/*
    RC17xxHP-RC232 - Library for using Radiocrafts RC17xxHP-RC232 RF modules.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#ifndef RC17xxHP_RC232_h
#define RC17xxHP_RC232_h

#include "Arduino.h"

class RC17xxHP_RC232
{
    public:
        RC17xxHP_RC232(HardwareSerial* serialModule, uint8_t cfgpin, uint8_t rstpin, uint8_t ctspin, uint8_t rtspin);

        void begin(uint32_t baud_module);

        void serial_Flush();

        uint8_t ping();
        
        uint8_t hard_Reset();

        uint8_t soft_Reset();

        uint8_t memory_Reset();

        // Set functions

        uint8_t set_RF_CHANNEL(uint8_t value);

        uint8_t set_RF_POWER(uint8_t value);

        uint8_t set_RF_DATA_RATE(uint8_t value);

        uint8_t set_SLEEP_MODE(uint8_t value);

        uint8_t set_RSSI_MODE(uint8_t value);

        uint8_t set_PACKET_LENGTH(uint8_t value);

        uint8_t set_PACKET_TIMEOUT(uint8_t value);

        uint8_t set_PACKET_END_CHARACTER(uint8_t value);

        uint8_t set_ADDRESS_MODE(uint8_t value);

        uint8_t set_CRC_MODE(uint8_t value);

        uint8_t set_UID(uint8_t value);

        uint8_t set_SID(uint8_t value);

        uint8_t set_DID(uint8_t value);

        uint8_t set_BID(uint8_t value);

        uint8_t set_UART_BAUD_RATE(uint8_t value);

        uint8_t set_UART_FLOW_CONTROL(uint8_t value);

        uint8_t set_LED_CONTROL(uint8_t value);

        // Get functions

        uint8_t get_RF_CHANNEL(uint8_t* result);

        uint8_t get_RF_POWER(uint8_t* result);

        uint8_t get_RF_DATA_RATE(uint8_t* result);

        uint8_t get_SLEEP_MODE(uint8_t* result);

        uint8_t get_RSSI_MODE(uint8_t* result);

        uint8_t get_PACKET_LENGTH(uint8_t* result);

        uint8_t get_PACKET_TIMEOUT(uint8_t* result);

        uint8_t get_PACKET_END_CHARACTER(uint8_t* result);

        uint8_t get_ADDRESS_MODE(uint8_t* result);

        uint8_t get_CRC_MODE(uint8_t* result);

        uint8_t get_UID(uint8_t* result);

        uint8_t get_SID(uint8_t* result);

        uint8_t get_DID(uint8_t* result);

        uint8_t get_BID(uint8_t* result);

        uint8_t get_UART_BAUD_RATE(uint8_t* result);

        uint8_t get_UART_FLOW_CONTROL(uint8_t* result);

        uint8_t get_LED_CONTROL(uint8_t* result);

        // Read functions

        uint8_t read_RSSI(float* result);

        uint8_t read_TEMPERATURE(int8_t* result);

        uint8_t read_VOLTAGE(float* result);

        // Test modes

        //uint8_t TEST_MODE_0();

        //uint8_t TEST_MODE_1();

        //uint8_t TEST_MODE_2();

        //uint8_t TEST_MODE_3();

        //uint8_t TEST_MODE_4();

    private:
        uint8_t _rstpin;
        uint8_t _ctspin;
        uint8_t _cfgpin;
        uint8_t _rtspin;
        uint32_t _baud_module;
        HardwareSerial* serialModule;

        uint16_t serial_Wait(uint32_t delay_microseconds);

        uint8_t enter_Config();
        uint8_t exit_Config();
        uint8_t send_Config_Command(uint8_t command);
        uint8_t read_Memory_Byte(uint8_t address, uint8_t* result);
        uint8_t write_Memory_Byte(uint8_t memory_address, uint8_t value);
};

#endif
