#include "Arduino.h"
#include "utility.h"
#include "Radiocrafts_RC17xxHP_RC232.h"
#include "Packet.h"

static uint8_t radioModuleConfigure(RC17xxHP_RC232 *radioModule)
{
    radioModule->resetHard(); // initial reboot to clear settings
    radioModule->begin();
    if (radioModule->ping() != 0) // confirm response
    {
        return 1;
    }
    if (radioModule->set_RF_DATA_RATE(0x05) != 0) // over-the-air data rate index
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
void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct pinLed, uint8_t pinBuzzer)
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
    uint8_t command = radioModule->read();

    // availability
    if (radioModule->available() == 0)
    {
        return 0;
    }

    // parity check
    uint8_t count = 0;
    for (int z = 0; z < 8; z++)
    {
        if (command & (1 << z))
        {
            count++;
        }
    }
    if (count % 2 == 0)
    {
        command &= 0x7F;
    }

    // normalise
    if (command >= 'A' && command <= 'Z')
    {
        command += 'a' - 'A';
    }

    // command parsing
    return command;
}

uint8_t packetSendCheck(uint8_t *flightmode, uint8_t loopFrequency, uint8_t timeBetweenStandbyPackets, uint16_t loopCount)
{
    static uint16_t loopCountWhenFlightmodeStarts = 0;
    static uint8_t lastValueOfFlightmode = 0;

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

        if (loopCount % (uint16_t)timeBetweenStandbyPackets * loopFrequency == 0)
        {

            return (loopCount % 2) + 1;
        }
        else
        {
            return 0;
        }
    }
}

void packetSend(RC17xxHP_RC232 *radioModule, dataStruct dataVariables, uint8_t packetIdentifier)
{
    if (packetIdentifier == 0)
    {
        return;
    }
    uint8_t packet[12] = {0};

    if (packetIdentifier == 1)
    {
        Packet::encodeFlightData(packet, dataVariables);
    }
    else if (packetIdentifier == 2)
    {
        Packet::encodeTelemetryData(packet, dataVariables);
    }
    radioModule->send(packet, 12);
}

void loopVariablesUpdate(uint16_t *loopCount, uint32_t *loopStartTime, uint8_t loopFrequency, uint8_t pinLedLoop)
{
    *loopCount = *loopCount + 1;

    if (*loopCount % 2 == 1)
        digitalWrite(pinLedLoop, HIGH);

    else
        digitalWrite(pinLedLoop, LOW);

    delay(1000 / loopFrequency - (millis() - *loopStartTime));
    *loopStartTime = millis();
}

void ledUpdate(uint8_t state, ledStruct &pinLed)
{
    switch (state)
    {
    case SETUPBEGIN:

        digitalWrite(pinLed.B, LOW);
        digitalWrite(pinLed.G, LOW);
        digitalWrite(pinLed.R, HIGH);

        break;

    case SETUPRADIOMODULS:

        digitalWrite(pinLed.R, LOW);
        digitalWrite(pinLed.G, LOW);
        digitalWrite(pinLed.B, HIGH);

        break;

    case SETUPEND:

        digitalWrite(pinLed.R, LOW);
        digitalWrite(pinLed.B, LOW);
        digitalWrite(pinLed.G, HIGH);

        break;

    case RADIOMODUL_ONE:

        digitalWrite(pinLed.D2, HIGH);

        break;

    case RADIOMODUL_TWO:

        digitalWrite(pinLed.D3, HIGH);

        break;

    default:

        break;
    }
}

void buzzerSound(uint8_t pinBuzzer)
{
    tone(pinBuzzer, 1260, 50);
}

void buzzerSoundError(uint8_t pinBuzzer)
{
    tone(pinBuzzer, 1400, 50);
    delay(20);
    tone(pinBuzzer, 1400, 50);
    delay(40);
    tone(pinBuzzer, 1400, 50);
    delay(20);
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
