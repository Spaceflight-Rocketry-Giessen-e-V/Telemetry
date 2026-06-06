/*
    RC17xxHP-RC232 - Library for using Radiocrafts RC17xxHP-RC232 RF modules.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#ifndef RC17xxHP_RC232_h
#define RC17xxHP_RC232_h

#include "Arduino.h"

class RC17xxHP_RC232
{
public:
    RC17xxHP_RC232(HardwareSerial *serial, uint8_t pinTX, uint8_t pinRX, uint32_t baudrate, uint8_t pinCFG, uint8_t pinRST, uint8_t pinCTS, uint8_t pinRTS);

    void begin();

    uint8_t ping();

    // Serial Functions

    void flush();

    uint16_t serialWait(uint32_t delayMicroseconds);

    void send(uint8_t *bytes, uint8_t length);
    void send(uint8_t byte);

    void read(uint8_t *bytes, uint8_t length);
    uint8_t read();

    uint8_t available();

    // Reset Functions

    uint8_t resetHard();

    uint8_t resetSoft();

    uint8_t memoryReset();

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

    uint8_t get_RF_CHANNEL(uint8_t *result);

    uint8_t get_RF_POWER(uint8_t *result);

    uint8_t get_RF_DATA_RATE(uint8_t *result);

    uint8_t get_SLEEP_MODE(uint8_t *result);

    uint8_t get_RSSI_MODE(uint8_t *result);

    uint8_t get_PACKET_LENGTH(uint8_t *result);

    uint8_t get_PACKET_TIMEOUT(uint8_t *result);

    uint8_t get_PACKET_END_CHARACTER(uint8_t *result);

    uint8_t get_ADDRESS_MODE(uint8_t *result);

    uint8_t get_CRC_MODE(uint8_t *result);

    uint8_t get_UID(uint8_t *result);

    uint8_t get_SID(uint8_t *result);

    uint8_t get_DID(uint8_t *result);

    uint8_t get_BID(uint8_t *result);

    uint8_t get_UART_BAUD_RATE(uint8_t *result);

    uint8_t get_UART_FLOW_CONTROL(uint8_t *result);

    uint8_t get_LED_CONTROL(uint8_t *result);

    // Read functions

    uint8_t read_RSSI(float *result);

    uint8_t read_TEMPERATURE(int8_t *result);

    uint8_t read_VOLTAGE(float *result);

    // Test modes

    // uint8_t TEST_MODE_0();

    // uint8_t TEST_MODE_1();

    // uint8_t TEST_MODE_2();

    // uint8_t TEST_MODE_3();

    // uint8_t TEST_MODE_4();

private:
    uint8_t _pinRST;
    uint8_t _pinCTS;
    uint8_t _pinCFG;
    uint8_t _pinRTS;
    uint8_t _pinTX;
    uint8_t _pinRX;
    uint32_t _baudrate;
    HardwareSerial *_serial;

    uint8_t configEnter();
    uint8_t configExit();
    uint8_t configCommand(uint8_t command);
    uint8_t memoryRead(uint8_t address, uint8_t *result);
    uint8_t memoryWrite(uint8_t address, uint8_t value);
};

#endif
