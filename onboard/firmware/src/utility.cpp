#include "utility.h"

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
    if (radioModule->set_PACKET_TIMEOUT(0x00) != 0) // no inter-byte timeout trigger
    {
        return 1;
    }
    if (radioModule->set_PACKET_END_CHARACTER(0xEE) != 0) // 0xEE flushes the buffer over RF
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
void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct *pinLed, uint8_t pinBuzzer)
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
        buzzerSoundError(pinBuzzer);
        exit(1);
    }
}

// Returns the latest single-byte command from the uplink module (rc1701hp, on Serial3), or 0 if command is bad/unknown
uint8_t commandReceive(RC17xxHP_RC232 *radioModule)
{
    // availability
    if (radioModule->available() == 0)
    {
        return 0;
    }
    else
    {
        uint8_t command = radioModule->read();

        Packet::decodeCommand(command, &command);

        return command;
    }
}

void commandExecute(uint8_t command, RC17xxHP_RC232 *radioModule, dataStruct *dataVariables, uint8_t *lowPowerMode, uint8_t *flightMode, Subsystem **subsystemsList, uint8_t subsystemsCount, Subsystem *subsystemSens, Subsystem *subsystemControl, uint8_t pinArm, uint8_t pinSleep)
{
    switch (command)
    {
    case 0:
        break;

    case 'a': // Arming
        digitalWrite(pinArm, HIGH);
        for (uint8_t i = 0; i < subsystemsCount; i++)
        {
            subsystemsList[i]->write('a');
        }
        break;

    case 'b': // Dearming
        digitalWrite(pinArm, LOW);
        for (uint8_t i = 0; i < subsystemsCount; i++)
        {
            subsystemsList[i]->write('b');
        }
        break;

    case 'f': // Flight Mode Activation
        *flightMode = 1;
        break;

    case 'g': // Flight Mode Deactivation
        *flightMode = 0;
        break;

    case 'h': // Change Pressure Sensor
        subsystemSens->write('h');
        break;

    case 'i': // Change Acceleration Sensor
        subsystemSens->write('i');
        break;

    case 'j': // Change GNSS Sensor
        subsystemSens->write('j');
        break;

    case 'l': // Low Power Mode Activation
        *lowPowerMode = 1;
        digitalWrite(pinSleep, HIGH);
        break;

    case 'm': // Low Power Mode Deactivation
        *lowPowerMode = 0;
        digitalWrite(pinSleep, LOW);
        break;

    case 'p': // Ping
        packetSend(radioModule, dataVariables, 1);
        packetSend(radioModule, dataVariables, 2);
        break;

    case 'q': // Drogue Ejection
        subsystemControl->write('q');
        break;

    case 'r': // Main Ejection
        subsystemControl->write('r');
        break;

    case 's': // Decoupling
        subsystemControl->write('s');
        break;

    case 't': // Switch Main Parachute Ejection Height
        subsystemControl->write('t');
        break;

    case 'v': // Delete flash content (sensorics subsystem)
        subsystemSens->write('v');
        break;

    case 'w': // Enter flash write mode (sensorics subsystem)
        subsystemSens->write('w');
        break;

    default:
        break;
    }
}

void flashWrite(dataStruct *dataVariables)
{
}

uint8_t packetSendCheck(uint8_t *flightmode, uint8_t loopFrequency, uint8_t timeBetweenStandbyPackets, uint32_t loopCount)
{
    static uint16_t loopCountWhenFlightmodeStarts = 0;
    static uint8_t lastValueOfFlightmode = 0;
    static uint8_t lastPacketTypeStandby = 0;

    if (*flightmode == 1 && lastValueOfFlightmode == 0)
    {
        loopCountWhenFlightmodeStarts = loopCount;
    }
    lastValueOfFlightmode = *flightmode;

    if (*flightmode == 1)
    {

        if ((loopCount - loopCountWhenFlightmodeStarts) / loopFrequency >= 360 - 3600 / timeBetweenStandbyPackets / loopFrequency)
        {
            *flightmode = 0;
            return 0;
        }

        if (loopCount % 10 == 0)
        {
            return 2;
        }
        else
        {
            return 1;
        }
    }
    else
    {
        if ((loopCount % (uint16_t)(timeBetweenStandbyPackets * loopFrequency)) == 0)
        {
            lastPacketTypeStandby = 1 - lastPacketTypeStandby;
            return lastPacketTypeStandby;
        }
        else
        {
            return 0;
        }
    }
}

