#include "utility.h"

// LEDs states
#define SETUPBEGIN 1
#define SETUPRADIOMODULS 2
#define SETUPEND 3
#define RADIOMODUL_ONE 4
#define RADIOMODUL_TWO 5

static uint8_t radioModuleConfigure(RC17xxHP_RC232 *radioModule)
{
    radioModule->begin();
    radioModule->resetHard();     // initial reboot to clear setting
    if (radioModule->ping() != 0) // confirm response
    {
        return 1;
    }
    if (radioModule->set_RF_DATA_RATE(0x05) != 0) // radio data rate
    {
        return 1;
    }
    if (radioModule->set_RSSI_MODE(0x01) != 0) // append signal strength to packet
    {
        return 1;
    }
    if (radioModule->set_PACKET_LENGTH(0x01) != 0) // send every byte when it arrives
    {
        return 1;
    }
    if (radioModule->set_PACKET_TIMEOUT(0x01) != 0) // send byte 32 ms after it arrives (backup when packet length fails)
    {
        return 1;
    }
    if (radioModule->set_ADDRESS_MODE(0x00) != 0) // addressing off (broadcast)
    {
        return 1;
    }
    if (radioModule->set_CRC_MODE(0x00) != 0) // CRC off
    {
        return 1;
    }
    if (radioModule->set_LED_CONTROL(0x01) != 0) // enable the module's status LED
    {
        return 1;
    }
    radioModule->resetHard(); // reboot settings take effect
    radioModule->flush();     // flush serial buffer
    return 0;
}

// Configures both radio modules; lights each module's status LED on success and sounds buzzzer
void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct *pinLed)
{
    // fallback loop
    uint8_t error1780 = radioModuleConfigure(rc1780hp); // module 1: downlink (TX)
    if (error1780 == 0)
    {
        ledUpdate(RADIOMODUL_ONE, pinLed);
    }

    uint8_t error1701 = radioModuleConfigure(rc1701hp); // module 2: uplink (RX)
    if (error1701 == 0)
    {
        ledUpdate(RADIOMODUL_TWO, pinLed);
    }

    if (error1780 != 0 || error1701 != 0)
    {
        exit(1);
    }
}

uint8_t commandReceive(HardwareSerial *serialUSB)
{
    // availability
    if (serialUSB->available() == 0)
    {
        return 0;
    }
    else
    {
        uint8_t command = serialUSB->read();
        return command;
    }
}

void commandExecute(uint8_t command, RC17xxHP_RC232 *radioModule)
{
    uint8_t packet;
    if (command != 0)
    {
        Packet::encodeCommand(command, &packet);
        radioModule->send(packet);
    }
}

uint8_t packetReceive(RC17xxHP_RC232 *radioModule, uint8_t *packetBuffer, uint8_t *packetBufferIndex, dataStruct *dataVariables)
{
    while (radioModule->available() != 0)
    {
        packetBuffer[*packetBufferIndex] = radioModule->read();
        (*packetBufferIndex)++;
    }

    if (packetBuffer[*packetBufferIndex - 2] == 0xEE) // -2 because of rssi
    {

        if (*packetBufferIndex >= 13)
        {
            dataVariables->timeSinceLastPacket = millis() - dataVariables->timestampLastPacket;
            dataVariables->timestampLastPacket = millis();

            uint8_t packetIdentifier;
            if (Packet::decodeFrame(&packetBuffer[*packetBufferIndex - 13], &packetIdentifier) == 0)
            {

                if (packetIdentifier == 0)
                {

                    Packet::decodeFlightData(&packetBuffer[*packetBufferIndex - 13], &dataVariables->acceleration, &dataVariables->heightPressure, &dataVariables->flightEvents, &dataVariables->latitude, &dataVariables->longitude, &dataVariables->rssi);
                }
                else if (packetIdentifier == 1)
                {

                    Packet::decodeTelemetryData(&packetBuffer[*packetBufferIndex - 13], &dataVariables->stateTelemetry, &dataVariables->statePower, &dataVariables->stateSens, &dataVariables->stateControl, &dataVariables->heightGNSS, &dataVariables->satCountGNSS, &dataVariables->hdopGNSS, &dataVariables->temperatureElectronics, &dataVariables->temperatureBattery, &dataVariables->stateCapacitors, &dataVariables->continuityPyros, &dataVariables->pressureDecoupler, &dataVariables->ldrDecoupler, &dataVariables->voltageBattery, &dataVariables->currentBattery, &dataVariables->currentUmbilical, &dataVariables->stateUmbilical, &dataVariables->lowPowerMode, &dataVariables->voltageBatteryCOTS, &dataVariables->rssi);
                }
            }
            *packetBufferIndex = 0;
            return 0;
        }
    }
    // Serial5.print("nach decode");
    if (*packetBufferIndex > 31)
    {
        *packetBufferIndex = 0;
    }
    return 1;
}

