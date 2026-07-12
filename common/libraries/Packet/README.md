# Telemetry Packet Library

A lightweight library for encoding and decoding data packets according to our [data packet structure](../../../docs/packet_structure.md).

## Features

- Encode raw data into the packet structure
- Decode packets back to the original data
- Customizable for different packet structures while keeping a similar interface

## Limitations

- When raw data values exceed their maximum or fall below their minimum value, the maximum/minimum value is used respectively.
- The COBS algorithm could be adapted for a 16 byte packet when using 0xFF as the unique end byte. When opting to use even bigger packets, more bits must be allocated to the COBS data component  

## Examples

- [Encode Command](/examples/encodeCommand.cpp)
- [Decode Command](/examples/decodeCommand.cpp)
- [Encode Flight Data](/examples/encodeFlightData.cpp)
- [Decode Flight Data](/examples/decodeFlightData.cpp)
- [Encode Telemetry Data](/examples/encodeTelemetryData.cpp)
- [Decode Telemetry Data](/examples/decodeTelemetryData.cpp)

## Reference

### encodeFrame()

- Sets the packet identifier, end byte, COBS, parity bit

### decodeFrame()

- Reads the packet identifier, end byte, COBS, parity bit
- Returns 0 if successfull

### encodeFlightData()

- Encodes a flight data packet
- Packet identifier = 0

### decodeFlightData

- Decodes a flight data packet

### encodeTelemetryData()

- Encodes a telemetry data packet
- Packet identifier = 1

### decodeTelemetryData

- Decodes a flight data packet

### encodeCommand

- Encodes a command (convert to lower case letters, set parity)

### decodeCommand

- Decodes a command (convert to lower case letters, read parity)

## Contributing

The same contribution guideline as for the parent project applies. Read more under [github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/CONTRIBUTING.md).

## License

The same license as for the parent project applies. Read more under [github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/LICENSE).