void packetSend(RC17xxHP_RC232 *radioModule, dataStruct *dataVariables, uint8_t packetIdentifier)
{
    if (packetIdentifier == 0)
    {
        return;
    }
    uint8_t packet[12] = {0};

    if (packetIdentifier == 1)
    {
        Packet::encodeFlightData(packet, dataVariables->acceleration, dataVariables->heightPressure, dataVariables->flightEvents, dataVariables->latitude, dataVariables->longitude);
    }
    else if (packetIdentifier == 2)
    {
        Packet::encodeTelemetryData(packet, dataVariables->stateTelemetry, dataVariables->statePower, dataVariables->stateSens, dataVariables->stateControl, dataVariables->heightGNSS, dataVariables->satCountGNSS, dataVariables->hdopGNSS, dataVariables->temperatureElectronics, dataVariables->temperatureBattery, dataVariables->stateCapacitors, dataVariables->continuityPyros, dataVariables->pressureDecoupler, dataVariables->ldrDecoupler, dataVariables->voltageBattery, dataVariables->currentBattery, dataVariables->currentUmbilical, dataVariables->stateUmbilical, dataVariables->lowPowerMode, dataVariables->voltageBatteryCOTS);
    }
    radioModule->send(packet, 12);
}

void loopVariablesUpdate(uint32_t *loopCount, uint32_t *loopStartTime, uint8_t loopFrequency, uint8_t pinLedLoop)
{
    *loopCount = *loopCount + 1;

    if (*loopCount % 2 == 1)
        digitalWrite(pinLedLoop, HIGH);
    else
        digitalWrite(pinLedLoop, LOW);

    if ((millis() - *loopStartTime) < 1000 / loopFrequency)
        delay(1000 / loopFrequency - (millis() - *loopStartTime));
    *loopStartTime = millis();
}

void ledUpdate(uint8_t state, ledStruct *pinLed)
{
    static uint8_t r = 0, g = 0, b = 0, d2 = 0, d3 = 0;

    switch (state)
    {
    case SETUPBEGIN:
        r = 1;
        g = 0;
        b = 0;
        break;
    case SETUPRADIOMODULS:
        r = 0;
        g = 0;
        b = 1;
        break;
    case SETUPEND:
        r = 0;
        g = 1;
        b = 0;
        break;
    case RADIOMODUL_ONE:
        d2 = 1;
        break;
    case RADIOMODUL_TWO:
        d3 = 1;
        break;
    default:
        break;
    }

    if (*pinLed->lowPowerMode == 1)
    {
        digitalWrite(pinLed->R, LOW);
        digitalWrite(pinLed->G, LOW);
        digitalWrite(pinLed->B, LOW);
        digitalWrite(pinLed->D2, LOW);
        digitalWrite(pinLed->D3, LOW);
        return;
    }

    digitalWrite(pinLed->R, r);
    digitalWrite(pinLed->G, g);
    digitalWrite(pinLed->B, b);
    digitalWrite(pinLed->D2, d2);
    digitalWrite(pinLed->D3, d3);
}

void buzzerSound(uint8_t pinBuzzer)
{
    tone(pinBuzzer, 1260, 50);
}

void buzzerSoundError(uint8_t pinBuzzer)
{
    tone(pinBuzzer, 1400, 50);
    delay(100);
    tone(pinBuzzer, 1400, 50);
    delay(200);
    tone(pinBuzzer, 1400, 50);
    delay(100);
    tone(pinBuzzer, 1400, 50);
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

    ::pinMode(Sens, OUTPUT);
    ::digitalWrite(Sens, LOW);
    ::pinMode(Power, OUTPUT);
    ::digitalWrite(Power, LOW);
    ::pinMode(Control, OUTPUT);
    ::digitalWrite(Control, LOW);

    ::pinMode(Debug1, OUTPUT);
    ::digitalWrite(Debug1, LOW);
    ::pinMode(Debug2, OUTPUT);
    ::digitalWrite(Debug2, LOW);
}
