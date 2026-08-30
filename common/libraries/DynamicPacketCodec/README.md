# Dynamic Packet Codec Library

A library for dynamically encoding and decoding data packets and handling the packet framing.

- [Features](#features)
- [Limitations](#limitations)
- [Examples](#examples)
- [Documentation](#documentation)
    - [General Usage](#general-usage)
    - [Component Priorities](#component-priorities)
    - [Implemented Data Components](#implemented-data-components)
    - [Implemented Frame Components](#implemented-frame-components)
    - [Creating Custom Components](#creating-custom-components)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- Encode data into a bit sequence
- Decode a bit sequence back to the original data
- Implementation of frame components like parity and COBS
- Easily customizable for different packet structures
- Simple addition of new data and frame components

## Limitations

- Memory intensive when using many components
- Not completely dynamic: the packet size has to be known in advance for certain frame components like COBS
- No detailed error handling is implemented so far

## Examples

- [Simple Packet Encoding/Decoding](examples/)

## Documentation

### General Usage

#### Including the library

Place the library in the `lib` folder of the PlatformIO project or include in folder in the `lib_deps` of the `platformio.ini` file.
```c
#include "DynamicPacketCodec.h";
```

#### Initializing a packet object

```c
Packet myPacket;
```

#### Adding an `uint8_t` component

```c
uint8_t myVariable = 5;
myPacket.addComponent(new uint8_t_component(&myVariable, 3, 0, 63));
```

#### Encoding the Packet

The components will be encoded in the order of their priorities.

```c
uint8_t *packetBufTX = myPacket.encode();
```

#### Transmitting & receiving the Packet

```c
// Transmitting
for (uint8_t i = 0; i < myPacket.getByteSize(); i++)
{
	Serial.write(packetBufTX[i]);
}

// Receiving
uint8_t packetBufRX[myPacket.getByteSize()] = {0};
for (uint8_t i = 0; i < myPacket.getByteSize(); i++)
{
	packetBufRX[i] = Serial.read();
}
```

#### Decoding the received bytes

The components will be decoded in the opposite order of their priorities. The according variables will be updated automatically.

```c
myPacket.decode(PacketBufRX);
```

### Component Priorities

All components possess default priorities. They can be altered if necessary. Components with other priorities can be easily implemented.

- `0`: All data components and constant/empty frame components
- `1`: Parity bit
- `127`: COBS, should be the last alteration before transmittion
- `255`: Custom priority for components which should not be altered by frame components. Examples:
    - Unique End Byte
    - Components which get appended during receiving (for example RSSI indication)

### Implemented Data Components

Data components represent some sort of data variable and don't interact with other components inside the packet. The respective variable is linked by a pointer so that the `encode()` and `decode()` functions can access and alter the values. Data components have a default priority of `0`, which means that they can be altered by frame components. The `decode()` function always returns `0` (success).

#### `uint8_t`

```c
uint8_t_Component(uint8_t* value, uint8_t size, const uint8_t min, const uint8_t max, const uint8_t priority = 0)
```

The `value` will be stretched to the `min`-`max`-interval.

#### `float`

```c
float_Component(float* value, uint8_t size, const float min, const float max, const uint8_t priority = 0)
```

The `value` will be stretched to the `min`-`max`-interval.

#### `char`

```c
char_Component(uint8_t* value, const uint8_t priority = 0)
```

Upper case letters will be altered to lower case letters. Letters will be encoded in the interval `1` to `'z'-'a'+1`. All other chars will be encoded as `0`.

### Implemented Frame Components

Frame components serve special purposes in the packet and might alter the data components or lower priority frame components.

#### `const`

```c
const_Component(uint32_t value, uint8_t size, const uint8_t priority = 0)
```

Constant bit sequence with up to 32 bits. The `decode()` function returns `0`, if the relevant bit sequence matches the `value`.

#### `empty`

```c
empty_Component(uint8_t size, const uint8_t priority = 0)
```

Constant bit sequence with up to 32 zero bits. The `decode()` function returns `0`, if the relevant bit sequence is zero.

#### `parity`

```c
parity_Component(const uint8_t priority = 1)
```

Parity bit to ensure even parity. The `decode()` function returns `0`, if the parity is even.

#### `cobs`

```c
cobs_Component(uint8_t markerByte, uint8_t size, const uint8_t priority = 127)
```

Ensures no unwanted occurances of the `markerByte` in the encoded byte sequence. The `size` has to be set according to the total packet size: `ceil(log2(byteSize))`. If a, for example constant, occurance of the `markerByte` should not be altered, a higher priority has to be chosen for it. The `decode()` function always returns `0` (success).

See the [Packet Structure Documentation](/docs/packet_structure.md) for a more detailed explanation of the COBS algorithm.

### Creating Custom Components

Please see the definitions of the already implemented components as examples.

The declarations of custom components should be included in the `dataComponents.h` or `frameComponents.h` files. The definitions should be included in the `dataComponents.cpp` or `frameComponents.cpp` files.

#### (1) Declaration of the class:
```c
class myComponent : public Component
{
public:
	myComponent(const uint8_t priority = 0);
	void encode(uint8_t* packet) override;
	uint8_t decode(uint8_t* packet) override;
protected:
};
```
`myComponent` is the name of the new component. In the constructor, all necessary variables can be passed as parameters. Under `protected`, any custom variables can be declared. The `encode()` and `decode` declarations should not be altered.

#### (2) Definition of the constructor:
```c
myComponent::myComponent(const uint8_t priority) : Component(size, priority)
{}
```
The `size` parameter of the `Component` constructor has to be set with a parameter of the `myComponent` constructor or as a const value. Inside the curly brackets, custom `protected` variables can be set.

#### (3) Definition of the `encode()` function:
```c
void myComponent::encode(uint8_t* packet)
{
	uint32_t dataBits = ;

	bitWriter(dataBits, packet);
}
```
The `dataBits` variable has to be set according to the desired encoding scheme.

#### (4) Definition of the `decode()` function:
```c
uint8_t myComponent::decode(uint8_t* packet)
{
	uint32_t dataBits = 0;
	bitReader(&dataBits, packet);

	return 0;
}
```
With the extracted `dataBits`, any operation can be done (for example the linked variable can be updated). In case of the decoding scheme failing (for example failed parity check), a nonzero value should be returned.

## Contributing

The same contribution guideline as for the parent project applies. Read more under [github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/CONTRIBUTING.md). 

Please use the `Firmware` label when creating an issue.

## License

The same license as for the parent project applies. Read more under [github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry](https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry/blob/main/LICENSE).