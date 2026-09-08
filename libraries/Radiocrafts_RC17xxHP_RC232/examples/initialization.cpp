#include "Arduino.h"
#include "../Radiocrafts_RC17xxHP_RC232.h"

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

// Initialize radio transceiver and wait until communication is established
delay(3.2 * 10); // Necessary delay: t_{OFF-IDLE} = 3.2, safety factor 10
rc1780hp.begin();
delay(3.2 * 10); // Necessary delay: t_{OFF-IDLE} = 3.2, safety factor 10
rc1780hp.ping();

// The non-standard setting can be reconfigured
while (rc1780hp.set_RF_DATA_RATE(0x05) != 0)
    ;
// ...

// Resetting the module for the configuration to take place
rc1780hp.resetHard();
rc1780hp.flush();