void dataSendUsb(HardwareSerial *serialUSB, dataStruct *dataVariables)
{
    serialUSB->print("\n");
    serialUSB->print("Acceleration: ");
    serialUSB->println(dataVariables->acceleration);
    serialUSB->print("Height (Pressure): ");
    serialUSB->println(dataVariables->heightPressure);
    serialUSB->print("Flight Events: ");
    serialUSB->println(dataVariables->flightEvents);
    serialUSB->print("Latitude: ");
    serialUSB->println(dataVariables->latitude);
    serialUSB->print("Longitude: ");
    serialUSB->println(dataVariables->longitude);
    serialUSB->print("State Telemetry: ");
    serialUSB->println(dataVariables->stateTelemetry);
    serialUSB->print("State Power Supply: ");
    serialUSB->println(dataVariables->statePower);
    serialUSB->print("State Sensorics: ");
    serialUSB->println(dataVariables->stateSens);
    serialUSB->print("State Flight Control: ");
    serialUSB->println(dataVariables->stateControl);
    serialUSB->print("Height (GNSS): ");
    serialUSB->println(dataVariables->heightGNSS);
    serialUSB->print("GNSS Satellite Count: ");
    serialUSB->println(dataVariables->satCountGNSS);
    serialUSB->print("GNSS HDOP: ");
    serialUSB->println(dataVariables->hdopGNSS);
    serialUSB->print("Electronics Temperature: ");
    serialUSB->println(dataVariables->temperatureElectronics);
    serialUSB->print("Battery Temperature: ");
    serialUSB->println(dataVariables->temperatureBattery);
    serialUSB->print("Capacitors State: ");
    serialUSB->println(dataVariables->stateCapacitors);
    serialUSB->print("Pyros Continuity: ");
    serialUSB->println(dataVariables->continuityPyros);
    serialUSB->print("Decoupler Pressure: ");
    serialUSB->println(dataVariables->pressureDecoupler);
    serialUSB->print("Decoupler LDR: ");
    serialUSB->println(dataVariables->ldrDecoupler);
    serialUSB->print("Battery Voltage: ");
    serialUSB->println(dataVariables->voltageBattery);
    serialUSB->print("Battery Current: ");
    serialUSB->println(dataVariables->currentBattery);
    serialUSB->print("Umbilical Current: ");
    serialUSB->println(dataVariables->currentUmbilical);
    serialUSB->print("Umbilical State: ");
    serialUSB->println(dataVariables->stateUmbilical);
    serialUSB->print("Low Power Mode: ");
    serialUSB->println(dataVariables->lowPowerMode);
    serialUSB->print("COTS Battery Voltage: ");
    serialUSB->println(dataVariables->voltageBatteryCOTS);
    serialUSB->print("RSSI: ");
    serialUSB->println(dataVariables->rssi);
    serialUSB->print("Time Since Last Packet: ");
    serialUSB->println(dataVariables->timeSinceLastPacket);
}

