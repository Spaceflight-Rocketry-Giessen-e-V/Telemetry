

# Class uint8\_t\_Component



[**ClassList**](annotated.md) **>** [**uint8\_t\_Component**](classuint8__t__Component.md)





* `#include <dataComponents.h>`



Inherits the following classes: [Component](classComponent.md)
























## Public Attributes inherited from Component

See [Component](classComponent.md)

| Type | Name |
| ---: | :--- |
|  uint8\_t | [**bitPosition**](classComponent.md#variable-bitposition)  <br> |
|  [**Packet**](classPacket.md) \* | [**packet**](classComponent.md#variable-packet)  <br> |
|  uint8\_t | [**priority**](classComponent.md#variable-priority)  <br> |
|  uint8\_t | [**size**](classComponent.md#variable-size)  <br> |






























## Public Functions

| Type | Name |
| ---: | :--- |
| virtual uint8\_t | [**decode**](#function-decode) (uint8\_t \* packet) override<br> |
| virtual void | [**encode**](#function-encode) (uint8\_t \* packet) override<br> |
|   | [**uint8\_t\_Component**](#function-uint8_t_component) (uint8\_t \* value, uint8\_t size, const uint8\_t min, const uint8\_t max, const uint8\_t priority=0) <br> |


## Public Functions inherited from Component

See [Component](classComponent.md)

| Type | Name |
| ---: | :--- |
|   | [**Component**](classComponent.md#function-component) (uint8\_t size, const uint8\_t priority=0) <br> |
| virtual uint8\_t | [**decode**](classComponent.md#function-decode) (uint8\_t \* packet) = 0<br> |
| virtual void | [**encode**](classComponent.md#function-encode) (uint8\_t \* packet) = 0<br> |














## Protected Attributes

| Type | Name |
| ---: | :--- |
|  uint8\_t | [**max**](#variable-max)  <br> |
|  uint8\_t | [**min**](#variable-min)  <br> |
|  uint8\_t | [**resolution**](#variable-resolution)  <br> |
|  uint8\_t \* | [**value**](#variable-value)  <br> |


































## Protected Functions inherited from Component

See [Component](classComponent.md)

| Type | Name |
| ---: | :--- |
|  void | [**bitReader**](classComponent.md#function-bitreader) (uint32\_t \* dataBits, uint8\_t \* packet) const<br> |
|  void | [**bitReset**](classComponent.md#function-bitreset) (uint8\_t \* packet) const<br> |
|  void | [**bitWriter**](classComponent.md#function-bitwriter) (uint32\_t dataBits, uint8\_t \* packet) const<br> |






## Public Functions Documentation




### function decode 

```C++
virtual uint8_t uint8_t_Component::decode (
    uint8_t * packet
) override
```



Implements [*Component::decode*](classComponent.md#function-decode)


<hr>



### function encode 

```C++
virtual void uint8_t_Component::encode (
    uint8_t * packet
) override
```



Implements [*Component::encode*](classComponent.md#function-encode)


<hr>



### function uint8\_t\_Component 

```C++
uint8_t_Component::uint8_t_Component (
    uint8_t * value,
    uint8_t size,
    const uint8_t min,
    const uint8_t max,
    const uint8_t priority=0
) 
```




<hr>
## Protected Attributes Documentation




### variable max 

```C++
uint8_t uint8_t_Component::max;
```




<hr>



### variable min 

```C++
uint8_t uint8_t_Component::min;
```




<hr>



### variable resolution 

```C++
uint8_t uint8_t_Component::resolution;
```




<hr>



### variable value 

```C++
uint8_t* uint8_t_Component::value;
```




<hr>

------------------------------
The documentation for this class was generated from the following file `libraries/DynamicPacketCodec/include/dataComponents.h`

