/*
    RC17xxHP-RC232 - Library for using Radiocrafts RC17xxHP-RC232 RF modules.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Radiocrafts_RC17xxHP_RC232.h"

RC17xxHP_RC232::RC17xxHP_RC232(HardwareSerial *serial, uint8_t pinTX, uint8_t pinRX, uint32_t baudrate, uint8_t pinCFG, uint8_t pinRST, uint8_t pinCTS, uint8_t pinRTS) // Store the hardware serial settings and pin assignments
{
    _serial = serial;
    _pinTX = pinTX;
    _pinRX = pinRX;
    _baudrate = baudrate;
    _pinCFG = pinCFG;
    _pinRST = pinRST;
    _pinCTS = pinCTS;
    _pinRTS = pinRTS;
}

void RC17xxHP_RC232::begin()
{
    pinMode(_pinRST, OUTPUT); // Hardware reset pin (active LOW)
    pinMode(_pinCFG, OUTPUT); // Configuration mode pin
    pinMode(_pinCTS, INPUT);  // Handshake
    pinMode(_pinRTS, OUTPUT); // Handshake

    digitalWrite(_pinRST, HIGH); // No reset of hardware
    digitalWrite(_pinCFG, HIGH); // Normal mode (Not in config mode)
    digitalWrite(_pinRTS, HIGH); // Default to no transmission request

    delayMicroseconds(3200); // t_{OFF-IDLE} = 3.2 ms

    _serial->pins(_pinTX, _pinRX);
    _serial->begin(_baudrate);
}

uint8_t RC17xxHP_RC232::ping() // Requests a ping from the module to ensure it works
{
    if (configEnter() == 0)
    {
        if (configExit() == 0)
        {
            return 0; // Success
        }
    }
    return 1; // Failure
}

// Public

// Serial Functions

void RC17xxHP_RC232::flush() // Clears the module's _serial buffer
{
    while (_serial->available())
    {
        _serial->read();
    }
}

uint16_t RC17xxHP_RC232::serialWait(uint32_t delayMicroseconds) // Waits for incoming _serial data or until a timeout expires
{
    uint32_t time_start = micros();
    while (_serial->available() == 0 && (micros() - time_start) < delayMicroseconds)
    {
        ::delayMicroseconds(10);
    }
    return _serial->available();
}

void RC17xxHP_RC232::send(uint8_t *bytes, uint8_t length)
{
    _serial->write(bytes, length);
}

void RC17xxHP_RC232::send(uint8_t byte)
{
    _serial->write(byte);
}

void RC17xxHP_RC232::read(uint8_t *bytes, uint8_t length)
{
    for (uint8_t i = 0; i < length; i++)
    {
        bytes[i] = _serial->read();
    }
}

uint8_t RC17xxHP_RC232::read()
{
    return _serial->read();
}

uint8_t RC17xxHP_RC232::available()
{
    return _serial->available();
}

// Resets

uint8_t RC17xxHP_RC232::resetHard() // Performs a reset of the hardware
{
    digitalWrite(_pinRST, LOW); // Pulling the reset pin to LOW (Resets module)
    delayMicroseconds(1000);
    digitalWrite(_pinRST, HIGH); // Puts reset pin on HIGH again, to enable to continue
    delayMicroseconds(4 * 3000); // t_{RESET-IDLE} = 3.0 ms
    return 0;
}

uint8_t RC17xxHP_RC232::resetSoft() // Performs a reset of the software (configurations stay the same)
{
    if (configEnter() == 0)
    {
        digitalWrite(_pinCFG, LOW);  // Ensure the module stays in CONFIG mode
        _serial->print("@RR");       // Soft reset command sequence
        delayMicroseconds(6000);     // Time module needs to respond (t_{RESET-IDLE} = 3 ms), bufferfaktor 2
        digitalWrite(_pinCFG, HIGH); // Return configuration pin to normal state
        delayMicroseconds(1000);
        _serial->write('X'); // Exit CONFIG mode
        return 0;
    }
    return 1;
}

uint8_t RC17xxHP_RC232::memoryReset() // Resets all the settings to the standarts configurations
{
    if (configEnter() == 0)
    {
        digitalWrite(_pinCFG, LOW);                        // Ensure the module stays in CONFIG mode
        _serial->print("@RC");                             // Factory reset command
        serialWait(4 * (62000 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{MEMORY-CONFIG} = 62 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
        digitalWrite(_pinCFG, HIGH);                       // Return configuration pin to normal state
        if (_serial->available() != 0)
        {
            if (_serial->read() == '>') // Confirm module completed reset
            {
                if (configExit() == 0)
                {
                    return 0; // Success
                }
            }
        }
    }
    return 1; // Failure
}

// Set functions

// All these functions use the memoryWrite function, just with different addresses.

uint8_t RC17xxHP_RC232::set_RF_CHANNEL(uint8_t value)
{
    uint8_t current_value;
    get_RF_CHANNEL(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x00, value);
    }
}

uint8_t RC17xxHP_RC232::set_RF_POWER(uint8_t value)
{
    uint8_t current_value;
    get_RF_POWER(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x01, value);
    }
}

uint8_t RC17xxHP_RC232::set_RF_DATA_RATE(uint8_t value)
{
    uint8_t current_value;
    get_RF_DATA_RATE(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x02, value);
    }
}

uint8_t RC17xxHP_RC232::set_SLEEP_MODE(uint8_t value)
{
    uint8_t current_value;
    get_SLEEP_MODE(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x04, value);
    }
}

uint8_t RC17xxHP_RC232::set_RSSI_MODE(uint8_t value)
{
    uint8_t current_value;
    get_RSSI_MODE(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x05, value);
    }
}

uint8_t RC17xxHP_RC232::set_PACKET_LENGTH(uint8_t value)
{
    uint8_t current_value;
    get_PACKET_LENGTH(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x0F, value);
    }
}

uint8_t RC17xxHP_RC232::set_PACKET_TIMEOUT(uint8_t value)
{
    uint8_t current_value;
    get_PACKET_TIMEOUT(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x10, value);
    }
}

uint8_t RC17xxHP_RC232::set_PACKET_END_CHARACTER(uint8_t value)
{
    uint8_t current_value;
    get_PACKET_END_CHARACTER(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x11, value);
    }
}

uint8_t RC17xxHP_RC232::set_ADDRESS_MODE(uint8_t value)
{
    uint8_t current_value;
    get_ADDRESS_MODE(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x14, value);
    }
}

uint8_t RC17xxHP_RC232::set_CRC_MODE(uint8_t value)
{
    uint8_t current_value;
    get_CRC_MODE(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x15, value);
    }
}

uint8_t RC17xxHP_RC232::set_UID(uint8_t value)
{
    uint8_t current_value;
    get_UID(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x19, value);
    }
}

uint8_t RC17xxHP_RC232::set_SID(uint8_t value)
{
    uint8_t current_value;
    get_SID(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x1A, value);
    }
}

uint8_t RC17xxHP_RC232::set_DID(uint8_t value)
{
    uint8_t current_value;
    get_DID(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x21, value);
    }
}

uint8_t RC17xxHP_RC232::set_BID(uint8_t value)
{
    uint8_t current_value;
    get_BID(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x28, value);
    }
}

uint8_t RC17xxHP_RC232::set_UART_BAUD_RATE(uint8_t value)
{
    uint8_t current_value;
    get_UART_BAUD_RATE(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x30, value);
    }
}

uint8_t RC17xxHP_RC232::set_UART_FLOW_CONTROL(uint8_t value)
{
    uint8_t current_value;
    get_UART_FLOW_CONTROL(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x35, value);
    }
}

uint8_t RC17xxHP_RC232::set_LED_CONTROL(uint8_t value)
{
    uint8_t current_value;
    get_LED_CONTROL(&current_value);
    if (current_value == value)
    {
        return 0;
    }
    else
    {
        return memoryWrite(0x3A, value);
    }
}

// Get functions

// All these functions use the memoryRead function, just with different addresses.

uint8_t RC17xxHP_RC232::get_RF_CHANNEL(uint8_t *result)
{
    return memoryRead(0x00, result);
}

uint8_t RC17xxHP_RC232::get_RF_POWER(uint8_t *result)
{
    return memoryRead(0x01, result);
}

uint8_t RC17xxHP_RC232::get_RF_DATA_RATE(uint8_t *result)
{
    return memoryRead(0x02, result);
}

uint8_t RC17xxHP_RC232::get_SLEEP_MODE(uint8_t *result)
{
    return memoryRead(0x04, result);
}

uint8_t RC17xxHP_RC232::get_RSSI_MODE(uint8_t *result)
{
    return memoryRead(0x05, result);
}

uint8_t RC17xxHP_RC232::get_PACKET_LENGTH(uint8_t *result)
{
    return memoryRead(0x0F, result);
}

uint8_t RC17xxHP_RC232::get_PACKET_TIMEOUT(uint8_t *result)
{
    return memoryRead(0x10, result);
}

uint8_t RC17xxHP_RC232::get_PACKET_END_CHARACTER(uint8_t *result)
{
    return memoryRead(0x11, result);
}

uint8_t RC17xxHP_RC232::get_ADDRESS_MODE(uint8_t *result)
{
    return memoryRead(0x14, result);
}

uint8_t RC17xxHP_RC232::get_CRC_MODE(uint8_t *result)
{
    return memoryRead(0x15, result);
}

uint8_t RC17xxHP_RC232::get_UID(uint8_t *result)
{
    return memoryRead(0x19, result);
}

uint8_t RC17xxHP_RC232::get_SID(uint8_t *result)
{
    return memoryRead(0x1A, result);
}

uint8_t RC17xxHP_RC232::get_DID(uint8_t *result)
{
    return memoryRead(0x21, result);
}

uint8_t RC17xxHP_RC232::get_BID(uint8_t *result)
{
    return memoryRead(0x28, result);
}

uint8_t RC17xxHP_RC232::get_UART_BAUD_RATE(uint8_t *result)
{
    return memoryRead(0x30, result);
}

uint8_t RC17xxHP_RC232::get_UART_FLOW_CONTROL(uint8_t *result)
{
    return memoryRead(0x35, result);
}

uint8_t RC17xxHP_RC232::get_LED_CONTROL(uint8_t *result)
{
    return memoryRead(0x3A, result);
}

// Read functions

// These functions do not read a memory address like the others. Instead, they enter CONFIG mode and send a specific UART command to request live measurements from the module (V = voltage, S = RSSI,
// U = temperature).

uint8_t RC17xxHP_RC232::read_RSSI(float *result)
{
    if (configEnter() == 0)
    {
        _serial->write('S');
        serialWait(4 * (20000 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{RSSI} = 20 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
        if (_serial->available() != 0)
        {
            *result = (float)-_serial->read() / 2;
            serialWait(4 * (1100 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if (_serial->available() != 0)
            {
                if (_serial->read() == '>')
                {
                    if (configExit() == 0)
                    {
                        return 0; // Success
                    }
                }
            }
        }
    }
    return 1; // Failure
}

uint8_t RC17xxHP_RC232::read_TEMPERATURE(int8_t *result)
{
    if (configEnter() == 0)
    {
        _serial->write('U');
        serialWait(4 * (1100 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
        if (_serial->available() != 0)
        {
            *result = _serial->read() - 128;
            serialWait(4 * (1100 * 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if (_serial->available() != 0)
            {
                if (_serial->read() == '>')
                {
                    if (configExit() == 0)
                    {
                        return 0; // Success
                    }
                }
            }
        }
    }
    return 1; // Failure
}

uint8_t RC17xxHP_RC232::read_VOLTAGE(float *result)
{
    if (configEnter() == 0)
    {
        _serial->write('V');
        serialWait(4 * (1100 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
        if (_serial->available() != 0)
        {
            *result = (float)_serial->read() * 0.030;
            serialWait(4 * (1100 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{C#-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if (_serial->available() != 0)
            {
                if (_serial->read() == '>')
                {
                    if (configExit() == 0)
                    {
                        return 0; // Success
                    }
                }
            }
        }
    }
    return 1; // Failure
}

// Test modes

// These modes are optional to test the module's functions

// uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_0(){}

// uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_1(){}

// uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_2(){}

// uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_3(){}

// uint8_t RC17xxHP_RC232::uint8_t TEST_MODE_4(){}

// Private

uint8_t RC17xxHP_RC232::configEnter() // Attempts to enter CONFIG mode on the module
{
    flush();
    digitalWrite(_pinCFG, LOW);
    serialWait(4 * (590 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{CONFIG-PROMPT} = 590 us), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
    digitalWrite(_pinCFG, HIGH);
    if (_serial->available() != 0)
    {
        if (_serial->read() == '>')
        {
            return 0; // Success
        }
    }
    return 1; // Failure
}

uint8_t RC17xxHP_RC232::configCommand(uint8_t command) // Sends a single-byte configuration command to the module
{
    _serial->write(command);
    serialWait(4 * (1100 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{C-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
    if (_serial->available() != 0)
    {
        if (_serial->read() == '>')
        {
            return 0; // Success
        }
    }
    return 1; // Failure
}

uint8_t RC17xxHP_RC232::configExit() // Attempts to exit CONFIG mode
{
    _serial->write('X');
    serialWait(4 * (1420 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{CONFIG-IDLE} = 1420 us), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
    if (_serial->available() == 0)
    {
        return 0; // Success
    }
    flush();
    return 1; // Failure
}

uint8_t RC17xxHP_RC232::memoryRead(uint8_t address, uint8_t *result) // Reads a single byte from the module's memory
{
    if (configEnter() == 0) // Successfully entered config mode
    {
        if (configCommand('Y') == 0) // Command to receive one Byte from memory
        {
            _serial->write(address);                          // Address of the category, of which the information is needed
            serialWait(4 * (1100 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{C-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if (_serial->available() != 0)
            {
                *result = _serial->read();                        // Read the Byte the module responded
                serialWait(4 * (1100 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{C-CONFIG} = 1.1 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
                if (_serial->available() != 0)                    // Leaving config mode
                {
                    if (_serial->read() == '>')
                    {
                        if (configExit() == 0)
                        {
                            return 0; // Success
                        }
                    }
                }
            }
        }
    }
    return 1; // Failure
}

uint8_t RC17xxHP_RC232::memoryWrite(uint8_t address, uint8_t value) // Writes a single byte to the module's memory
{
    if (configEnter() == 0) // Successfully entered config mode
    {
        if (configCommand('M') == 0) // Command to write one Byte in memory
        {
            _serial->write(address); // Address of the category chosen to set new configurations
            delayMicroseconds(1000);
            _serial->write(value); // Writing the new setting in the memory
            delayMicroseconds(1000);
            _serial->write(0xFF);                              // Signaling the end of the writing
            serialWait(4 * (62000 + 8 * 1000000 / _baudrate)); // Time module needs to respond (t_{MEMORY-CONFIG} = 62 ms), Transmission rate of a byte over UART: 8 / baud (in s!), bufferfaktor 2
            if (_serial->available() != 0)                     // Leaving config mode
            {
                if (_serial->read() == '>')
                {
                    if (configExit() == 0)
                    {
                        return 0; // Success
                    }
                }
            }
        }
    }
    return 1; // Failure
}
