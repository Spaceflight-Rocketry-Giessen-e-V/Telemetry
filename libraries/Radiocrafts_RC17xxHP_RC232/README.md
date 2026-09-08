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
- Flow Control is not implemented yet.

## Examples

- [radio module initialization](examples/initialization.cpp)
- [sending radio packets](examples/sending.cpp)

## Reference

### RC17xxHP_RC232()

- Initializes a RC17xxHP-RC232 object
- Function prototype: `public RC17xxHP_RC232(HardwareSerial *serial, uint8_t pinTX, uint8_t pinRX, uint32_t baudrate, uint8_t pinCFG, uint8_t pinRST, uint8_t pinCTS, uint8_t pinRTS)`
- Parameters:  
    - `HardwareSerial* serial`: serial port for the communication with the microcontroller
    - `uint8_t pinTX`: TX pin of the microcontroller for serial communication
    - `uint8_t pinRX`: RX pin of the microcontroller for serial communication
    - `uint32_t baudrate`: Baudrate for serial communication (`19200` if using default settings)
    - `uint8_t pinCFG`: IO pin of the microcontroller connected to the configuration pin of the radio module
    - `uint8_t pinRST`: IO pin of the microcontroller connected to the RST pin of the radio module
    - `uint8_t pinCTS`: IO pin of the microcontroller connected to the CTS pin of the radio module
    - `uint8_t pinRTS`: IO pin of the microcontroller connected to the RTS pin of the radio module
- Returns:
    - None
- Notes:
    - Multiple radio modules can be used simultaneously.
    - The pins don't have to be initialized before since this is done in the `begin()` function.
    - `pinRTS` and `pinCTS` are not used so far since flow control is not active.

### begin()

- Initializes the IO ports and the serial connection with the radio module
- Function prototype: `public void begin()`
- Parameters:  
    - None
- Returns:
    - None
- Notes:
    - None

### ping()

- Empties the serial buffer coming from the radio module
- Function prototype: `public uint8_t ping()`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### flush()

- Empties the serial buffer coming from the radio module
- Function prototype: `public void flush()`
- Parameters:  
    - None
- Returns:
    - None
- Notes:
    - The data coming from the module is flushed. The internal buffer cannot be flushed.

### serialWait()

- Waits for serial data from the modul in a given time
- Function prototype: `public uint16_t serialWait(uint32_t delayMicrosecond)`
- Parameters:  
    - `uint32_t delayMicrosecond`: maximum waiting time in microseconds
- Returns:
    - Number of bytes in the serial buffer
- Notes:
    - If serial data arrives before the time runs out, the remaining time is skipped.

### send()

- Send one or more bytes for transmission by the radio module
- Function prototypes: 
    - `public void send(uint8_t byte)`
    - `public void send(uint8_t *bytes, uint8_t length)`
- Parameters:  
    - `uint8_t byte`: single byte to be send
    - `uint8_t *bytes`: multiple bytes as array to be send
    - `uint8_t length`: length of `bytes` array
- Returns:
    - None
- Notes:
    - Wrapper of serial->write()

### read()

- Read one or more byte received by the radio module
- Function prototypes: 
    - `public uint8_t read()`
    - `public void rad(uint8_t *bytes, uint8_t length)`
- Parameters:  
    - `uint8_t *bytes`: array for byte readout
    - `uint8_t length`: amount of bytes to be read
- Returns:
    - Single byte readout: returns byte
    - Multiple bytes readout: None
- Notes:
    - Wrapper of serial->read()

### available()

- Read one or more byte received by the radio module
- Function prototype: `public uint8_t available()`
- Parameters:  
    - None
- Returns:
    - Amount of bytes available at the serial port
- Notes:
    - Wrapper of serial->available()

### resetHard()

- Resets the radio module via the reset pin
- Function prototype: `public uint8_t resetHard()`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - There is no check if the operation was successful. The function always returns 0.
    
### resetSoft()

- Resets the radio module via a configuration command
- Function prototype: `public uint8_t resetSoft();`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### memoryReset()

- Resets the non-volatile memory to the factory default
- Function prototype: `public uint8_t memoryReset();`
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
- Function prototype: `public uint8_t read_RSSI(float* result)`
- Parameters:  
    - `float* result`: rssi in dB
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### read_TEMPERATURE()

- Reads the current module temperature
- Function prototype: `public uint8_t read_TEMPERATURE(int8_t* result)`
- Parameters:  
    - `uint8_t* result`: temperature in Deg. C
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### read_VOLTAGE()

- Reads the current supply voltage (output of the internal voltage regulator)
- Function prototype: `public uint8_t read_VOLTAGE(float* result)`
- Parameters:  
    - `float* result`: voltage in volts
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### configEnter()

- Enters the modules configuration mode
- Function prototype: `private uint8_t configEnter()`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### configExit()

- Exits the modules configuration mode
- Function prototype: `private uint8_t configExit()`
- Parameters:  
    - None
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### configCommand()

- Sends a configuration command and waits for the proper response
- Function prototype: `private uint8_t configCommand(uint8_t command);`
- Parameters:  
    - `uint8_t command`: The command to be send
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.

### memoryRead()

- Reads one byte of the non-volatile memory
- Function prototype: `private uint8_t memoryRead(uint8_t address, uint8_t* result);`
- Parameters:  
    - `uint8_t address`: Address of the byte to be read.
    - `uint8_t* result`: Variable in which the result is stored in.
- Returns:
    - 0 if successful, else 1
- Notes:
    - Currently, there is no error handling implemented. Different error sources cannot be distinguished.
    - This is the base function for the read_CONFIGURATION_PARAMETER() wrappers.

### memoryWrite()

- Sets one byte of the non-volatile memory
- Function prototype: `private uint8_t memoryWrite(uint8_t address, uint8_t value)`
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