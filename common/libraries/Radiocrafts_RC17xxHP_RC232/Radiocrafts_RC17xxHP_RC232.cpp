/*
    RC17xxHP-RC232 - Library for using Radiocrafts RC17xxHP-RC232 RF modules.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Arduino.h"
#include "Radiocrafts_RC17xxHP_RC232.h"

RC17xxHP_RC232::RC17xxHP_RC232(HardwareSerial* serialModule, uint8_t cfgpin, uint8_t rstpin, uint8_t ctspin, uint8_t rtspin)  // Store the hardware serial interface and pin assignments
{  
    this->serialModule = serialModule;
    _cfgpin = cfgpin;
    _rstpin = rstpin;
    _ctspin = ctspin;
    _rtspin = rtspin;
}

void send(uint8_t* packet, uint8_t length) //Hinzugefügt
        {
            serialModule->write(packet, length);
        }

void RC17xxHP_RC232::begin(uint32_t baud_module)
{
    pinMode(_rstpin, OUTPUT);   // Hardware reset pin (active LOW)
    pinMode(_ctspin, INPUT);    // Status pin 
    pinMode(_cfgpin, OUTPUT);   // Configuration mode pin
    pinMode(_rtspin, OUTPUT);   // Transmission control pin

    digitalWrite(_rstpin, HIGH); // No reset of hardware
    digitalWrite(_cfgpin, HIGH); // Normal mode (Not in config mode)
    digitalWrite(_rtspin, HIGH); // Default to no transmission request

    delayMicroseconds(3200);                // t_{OFF-IDLE} = 3.2 ms

    serialModule->begin(baud_module);
    _baud_module = baud_module;
}

// Public

uint8_t RC17xxHP_RC232::ping() // Requests a ping from the module to ensure it works
{
    if(enter_Config() == 0)
    {
        if(exit_Config() == 0)
        {
            return 0; // Success 
        }
    }
    return 1;         // Failure
}

//Resets

uint8_t RC17xxHP_RC232::hard_Reset() // Performs a reset of the hardware
{
    digitalWrite(_rstpin, LOW);     // Pulling the reset pin to LOW (Resets module)
    delayMicroseconds(1000); 
    digitalWrite(_rstpin, HIGH);    // Puts reset pin on HIGH again, to enable to continue 
    delayMicroseconds(2 * 3000);    // t_{RESET-IDLE} = 3.0 ms
    return 0;
}

uint8_t RC17xxHP_RC232::soft_Reset() // Performs a reset of the software (configurations stay the same)
{
    if(enter_Config() == 0)
    {
        digitalWrite(_cfgpin, LOW);     // Ensure the module stays in CONFIG mode
        serialModule->print("@RR");     // Soft reset command sequence
        delayMicroseconds(6000);        // Time module needs to respond (t_{RESET-IDLE} = 3 ms), bufferfaktor 2
        digitalWrite(_cfgpin, HIGH);    // Return configuration pin to normal state
        delayMicroseconds(1000);
        serialModule->write('X');       // Exit CONFIG mode
        return 0;
    }
    return 1;
}

uint8_t RC17xxHP_RC232::memory_Reset() //Resets all the settings to the standarts configurations
{
    if(enter_Config() == 0)
    {
        digitalWrite(_cfgpin, LOW);                            // Ensure the module stays in CONFIG mode
        serialModule->print("@RC");                            // Factory reset command
        serial_Wait(2 * (62000 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{MEMORY-CONFIG} = 62 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
        digitalWrite(_cfgpin, HIGH);                           // Return configuration pin to normal state
        if(serialModule->available() != 0)
        {
            if(serialModule->read() == '>')                    // Confirm module completed reset
            {
                if(exit_Config() == 0)
                {
                    return 0; // Success
                }
            }
        }
    }
    return 1;                 // Failure
}

// Set functions

// All these functions use the write_Memory_Byte function, just with different addresses.

uint8_t RC17xxHP_RC232::set_RF_CHANNEL(uint8_t value)
{
    uint8_t current_value;
    get_RF_CHANNEL(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x00, value);
    }
}

uint8_t RC17xxHP_RC232::set_RF_POWER(uint8_t value)
{
    uint8_t current_value;
    get_RF_POWER(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x01, value);
    }
}

uint8_t RC17xxHP_RC232::set_RF_DATA_RATE(uint8_t value)
{
    uint8_t current_value;
    get_RF_DATA_RATE(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x02, value);
    }
}

uint8_t RC17xxHP_RC232::set_SLEEP_MODE(uint8_t value)
{
    uint8_t current_value;
    get_SLEEP_MODE(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x04, value);
    }
}

uint8_t RC17xxHP_RC232::set_RSSI_MODE(uint8_t value)
{
    uint8_t current_value;
    get_RSSI_MODE(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x05, value);
    }
}

uint8_t RC17xxHP_RC232::set_PACKET_LENGTH(uint8_t value)
{
    uint8_t current_value;
    get_PACKET_LENGTH(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x0F, value);
    }
}

uint8_t RC17xxHP_RC232::set_PACKET_TIMEOUT(uint8_t value)
{
    uint8_t current_value;
    get_PACKET_TIMEOUT(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x10, value);
    }
}

uint8_t RC17xxHP_RC232::set_PACKET_END_CHARACTER(uint8_t value)
{
    uint8_t current_value;
    get_PACKET_END_CHARACTER(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x11, value);
    }
}

uint8_t RC17xxHP_RC232::set_ADDRESS_MODE(uint8_t value)
{
    uint8_t current_value;
    get_ADDRESS_MODE(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x14, value);
    }
}

uint8_t RC17xxHP_RC232::set_CRC_MODE(uint8_t value)
{
    uint8_t current_value;
    get_CRC_MODE(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x15, value);
    }
}

uint8_t RC17xxHP_RC232::set_UID(uint8_t value)
{
    uint8_t current_value;
    get_UID(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x19, value);
    }
}

uint8_t RC17xxHP_RC232::set_SID(uint8_t value)
{
    uint8_t current_value;
    get_SID(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x1A, value);
    }
}

uint8_t RC17xxHP_RC232::set_DID(uint8_t value)
{
    uint8_t current_value;
    get_DID(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x21, value);
    }
}

uint8_t RC17xxHP_RC232::set_BID(uint8_t value)
{
    uint8_t current_value;
    get_BID(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x28, value);
    }
}

uint8_t RC17xxHP_RC232::set_UART_BAUD_RATE(uint8_t value)
{
    uint8_t current_value;
    get_UART_BAUD_RATE(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x30, value);
    }
}

uint8_t RC17xxHP_RC232::set_UART_FLOW_CONTROL(uint8_t value)
{
    uint8_t current_value;
    get_UART_FLOW_CONTROL(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x35, value);
    }
}

uint8_t RC17xxHP_RC232::set_LED_CONTROL(uint8_t value)
{
    uint8_t current_value;
    get_LED_CONTROL(&current_value);
    if(current_value == value)
    {
        return 0;
    }
    else
    {
        return write_Memory_Byte(0x3A, value);
    }
}

// Get functions

// All these functions use the read_Memory_Byte function, just with different addresses.

uint8_t RC17xxHP_RC232::get_RF_CHANNEL(uint8_t* result)
{
    return read_Memory_Byte(0x00, result);
}

uint8_t RC17xxHP_RC232::get_RF_POWER(uint8_t* result)
{
    return read_Memory_Byte(0x01, result);
}

uint8_t RC17xxHP_RC232::get_RF_DATA_RATE(uint8_t* result)
{
    return read_Memory_Byte(0x02, result);
}

uint8_t RC17xxHP_RC232::get_SLEEP_MODE(uint8_t* result)
{
    return read_Memory_Byte(0x04, result);
}

uint8_t RC17xxHP_RC232::get_RSSI_MODE(uint8_t* result)
{
    return read_Memory_Byte(0x05, result);
}

uint8_t RC17xxHP_RC232::get_PACKET_LENGTH(uint8_t* result)
{
    return read_Memory_Byte(0x0F, result);
}

uint8_t RC17xxHP_RC232::get_PACKET_TIMEOUT(uint8_t* result)
{
    return read_Memory_Byte(0x10, result);
}

uint8_t RC17xxHP_RC232::get_PACKET_END_CHARACTER(uint8_t* result)
{
    return read_Memory_Byte(0x11, result);
}

uint8_t RC17xxHP_RC232::get_ADDRESS_MODE(uint8_t* result)
{
    return read_Memory_Byte(0x14, result);
}

uint8_t RC17xxHP_RC232::get_CRC_MODE(uint8_t* result)
{
    return read_Memory_Byte(0x15, result);
}

uint8_t RC17xxHP_RC232::get_UID(uint8_t* result)
{
    return read_Memory_Byte(0x19, result);
}

uint8_t RC17xxHP_RC232::get_SID(uint8_t* result)
{
    return read_Memory_Byte(0x1A, result);
}

uint8_t RC17xxHP_RC232::get_DID(uint8_t* result)
{
    return read_Memory_Byte(0x21, result);
}

uint8_t RC17xxHP_RC232::get_BID(uint8_t* result)
{
    return read_Memory_Byte(0x28, result);
}

uint8_t RC17xxHP_RC232::get_UART_BAUD_RATE(uint8_t* result)
{
    return read_Memory_Byte(0x30, result);
}

uint8_t RC17xxHP_RC232::get_UART_FLOW_CONTROL(uint8_t* result)
{
    return read_Memory_Byte(0x35, result);
}

uint8_t RC17xxHP_RC232::get_LED_CONTROL(uint8_t* result)
{
    return read_Memory_Byte(0x3A, result);
}

// Read functions

// These functions do not read a memory address like the others. Instead, they enter CONFIG mode and send a specific UART command to request live measurements from the module (V = voltage, S = RSSI,
// U = temperature).

uint8_t RC17xxHP_RC232::read_RSSI(float* result)
{
   if(enter_Config() == 0)
   {
        serialModule->write('S');
        serial_Wait(2 * (20000 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{RSSI} = 20 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
        if(serialModule->available() != 0)
        {
            *result = (float) - serialModule->read() / 2;
            serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if(serialModule->available() != 0)
            {
                if(serialModule->read() == '>')
                {
                    if(exit_Config() == 0)
                    {
                        return 0; // Success
                    }
                }
            }
        }
    }
    return 1;                     // Failure
}

uint8_t RC17xxHP_RC232::read_TEMPERATURE(int8_t* result)
{
   if(enter_Config() == 0)
   {
        serialModule->write('U');
        serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
        if(serialModule->available() != 0)
        {
            *result = serialModule->read() - 128;
            serial_Wait(2 * (1100 * 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if(serialModule->available() != 0)
            {
                if(serialModule->read() == '>')
                {
                    if(exit_Config() == 0)
                    {
                        return 0; // Success
                    }
                }
            }
        }
    }
    return 1;                     // Failure
}

uint8_t RC17xxHP_RC232::read_VOLTAGE(float* result)
{
   if(enter_Config() == 0)
   {
        serialModule->write('V');
        serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
        if(serialModule->available() != 0)
        {
            *result = (float) serialModule->read() * 0.030;
            serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if(serialModule->available() != 0)
            {
                if(serialModule->read() == '>')
                {
                    if(exit_Config() == 0)
                    {
                        return 0; // Success
                    }
                }
            }
        }
    }
    return 1;                     // Failure
}

// Test modes

// These modes are optional to test the module's functions

//uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_0(){}

//uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_1(){}

//uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_2(){}

//uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_3(){}

//uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_4(){}


// Private

uint16_t RC17xxHP_RC232::serial_Wait(uint32_t delay_microseconds) // Waits for incoming serial data or until a timeout expires
{
    uint32_t time_start = micros();
    while(serialModule->available() == 0 && (micros() - time_start) < delay_microseconds)
    {
        delayMicroseconds(10);
    }
    return serialModule->available();
}

void RC17xxHP_RC232::serial_Flush() // Clears the module's serial buffer
{
    while (serialModule->available())
    {
        serialModule->read();
    }
}

uint8_t RC17xxHP_RC232::enter_Config() // Attempts to enter CONFIG mode on the module
{
    digitalWrite(_cfgpin, LOW);
    serial_Wait(2 * (590 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{CONFIG-PROMPT} = 590 us), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
    digitalWrite(_cfgpin, HIGH);
    if(serialModule->available() != 0)
    {
        if(serialModule->read() == '>')
        {
            return 0; // Success
        }
    }
    return 1;         // Failure
}

uint8_t RC17xxHP_RC232::send_Config_Command(uint8_t command) // Sends a single-byte configuration command to the module
{
    serialModule->write(command);
    serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{C-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
    if(serialModule->available() != 0)
    {
        if(serialModule->read() == '>')
        {
            return 0; // Success
        }
    }
    return 1;         // Failure
}

uint8_t RC17xxHP_RC232::exit_Config() //Attempts to exit CONFIG mode
{
    serialModule->write('X');
    serial_Wait(2 * (1420 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{CONFIG-IDLE} = 1420 us), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
    if(serialModule->available() == 0)
    {
        return 0; //Success
    }
    serial_Flush();
    return 1;     //Failure
}

uint8_t RC17xxHP_RC232::read_Memory_Byte(uint8_t address, uint8_t* result) // Reads a single byte from the module's memory
{
    if(enter_Config() == 0) // Successfully entered config mode
    {
        if(send_Config_Command('Y') == 0) // Command to receive one Byte from memory
        {
            serialModule->write(address); // Address of the category, of which the information is needed
            serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{C-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if(serialModule->available() != 0)
            {
                *result = serialModule->read(); // Read the Byte the module responded
                serial_Wait(2 * (1100 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{C-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
                if(serialModule->available() != 0) // Leaving config mode
                {
                    if(serialModule->read() == '>') 
                    {
                        if(exit_Config() == 0)
                        {
                            return 0; // Success
                        }
                    }
                }
            }
        }
    }
    return 1;                         // Failure
}

uint8_t RC17xxHP_RC232::write_Memory_Byte(uint8_t memory_address, uint8_t value) // Writes a single byte to the module's memory
{
    if(enter_Config() == 0) // Successfully entered config mode
    {
        if(send_Config_Command('M') == 0) // Command to write one Byte in memory
        {
            serialModule->write(memory_address); // Address of the category chosen to set new configurations
            delayMicroseconds(1000);             
            serialModule->write(value); //Writing the new setting in the memory
            delayMicroseconds(1000);
            serialModule->write(0xFF); //Signaling the end of the writing
            serial_Wait(2 * (62000 + 8 * 1000000 / _baud_module)); // Time module needs to respond (t_{MEMORY-CONFIG} = 62 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if(serialModule->available() != 0) // Leaving config mode 
            {
                if(serialModule->read() == '>')
                {
                    if(exit_Config() == 0)
                    {
                        return 0; // Success
                    }
                }
            }
        }
    }
    return 1;                     // Failure
}
