

# Class char\_Component



[**ClassList**](annotated.md) **>** [**char\_Component**](classchar__Component.md)





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
|   | [**char\_Component**](#function-char_component) (uint8\_t \* value, const uint8\_t priority=0) <br> |
| virtual uint8\_t | [**decode**](#function-decode) (uint8\_t \* packet) override<br> |
| virtual void | [**encode**](#function-encode) (uint8\_t \* packet) override<br> |


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
|  uint8\_t \* | [**value**](#variable-value)  <br> |


































## Protected Functions inherited from Component

See [Component](classComponent.md)

| Type | Name |
| ---: | :--- |
|  void | [**bitReader**](classComponent.md#function-bitreader) (uint32\_t \* dataBits, uint8\_t \* packet) const<br> |
|  void | [**bitReset**](classComponent.md#function-bitreset) (uint8\_t \* packet) const<br> |
|  void | [**bitWriter**](classComponent.md#function-bitwriter) (uint32\_t dataBits, uint8\_t \* packet) const<br> |






## Public Functions Documentation




### function char\_Component 

```C++
char_Component::char_Component (
    uint8_t * value,
    const uint8_t priority=0
) 
```




<hr>



### function decode 

```C++
virtual uint8_t char_Component::decode (
    uint8_t * packet
) override
```



Implements [*Component::decode*](classComponent.md#function-decode)


<hr>



### function encode 

```C++
virtual void char_Component::encode (
    uint8_t * packet
) override
```



Implements [*Component::encode*](classComponent.md#function-encode)


<hr>
## Protected Attributes Documentation




### variable value 

```C++
uint8_t* char_Component::value;
```




<hr>

------------------------------
The documentation for this class was generated from the following file `libraries/DynamicPacketCodec/include/dataComponents.h`

