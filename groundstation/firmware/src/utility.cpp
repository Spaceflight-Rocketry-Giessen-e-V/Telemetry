#include "utility.h"

static uint8_t radioModuleConfigure(RC17xxHP_RC232 *radioModule)
{
    radioModule->begin();
    radioModule->resetHard(); // initial reboot to clear setting
    while (radioModule->ping() != 0) // confirm response
    {
        return 1;
    }
    if (radioModule->set_RF_DATA_RATE(0x05) != 0) // radio data rate
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
void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct pinLed)
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
    ::pinMode(sw1, OUTPUT);
    ::digitalWrite(sw2, LOW);
    ::pinMode(sw2, OUTPUT);
    ::digitalWrite(sw2, LOW);
    ::pinMode(sw3, OUTPUT);
    ::digitalWrite(sw3, LOW);
    ::pinMode(sw4, OUTPUT);
    ::digitalWrite(sw4, LOW);
    ::pinMode(sw5, OUTPUT);
    ::digitalWrite(sw5, LOW);
    ::pinMode(sw6, OUTPUT);
    ::digitalWrite(sw6, LOW);
}