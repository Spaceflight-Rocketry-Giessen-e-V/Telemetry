#include "Arduino.h"
#include "../RC1780HP.h"

// This example uses an unique end byte to trigger the transmission. Alternativly the PACKET_TIMEOUT or PACKET_LENGTH parameters can be used.

// Initialization according to the initalization example

uint8_t cfgpin = PIN_PB6;
uint8_t rstpin = PIN_PF4;
uint8_t ctspin = PIN_PB5;
uint8_t rtspin = PIN_PB7;

HardwareSerial* SerialModule = &Serial0;

RC1780HP rc1780hp(SerialModule, cfgpin, rstpin, ctspin, rtspin);

delay(3.2 * 10);
rc1780hp.begin(19200);
delay(3.2 * 10);
rc1780hp.ping();

while(rc1780hp.memory_Reset() != 0);
while(rc1780hp.set_Packet_End_Character(0xEE) != 0);        // When 0xEE is send to the radio module, the whole buffer is transmitted
rc1780hp.hard_reset();
rc1780hp.serial_Flush();

// Send a two byte packet
SerialModule->write(0xA4);                                  // Arbitrary data byte
SerialModule->write(0xEE);                                  // Unique end byte triggering transmission