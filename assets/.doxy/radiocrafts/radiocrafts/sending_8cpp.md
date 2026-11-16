

# File sending.cpp



[**FileList**](files.md) **>** [**examples**](dir_b3b07431d1f2dc23f8f90d7ee279ceb1.md) **>** [**sending.cpp**](sending_8cpp.md)

[Go to the source code of this file](sending_8cpp_source.md)



* `#include "Arduino.h"`
* `#include "../Radiocrafts_RC17xxHP_RC232.h"`





















## Public Attributes

| Type | Name |
| ---: | :--- |
|  HardwareSerial \* | [**SerialModule**](#variable-serialmodule)   = `&Serial0`<br> |
|  uint32\_t | [**baudrate**](#variable-baudrate)   = `19200`<br> |
|  uint8\_t | [**pinCFG**](#variable-pincfg)   = `PIN\_PA5`<br> |
|  uint8\_t | [**pinCTS**](#variable-pincts)   = `PIN\_PA3`<br> |
|  uint8\_t | [**pinRST**](#variable-pinrst)   = `PIN\_PG7`<br> |
|  uint8\_t | [**pinRTS**](#variable-pinrts)   = `PIN\_PA4`<br> |
|  uint8\_t | [**pinRX**](#variable-pinrx)   = `PIN\_PA1`<br> |
|  uint8\_t | [**pinTX**](#variable-pintx)   = `PIN\_PA0`<br> |
|  [**RC17xxHP\_RC232**](classRC17xxHP__RC232.md) | [**rc1780hp**](#variable-rc1780hp)  <br> |
















## Public Functions

| Type | Name |
| ---: | :--- |
|  int | [**main**](#function-main) () <br> |




























## Public Attributes Documentation




### variable SerialModule 

```C++
HardwareSerial* SerialModule;
```




<hr>



### variable baudrate 

```C++
uint32_t baudrate;
```




<hr>



### variable pinCFG 

```C++
uint8_t pinCFG;
```




<hr>



### variable pinCTS 

```C++
uint8_t pinCTS;
```




<hr>



### variable pinRST 

```C++
uint8_t pinRST;
```




<hr>



### variable pinRTS 

```C++
uint8_t pinRTS;
```




<hr>



### variable pinRX 

```C++
uint8_t pinRX;
```




<hr>



### variable pinTX 

```C++
uint8_t pinTX;
```




<hr>



### variable rc1780hp 

```C++
RC17xxHP_RC232 rc1780hp(SerialModule, pinTX, pinRX, 19200, pinCFG, pinRST, pinCTS, pinRTS);
```




<hr>
## Public Functions Documentation




### function main 

```C++
int main () 
```




<hr>

------------------------------
The documentation for this class was generated from the following file `libraries/Radiocrafts_RC17xxHP_RC232/examples/sending.cpp`

