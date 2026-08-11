#include "../Packet.h"

uint8_t packet[12] = { 0 };

uint8_t stateTelemetry = 3;
uint8_t statePower = 3;
uint8_t stateSens = 2;
uint8_t stateControl = 3;
float heightGNSS = 2133.1;
uint8_t satCountGNSS = 5;
float hdopGNSS = 1.0;
uint8_t temperatureElectronics = 50;
uint8_t temperatureBattery = 40;
uint8_t stateCapacitors = 7;
uint8_t continuityPyros = 3;
uint8_t pressureDecoupler = 1;
uint8_t ldrDecoupler = 0;
float voltageBattery = 7.2;
float currentBattery = 1.2;
float currentUmbilical = 1.1;
uint8_t lowPowerMode = 1;
float voltageBatteryCOTS = 9.0;

Packet::encodeTelemetryData(packet, stateTelemetry, statePower, stateSens, stateControl, heightGNSS, satCountGNSS, hdopGNSS, temperatureElectronics, temperatureBattery, stateCapacitors, continuityPyros, pressureDecoupler, ldrDecoupler, voltageBattery, currentBattery, currentUmbilical, stateUmbilical, lowPowerMode, voltageBatteryCOTS);
Packet::encodeFrame(packet, 1);
// The 'packet' array can now be transmitted or used otherwise.