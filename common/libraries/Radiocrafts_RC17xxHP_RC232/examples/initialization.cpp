#include "Arduino.h"
#include "../Radiocrafts_RC17xxHP_RC232.h"

// Assigning arbitrary pins
uint8_t cfgpin = PIN_PB6;
uint8_t rstpin = PIN_PF4;
uint8_t ctspin = PIN_PB5;
uint8_t rtspin = PIN_PB7;

// Assigning an arbitrary serial port
HardwareSerial* SerialModule = &Serial0;

// Radio module initialization
RC17xxHP_RC232 rc1780hp(SerialModule, cfgpin, rstpin, ctspin, rtspin);

// Initialize radio transceiver and wait until communication is established
delay(3.2 * 10); // Necessary delay: t_{OFF-IDLE} = 3.2, safety factor 10
rc1780hp.begin(19200);
delay(3.2 * 10); // Necessary delay: t_{OFF-IDLE} = 3.2, safety factor 10
rc1780hp.ping();

// Before each use the non-volatile memory can be reset
while(rc1780hp.memory_Reset() != 0);

// The non-standard setting can be reconfigured
while(rc1780hp.set_RF_DATA_RATE(0x05) != 0);

// Resetting the module for the configuration to take place
rc1780hp.hard_reset();
rc1780hp.serial_Flush();