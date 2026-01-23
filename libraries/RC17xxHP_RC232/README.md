# Telemetry Packet Library

A library for configuring and using Radiocrafts RC17xxHP-RC232 radio modules.

## Features

- Configure the non-volatile memory
- Soft and hard reset capability
- Read temperature, signal strength, supply voltage
- Easily adaptable for other RC232-series radio modules from Radiocrafts

## Limitations

- The configuration of the volatile memory is not included.
- The five test modes are not implemented
- The input and output of non-volatile memory parameters is handled with their binary values and not their real-world values. 
- Currently, there is no error handling implemented. Different error sources cannot be distinguished.

## Examples

- [radio module initialization](examples/initialization.cpp)
- [sending radio packets](examples/sending.cpp)

## Reference

### RC17xxHP_RC232()

- Initializes a RC17xxHP-RC232 object
- Function prototype: `public RC17xxHP_RC232(HardwareSerial* serialModule, uint8_t cfgpin, uint8_t rstpin, uint8_t ctspin, uint8_t rtspin)`
- Parameters:  
    - `HardwareSerial* serialModule`: serial port for the communication with the microcontroller
    - `uint8_t cfgpin`: IO pin of the microcontroller connected to the configuration pin of the radio module
    - `uint8_t rstpin`: IO pin of the microcontroller connected to the RST pin of the radio module
    - `uint8_t ctspin`: IO pin of the microcontroller connected to the CTS pin of the radio module
    - `uint8_t rtspin`: IO pin of the microcontroller connected to the RTS pin of the radio module
- Returns:
    - None
- Notes:
    - Multiple radio modules can be used simultaneously.
    - The pins don't have to be initializes before since this is done in the `begin()` function.
    - `rtspin` and `ctspin` are not used so far since flow control is not active.

### begin()

- Initializes the IO ports and the serial connection with the radio module
- Function prototype: `public void begin(uint32_t baud_module)`
- Parameters:  
    - `uint32_t baud_module`: baud rate for the serial connection
- Returns:
    - None
- Notes:
    - None

### serial_Flush()

- Empties the serial buffer coming from the radio module
- Function prototype: `public void serial_Flush()`
- Parameters:  
    - None
- Returns:
    - None
- Notes:
    - The data coming from the module is flushed. The internal buffer cannot be flushed.

### ping()

- Empties the serial buffer coming from the radio module
- Function prototype: `public uint8_t ping()`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### hard_Reset()

- Resets the radio module via the reset pin
- Function prototype: `public uint8_t hard_Reset()`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - There is no check if the operation was successful. The function always returns 0.
    
### soft_Reset()

- Resets the radio module via a configuration command
- Function prototype: `public uint8_t soft_Reset();`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### memory_Reset()

- Resets the non-volatile memory to the factory default
- Function prototype: `public uint8_t memory_Reset();`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### set_CONFIGURATION_PARAMETER()

- Wrappers for setting non-volatile memory parameters.
- Function prototype: `public uint8_t set_CONFIGURATION_PARAMETER(uint8_t value);`
- Parameters:  
    - `uint8_t value`: the parameter is set to this value.
- Returns:
    - 0 if successful, else 1
- Notes:
    - The function first checks, whether the correct value is already set.
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.
    - The names of the parameters (`CONFIGURATION_PARAMETER`) are listed in the [Radiocrafts RC232 User Manual](https://radiocrafts.com/uploads/RC232_user_manual.pdf).

### get_CONFIGURATION_PARAMETER()

- Wrappers for reading non-volatile memory parameters.
- Function prototype: `public uint8_t read_CONFIGURATION_PARAMETER(uint8_t* result);`
- Parameters:  
    - `uint8_t* result`: the parameter reading is stored in this variable.
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.
    - The names of the parameters (`CONFIGURATION_PARAMETER`) are listed in the [Radiocrafts RC232 User Manual](https://radiocrafts.com/uploads/RC232_user_manual.pdf).

### read_RSSI()

- Reads the current signal strength (rssi)
- Function prototype: `public uint8_t read_Signal_Strength(float* result)`
- Parameters:  
    - `float* result`: rssi in dB
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### read_TEMPERATURE()

- Reads the current module temperature
- Function prototype: `public uint8_t read_Temperature(int8_t* result)`
- Parameters:  
    - `uint8_t* result`: temperature in Deg. C
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### read_VOLTAGE()

- Reads the current supply voltage (output of the internal voltage regulator)
- Function prototype: `public uint8_t read_Voltage(float* result)`
- Parameters:  
    - `float* result`: voltage in volts
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### serial_Wait()

- Waits for serial data from the modul in a given time
- Function prototype: `private uint16_t serial_Wait(uint32_t delay_microsecond)`
- Parameters:  
    - `uint32_t delay_microsecond`: maximum waiting time in microseconds
- Returns:
    - Number of bytes in the serial buffer
- Notes:
    - If serial data arrives before the time runs out, the remaining time is skipped.

### enter_Config()

- Enters the modules configuration mode
- Function prototype: `private uint8_t enter_Config()`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### exit_Config()

- Exits the modules configuration mode
- Function prototype: `private uint8_t exit_Config()`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### send_Config_Command()

- Sends a configuration command and waits for the proper response
- Function prototype: `private uint8_t send_Config_Command(uint8_t command);`
- Parameters:  
    - `uint8_t command`: The command to be send
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### read_Memory_Byte()

- Reads one byte of the non-volatile memory
- Function prototype: `private uint8_t read_Memory_Byte(uint8_t address, uint8_t* result);`
- Parameters:  
    - `uint8_t address`: Address of the byte to be read.
    - `uint8_t* result`: Variable in which the result is stored in.
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.
    - This is the base function for the read_CONFIGURATION_PARAMETER() wrappers.

### write_Memory_Byte()

- Sets one byte of the non-volatile memory
- Function prototype: `private uint8_t write_Memory_Byte(uint8_t memory_address, uint8_t value)`
- Parameters:  
    - `uint8_t address`: Address of the byte to be set.
    - `uint8_t value`: Value to be set.
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.
    - This is the base function for the set_CONFIGURATION_PARAMETER() wrappers.

## Contributing

The same contribution guideline as for the parent project applies. Read more under [github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/CONTRIBUTING.md).

## License

The same license as for the parent project applies. Read more under [github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/LICENSE).