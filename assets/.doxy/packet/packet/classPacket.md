

# Class Packet



[**ClassList**](annotated.md) **>** [**Packet**](classPacket.md)





* `#include <baseClasses.h>`





















## Public Attributes

| Type | Name |
| ---: | :--- |
|  std::vector&lt; [**Component**](classComponent.md) \* &gt; | [**components**](#variable-components)  <br> |
















## Public Functions

| Type | Name |
| ---: | :--- |
|   | [**Packet**](#function-packet) () <br> |
|  void | [**addComponent**](#function-addcomponent) ([**Component**](classComponent.md) \* newComponent) <br> |
|  uint8\_t | [**decode**](#function-decode) (uint8\_t \* packet) <br> |
|  uint8\_t \* | [**encode**](#function-encode) () <br> |
|  uint8\_t | [**getBitSize**](#function-getbitsize) () const<br> |
|  uint8\_t | [**getByteSize**](#function-getbytesize) () const<br> |








## Protected Attributes

| Type | Name |
| ---: | :--- |
|  uint8\_t | [**bitSize**](#variable-bitsize)  <br> |




















## Public Attributes Documentation




### variable components 

```C++
std::vector<Component*> Packet::components;
```




<hr>
## Public Functions Documentation




### function Packet 

```C++
Packet::Packet () 
```




<hr>



### function addComponent 

```C++
void Packet::addComponent (
    Component * newComponent
) 
```




<hr>



### function decode 

```C++
uint8_t Packet::decode (
    uint8_t * packet
) 
```




<hr>



### function encode 

```C++
uint8_t * Packet::encode () 
```




<hr>



### function getBitSize 

```C++
uint8_t Packet::getBitSize () const
```




<hr>



### function getByteSize 

```C++
uint8_t Packet::getByteSize () const
```




<hr>
## Protected Attributes Documentation




### variable bitSize 

```C++
uint8_t Packet::bitSize;
```




<hr>

------------------------------
The documentation for this class was generated from the following file `libraries/DynamicPacketCodec/include/baseClasses.h`