void ledUpdate(uint8_t state, ledStruct *pinLed)
{
    switch (state)
    {
    case SETUPBEGIN:
        digitalWrite(pinLed->R, HIGH);
        digitalWrite(pinLed->G, LOW);
        digitalWrite(pinLed->B, LOW);
        break;
    case SETUPRADIOMODULS:
        digitalWrite(pinLed->R, LOW);
        digitalWrite(pinLed->G, LOW);
        digitalWrite(pinLed->B, HIGH);
        break;
    case SETUPEND:
        digitalWrite(pinLed->R, LOW);
        digitalWrite(pinLed->G, HIGH);
        digitalWrite(pinLed->B, LOW);
        break;
    case RADIOMODUL_ONE:
        digitalWrite(pinLed->D2, HIGH);
        break;
    case RADIOMODUL_TWO:
        digitalWrite(pinLed->D3, HIGH);
        break;
    default:
        break;
    }
}

void ledRssiUpdate(float rssi, ledStruct *pinLed)
{
    // RGB LED (RSSI)
    if (rssi > -40) // High signal strength
    {
        digitalWrite(pinLed->rssi_1, HIGH);
        digitalWrite(pinLed->rssi_2, HIGH);
        digitalWrite(pinLed->rssi_3, HIGH);
        digitalWrite(pinLed->rssi_4, HIGH);
        digitalWrite(pinLed->rssi_5, HIGH);
        digitalWrite(pinLed->rssi_6, HIGH);
        digitalWrite(pinLed->rssi_7, HIGH);
        digitalWrite(pinLed->rssi_8, HIGH);
    }
    else if (rssi > -50)
    {
        digitalWrite(pinLed->rssi_1, HIGH);
        digitalWrite(pinLed->rssi_2, HIGH);
        digitalWrite(pinLed->rssi_3, HIGH);
        digitalWrite(pinLed->rssi_4, HIGH);
        digitalWrite(pinLed->rssi_5, HIGH);
        digitalWrite(pinLed->rssi_6, HIGH);
        digitalWrite(pinLed->rssi_7, HIGH);
        digitalWrite(pinLed->rssi_8, LOW);
    }
    else if (rssi > -60)
    {
        digitalWrite(pinLed->rssi_1, HIGH);
        digitalWrite(pinLed->rssi_2, HIGH);
        digitalWrite(pinLed->rssi_3, HIGH);
        digitalWrite(pinLed->rssi_4, HIGH);
        digitalWrite(pinLed->rssi_5, HIGH);
        digitalWrite(pinLed->rssi_6, HIGH);
        digitalWrite(pinLed->rssi_7, LOW);
        digitalWrite(pinLed->rssi_8, LOW);
    }
    else if (rssi > -70) // Medium signal strength
    {
        digitalWrite(pinLed->rssi_1, HIGH);
        digitalWrite(pinLed->rssi_2, HIGH);
        digitalWrite(pinLed->rssi_3, HIGH);
        digitalWrite(pinLed->rssi_4, HIGH);
        digitalWrite(pinLed->rssi_5, HIGH);
        digitalWrite(pinLed->rssi_6, LOW);
        digitalWrite(pinLed->rssi_7, LOW);
        digitalWrite(pinLed->rssi_8, LOW);
    }
    else if (rssi > -80)
    {
        digitalWrite(pinLed->rssi_1, HIGH);
        digitalWrite(pinLed->rssi_2, HIGH);
        digitalWrite(pinLed->rssi_3, HIGH);
        digitalWrite(pinLed->rssi_4, HIGH);
        digitalWrite(pinLed->rssi_5, LOW);
        digitalWrite(pinLed->rssi_6, LOW);
        digitalWrite(pinLed->rssi_7, LOW);
        digitalWrite(pinLed->rssi_8, LOW);
    }
    else if (rssi > -90)
    {
        digitalWrite(pinLed->rssi_1, HIGH);
        digitalWrite(pinLed->rssi_2, HIGH);
        digitalWrite(pinLed->rssi_3, HIGH);
        digitalWrite(pinLed->rssi_4, LOW);
        digitalWrite(pinLed->rssi_5, LOW);
        digitalWrite(pinLed->rssi_6, LOW);
        digitalWrite(pinLed->rssi_7, LOW);
        digitalWrite(pinLed->rssi_8, LOW);
    }
    else if (rssi > -100) // Low signal strength
    {
        digitalWrite(pinLed->rssi_1, HIGH);
        digitalWrite(pinLed->rssi_2, HIGH);
        digitalWrite(pinLed->rssi_3, LOW);
        digitalWrite(pinLed->rssi_4, LOW);
        digitalWrite(pinLed->rssi_5, LOW);
        digitalWrite(pinLed->rssi_6, LOW);
        digitalWrite(pinLed->rssi_7, LOW);
        digitalWrite(pinLed->rssi_8, LOW);
    }
    else if (rssi > -110)
    {
        digitalWrite(pinLed->rssi_1, HIGH);
        digitalWrite(pinLed->rssi_2, LOW);
        digitalWrite(pinLed->rssi_3, LOW);
        digitalWrite(pinLed->rssi_4, LOW);
        digitalWrite(pinLed->rssi_5, LOW);
        digitalWrite(pinLed->rssi_6, LOW);
        digitalWrite(pinLed->rssi_7, LOW);
        digitalWrite(pinLed->rssi_8, LOW);
    }
    else if (rssi <= -110)
    {
        digitalWrite(pinLed->rssi_1, LOW);
        digitalWrite(pinLed->rssi_2, LOW);
        digitalWrite(pinLed->rssi_3, LOW);
        digitalWrite(pinLed->rssi_4, LOW);
        digitalWrite(pinLed->rssi_5, LOW);
        digitalWrite(pinLed->rssi_6, LOW);
        digitalWrite(pinLed->rssi_7, LOW);
        digitalWrite(pinLed->rssi_8, LOW);
    }
}

