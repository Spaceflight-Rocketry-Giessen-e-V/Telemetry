/*
    RC1780HP.h - Library for using Radiocrafts RC1780HP RF modules.
    Created by ..., xx.xx.2025.
    Spaceflight Rocketry Giessen e.V.
    Licence...
*/

#include "Arduino.h"
#include "RC1780HP.h"

RC1780HP::RC1780HP(HardwareSerial* serialModule, uint8_t cfgpin, uint8_t rstpin, uint8_t ctspin, uint8_t rtspin)
{  
    this->serialModule = serialModule;
    _cfgpin = cfgpin;
    _rstpin = rstpin;
    _ctspin = ctspin;
    _rtspin = rtspin;
}

void RC1780HP::begin(uint32_t baud_module)
{
    pinMode(_rstpin, OUTPUT);
    pinMode(_ctspin, INPUT);
    pinMode(_cfgpin, OUTPUT);
    pinMode(_rtspin, OUTPUT);

    digitalWrite(_rstpin, HIGH);
    digitalWrite(_cfgpin, HIGH);
    digitalWrite(_rtspin, HIGH);

    delayMicroseconds(3200);                // t_{OFF-IDLE} = 3.2 ms

    reset();

    // Auslesen der Standardeinstellungen des Non-Volatile Memory
    readMemoryByte(0x00, &_channel);
    readMemoryByte(0x01, &_output_power);
    readMemoryByte(0x21, &_destination_address);

    serialModule->begin(baud_module);
    _baud_module = baud_module;
}

void RC1780HP::reset()
{
    digitalWrite(_rstpin, LOW);
    delayMicroseconds(1000);
    digitalWrite(_rstpin, HIGH);
    delayMicroseconds(2 * 3000);            // t_{RESET-IDLE} = 3.0 ms
}

uint16_t RC1780HP::serialWait(uint32_t delay_microsecond)
{
    for(uint32_t i = 0; i < (delay_microsecond / 10) && serialModule->available() == 0; i++)
    {
        delayMicroseconds(10);
    }
    return serialModule->available();
}

void RC1780HP::serialFlush()
{
    while (serialModule->available())
    {
        serialModule->read();
    }
}

uint8_t RC1780HP::enterConfig()
{
    digitalWrite(_cfgpin, LOW);
    serialWait(2 * (590 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{CONFIG-PROMPT} = 590 us), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
    digitalWrite(_cfgpin, HIGH);
    if(serialModule->available() != 0)
    {
        if(serialModule->read() == '>')
        {
            return 0;
        }
    }
    return 1;
}

uint8_t RC1780HP::sendConfigCommand(uint8_t command)
{
    serialModule->write(command);
    serialWait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
    if(serialModule->available() != 0)
    {
        if(serialModule->read() == '>')
        {
            return 0;
        }
    }
    return 1;
}

uint8_t RC1780HP::exitConfig()
{
    serialModule->write('X');
    serialWait(2 * (1420 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{CONFIG-IDLE} = 1420 us), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
    if(serialModule->available() == 0)
    {
        return 0;
    }
    return 1;
}

uint8_t RC1780HP::readMemoryByte(uint8_t address, uint8_t* result)
{
    if(enterConfig() == 0)
    {
        if(sendConfigCommand('Y') == 0)
        {
            serialModule->write(address);
            serialWait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
            if(serialModule->available() != 0)
            {
                *result = serialModule->read();
                if(exitConfig() == 0)
                {
                    return 0;
                }
            }
        }
    }
    return 1;
}

uint8_t RC1780HP::setChannel(uint8_t channel)
{
    if(channel >= 1 && channel <= 84)
    {
        if(enterConfig() == 0)
        {
            if(sendConfigCommand('C') == 0)
            {
                if(sendConfigCommand(channel) == 0)
                {
                    _channel = channel;
                    if(exitConfig() == 0)
                    {
                        return 0;
                    }
                }
            }
        }
    }
    return 1;
}
