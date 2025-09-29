/*
    RC1780HP - Library for using Radiocrafts RC1780HP-RC232 RF modules.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
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

    serialModule->begin(baud_module);
    _baud_module = baud_module;
}

// Public

uint8_t RC1780HP::ping()
{
    if(enter_Config() == 0)
    {
        if(exit_Config() == 0)
        {
            return 0;
        }
    }
    return 1;
}

uint8_t RC1780HP::hard_reset()
{
    digitalWrite(_rstpin, LOW);
    delayMicroseconds(1000);
    digitalWrite(_rstpin, HIGH);
    delayMicroseconds(2 * 3000);            // t_{RESET-IDLE} = 3.0 ms
    return 0;
}

uint8_t RC1780HP::soft_Reset()
{
    if(enter_Config() == 0)
    {
        digitalWrite(_cfgpin, LOW);
        serialModule->print("@RR");
        delayMicroseconds(6000);  // Nötige Wartezeit: Reaktionszeit vom Modul (t_{RESET-IDLE} = 3 ms), Pufferfaktor 2
        digitalWrite(_cfgpin, HIGH);
        delayMicroseconds(1000);
        serialModule->write('X');
        return 0;
    }
    return 1;
}

uint8_t RC1780HP::memory_Reset()
{
    if(enter_Config() == 0)
    {
        digitalWrite(_cfgpin, LOW);
        serialModule->print("@RC");
        serial_Wait(2 * (62000 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{MEMORY-CONFIG} = 62 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
        digitalWrite(_cfgpin, HIGH);
        if(serialModule->available() != 0)
        {
            if(serialModule->read() == '>')
            {
                if(exit_Config() == 0)
                {
                    return 0;
                }
                else
                    return 15;
            }
            else
                return 14;
        }
        else
            return 13;
    }
    else
        return 12;
    return 1;
}

// Set functions

uint8_t RC1780HP::set_RSSI_Mode(uint8_t value)
{
    return write_Memory_Byte(0x05, value);
}

uint8_t RC1780HP::set_Packet_Timeout(uint8_t value)
{
    return write_Memory_Byte(0x10, value);
}

uint8_t RC1780HP::set_Packet_End_Character(uint8_t value)
{
    return write_Memory_Byte(0x11, value);
}

uint8_t RC1780HP::set_Address_Mode(uint8_t value)
{
    return write_Memory_Byte(0x14, value);    
}

uint8_t RC1780HP::set_CRC_Mode(uint8_t value)
{
    return write_Memory_Byte(0x15, value);      
}

uint8_t RC1780HP::set_LED_Control(uint8_t value)
{
    return write_Memory_Byte(0x3A, value);      
}

// Read functions

uint8_t RC1780HP::read_RSSI_Mode(uint8_t* result)
{
    return read_Memory_Byte(0x05, result);
}

uint8_t RC1780HP::read_Packet_Timeout(uint8_t* result)
{
    return read_Memory_Byte(0x10, result);
}

uint8_t RC1780HP::read_Packet_End_Character(uint8_t* result)
{
    return read_Memory_Byte(0x11, result);
}

uint8_t RC1780HP::read_Address_Mode(uint8_t* result)
{
    return read_Memory_Byte(0x14, result);
}

uint8_t RC1780HP::read_CRC_Mode(uint8_t* result)
{
    return read_Memory_Byte(0x15, result);
}

uint8_t RC1780HP::read_LED_Control(uint8_t* result)
{
    return read_Memory_Byte(0x3A, result);
}

uint8_t RC1780HP::read_Voltage(float* result)
{
   if(enter_Config() == 0)
   {
        serialModule->write('V');
        serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C#-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
        if(serialModule->available() != 0)
        {
            *result = (float) serialModule->read() * 0.030;
            serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C#-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
            if(serialModule->available() != 0)
            {
                if(serialModule->read() == '>')
                {
                    if(exit_Config() == 0)
                    {
                        return 0;
                    }
                }
            }
        }
    }
    return 1;
}

uint8_t RC1780HP::read_Signal_Strength(float* result)
{
   if(enter_Config() == 0)
   {
        serialModule->write('S');
        serial_Wait(2 * (20000 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{RSSI} = 20 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
        if(serialModule->available() != 0)
        {
            *result = (float) - serialModule->read() / 2;
            serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C#-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
            if(serialModule->available() != 0)
            {
                if(serialModule->read() == '>')
                {
                    if(exit_Config() == 0)
                    {
                        return 0;
                    }
                }
            }
        }
    }
    return 1;
}

uint8_t RC1780HP::read_Temperature(int8_t* result)
{
   if(enter_Config() == 0)
   {
        serialModule->write('U');
        serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C#-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
        if(serialModule->available() != 0)
        {
            *result = serialModule->read() - 128;
            serial_Wait(2 * (1100 * 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C#-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
            if(serialModule->available() != 0)
            {
                if(serialModule->read() == '>')
                {
                    if(exit_Config() == 0)
                    {
                        return 0;
                    }
                }
            }
        }
    }
    return 1;
}

// Test modes

uint8_t RC1780HP::rf_Test_Mode(uint16_t time_millisecond)
{
  if( enter_Config() == 0)
  {
    if(send_Config_Command('2') == 0)
    {
        delay(time_millisecond);
        if(send_Config_Command('3') == 0)
        {
            if(exit_Config() == 0)
            {
                return 0;
            }
        }
    }
  }
  return 1;
}

// Private

uint16_t RC1780HP::serial_Wait(uint32_t delay_microsecond)
{
    for(uint32_t i = 0; i < (delay_microsecond / 10) && serialModule->available() == 0; i++)
    {
        delayMicroseconds(10);
    }
    return serialModule->available();
}

void RC1780HP::serial_Flush()
{
    while (serialModule->available())
    {
        serialModule->read();
    }
}

uint8_t RC1780HP::enter_Config()
{
    digitalWrite(_cfgpin, LOW);
    serial_Wait(2 * (590 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{CONFIG-PROMPT} = 590 us), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
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

uint8_t RC1780HP::send_Config_Command(uint8_t command)
{
    serialModule->write(command);
    serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
    if(serialModule->available() != 0)
    {
        if(serialModule->read() == '>')
        {
            return 0;
        }
    }
    return 1;
}

uint8_t RC1780HP::exit_Config()
{
    serialModule->write('X');
    serial_Wait(2 * (1420 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{CONFIG-IDLE} = 1420 us), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
    if(serialModule->available() == 0)
    {
        return 0;
    }
    return 1;
}

uint8_t RC1780HP::read_Memory_Byte(uint8_t address, uint8_t* result)
{
    if(enter_Config() == 0)
    {
        if(send_Config_Command('Y') == 0)
        {
            serialModule->write(address);
            serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
            if(serialModule->available() != 0)
            {
                *result = serialModule->read();
                serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{C-CONFIG} = 1.1 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
                if(serialModule->available() != 0)
                {
                    if(serialModule->read() == '>')
                    {
                        if(exit_Config() == 0)
                        {
                            return 0;
                        }
                    }
                }
            }
        }
    }
    return 1;
}

uint8_t RC1780HP::write_Memory_Byte(uint8_t memory_address, uint8_t value)
{
    if(enter_Config() == 0)
    {
        if(send_Config_Command('M') == 0)
        {
            serialModule->write(memory_address);
            delayMicroseconds(1000);
            serialModule->write(value);
            delayMicroseconds(1000);
            serialModule->write(0xFF);
            serial_Wait(2 * (62000 + 8 * 1000000 / _baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{MEMORY-CONFIG} = 62 ms), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
            if(serialModule->available() != 0)
            {
                if(serialModule->read() == '>')
                {
                    if(exit_Config() == 0)
                    {
                        return 0;
                    }
                }
            }
        }
    }
    return 1;
}
