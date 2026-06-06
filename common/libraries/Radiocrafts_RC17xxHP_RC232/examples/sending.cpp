#include "Arduino.h"
#include "../Radiocrafts_RC17xxHP_RC232.h"

// This example uses an unique end byte to trigger the transmission. As an alternative, the PACKET_TIMEOUT or PACKET_LENGTH parameters can be used.

// Initialization according to the initalization example

// Assigning pins
uint8_t pinCFG = PIN_PA5;
uint8_t pinRST = PIN_PG7;
uint8_t pinCTS = PIN_PA3;
uint8_t pinRTS = PIN_PA4;

// Assigning a serial port
uint8_t pinTX = PIN_PA0;
uint8_t pinRX = PIN_PA1;
HardwareSerial *SerialModule = &Serial0;
uint32_t baudrate = 19200;

// Radio module initialization
RC17xxHP_RC232 rc1780hp(SerialModule, pinTX, pinRX, 19200, pinCFG, pinRST, pinCTS, pinRTS);

delay(3.2 * 10);
rc1780hp.begin();
delay(3.2 * 10);
rc1780hp.ping();

while (rc1780hp.set_PACKET_END_CHARACTER(0xEE) != 0)
    ; // When 0xEE is send to the radio module, the whole buffer is transmitted

rc1780hp.resetHard();
rc1780hp.flush();

// Send a two byte packet
uint8_t packet[] = {0xA4, 0xEE}; // Arbitrary data byte with the unique end byte
rc1780hp.send(packet, 2);