void displayUpdate(uint8_t address, dataStruct *dataVariables)
{
}

void buttonCheck(buttonStruct pinButton)
{
}

void controlBoxCheck(uint8_t pin1, uint8_t pin2)
{
}

void ledStruct::pinMode()
{
    ::pinMode(R, OUTPUT);
    digitalWrite(R, LOW);
    ::pinMode(G, OUTPUT);
    digitalWrite(G, LOW);
    ::pinMode(B, OUTPUT);
    digitalWrite(B, LOW);

    ::pinMode(D1, OUTPUT);
    ::digitalWrite(D1, LOW);
    ::pinMode(D2, OUTPUT);
    ::digitalWrite(D2, LOW);
    ::pinMode(D3, OUTPUT);
    ::digitalWrite(D3, LOW);

    ::pinMode(rssi_1, OUTPUT);
    ::digitalWrite(rssi_2, LOW);
    ::pinMode(rssi_2, OUTPUT);
    ::digitalWrite(rssi_2, LOW);
    ::pinMode(rssi_3, OUTPUT);
    ::digitalWrite(rssi_3, LOW);
    ::pinMode(rssi_4, OUTPUT);
    ::digitalWrite(rssi_4, LOW);
    ::pinMode(rssi_5, OUTPUT);
    ::digitalWrite(rssi_5, LOW);
    ::pinMode(rssi_6, OUTPUT);
    ::digitalWrite(rssi_6, LOW);
    ::pinMode(rssi_7, OUTPUT);
    ::digitalWrite(rssi_7, LOW);
    ::pinMode(rssi_8, OUTPUT);
    ::digitalWrite(rssi_8, LOW);
}

void buttonStruct::pinMode()
{
    ::pinMode(sw1, INPUT);
    ::digitalWrite(sw2, LOW);
    ::pinMode(sw2, INPUT);
    ::digitalWrite(sw2, LOW);
    ::pinMode(sw3, INPUT);
    ::digitalWrite(sw3, LOW);
    ::pinMode(sw4, INPUT);
    ::digitalWrite(sw4, LOW);
    ::pinMode(sw5, INPUT);
    ::digitalWrite(sw5, LOW);
    ::pinMode(sw6, INPUT);
    ::digitalWrite(sw6, LOW);
}