# Telemetry Packet Library

A lightweight library for encoding and decoding data packets according to our [data packet structure](../../../docs/packet_structure.md).

## Features

- Encode raw data into the packet structure
- Decode packets back to the original data
- Customizable for different packet structures while keeping a similar interface

## Reference

### encode()

- Converts raw data into the packet structure
- Function prototype: `void encode(uint8_t* packet, float temperature, uint8_t subsystem_status, uint8_t flight_mode, uint8_t low_power_mode, uint8_t status_events, float acceleration, float height_pressure, float height_gnss, float lat_gnss, float lon_gnss, float battery_voltage)`
- Parameters:  
    - `uint8_t* packet`: byte array in which the encoded data is stored. 
    - The other parameters correspond to the raw data components.
- Returns:
    - This function doesn't return any values. The data packet is stored in the passed byte array.
- Notes:
    - The passed byte array should be of the same size as the data packet or bigger.

### decode()

- Converts a data packet back into the raw data components
- Function prototype: `void decode(uint8_t* packet, uint8_t* temperature, uint8_t* subsystem_status, uint8_t* flight_mode, uint8_t* low_power_mode, uint8_t* status_events, float* acceleration, float* height_pressure, float* height_gnss, float* lat_gnss, float* lon_gnss, float* battery_voltage, float* rssi)`
- Parameters:  
    - `uint8_t* packet`: byte array with the data packet to be encoded.
    - The other parameters correspond to the raw data components.
- Returns:
    - This function doesn't return any values. The data components are stored in the respective passed variables.
- Notes:
    - The received signal strength (rssi) is appended after receiving a telemetry packet and is thus part of decode() but not encode().
    - All variables have to be passed as pointers.

## Limitations

- When raw data values exceed their maximum or fall below their minimum value, the maximum/minimum value is used respectively.
- The COBS algorithm could be adapted for a 16 byte packet when using 0xFF as the unique end byte. When opting to use even bigger packets, more bits must be allocated to the COBS data component  

## Examples

- [encode()](examples/encode.cpp)
- [decode()](examples/decode.cpp)
- [encoding and decoding of an example data packet](examples/encode.cpp)

## Contributing

The same contribution guideline as for the parent project applies. Read more under [github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/CONTRIBUTING.md).

## License

The same license as for the parent project applies. Read more under [github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/LICENSE).