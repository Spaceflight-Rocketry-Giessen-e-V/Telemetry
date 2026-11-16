

# Class Component



[**ClassList**](annotated.md) **>** [**Component**](classComponent.md)





* `#include <baseClasses.h>`





Inherited by the following classes: [char\_Component](classchar__Component.md),  [cobs\_Component](classcobs__Component.md),  [const\_Component](classconst__Component.md),  [empty\_Component](classempty__Component.md),  [float\_Component](classfloat__Component.md),  [parity\_Component](classparity__Component.md),  [uint8\_t\_Component](classuint8__t__Component.md)
















## Public Attributes

| Type | Name |
| ---: | :--- |
|  uint8\_t | [**bitPosition**](#variable-bitposition)  <br> |
|  [**Packet**](classPacket.md) \* | [**packet**](#variable-packet)  <br> |
|  uint8\_t | [**priority**](#variable-priority)  <br> |
|  uint8\_t | [**size**](#variable-size)  <br> |
















## Public Functions

| Type | Name |
| ---: | :--- |
|   | [**Component**](#function-component) (uint8\_t size, const uint8\_t priority=0) <br> |
| virtual uint8\_t | [**decode**](#function-decode) (uint8\_t \* packet) = 0<br> |
| virtual void | [**encode**](#function-encode) (uint8\_t \* packet) = 0<br> |
























## Protected Functions

| Type | Name |
| ---: | :--- |
|  void | [**bitReader**](#function-bitreader) (uint32\_t \* dataBits, uint8\_t \* packet) const<br> |
|  void | [**bitReset**](#function-bitreset) (uint8\_t \* packet) const<br> |
|  void | [**bitWriter**](#function-bitwriter) (uint32\_t dataBits, uint8\_t \* packet) const<br> |




## Public Attributes Documentation




### variable bitPosition 

```C++
uint8_t Component::bitPosition;
```




<hr>



### variable packet 

```C++
Packet* Component::packet;
```




<hr>



### variable priority 

```C++
uint8_t Component::priority;
```




<hr>



### variable size 

```C++
uint8_t Component::size;
```




<hr>
## Public Functions Documentation




### function Component 

```C++
Component::Component (
    uint8_t size,
    const uint8_t priority=0
) 
```




<hr>



### function decode 

```C++
virtual uint8_t Component::decode (
    uint8_t * packet
) = 0
```




<hr>



### function encode 

```C++
virtual void Component::encode (
    uint8_t * packet
) = 0
```




<hr>
## Protected Functions Documentation




### function bitReader 

```C++
void Component::bitReader (
    uint32_t * dataBits,
    uint8_t * packet
) const
```




<hr>



### function bitReset 

```C++
void Component::bitReset (
    uint8_t * packet
) const
```




<hr>



### function bitWriter 

```C++
void Component::bitWriter (
    uint32_t dataBits,
    uint8_t * packet
) const
```




<hr>

------------------------------
The documentation for this class was generated from the following file `libraries/DynamicPacketCodec/include/baseClasses.h`

