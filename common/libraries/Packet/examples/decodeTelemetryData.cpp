#include "../Packet.h"

// The received data packet (usually with nonzero values)
uint8_t packet[13] = { 0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xEE, 0x00 };

uint8_t stateTelemetry;
uint8_t statePower;
uint8_t stateSens;
uint8_t stateControl;
float heightGNSS133;
uint8_t satCountGNSS;
float hdopGNSS;
uint8_t temperatureElectronics;
uint8_t temperatureBattery;
uint8_t stateCapacitors;
uint8_t continuityPyros;
uint8_t pressureDecoupler;
uint8_t ldrDecoupler;
float voltageBattery;
float currentBattery;
float currentUmbilical;
uint8_t lowPowerMode;
float voltageBatteryCOTS;
float rssi;

uint8_t packet_identifier;
Packet::decodeFrame(packet, &packet_identifier)

if(packet_identifier == 1)
{
    Packet::decodeTelemetryData(packet, &stateTelemetry, &statePower, &stateSens, &stateControl, &heightGNSS, &satCountGNSS, &hdopGNSS, &temperatureElectronics, &temperatureBattery, &stateCapacitors, &continuityPyros, &pressureDecoupler, &ldrDecoupler, &voltageBattery, &currentBattery, &currentUmbilical, &stateUmbilical, &lowPowerMode, &voltageBatteryCOTS, &rssi);
}
