

# Class RC17xxHP\_RC232



[**ClassList**](annotated.md) **>** [**RC17xxHP\_RC232**](classRC17xxHP__RC232.md)





* `#include <Radiocrafts_RC17xxHP_RC232.h>`





































## Public Functions

| Type | Name |
| ---: | :--- |
|   | [**RC17xxHP\_RC232**](#function-rc17xxhp_rc232) (HardwareSerial \* serial, uint8\_t pinTX, uint8\_t pinRX, uint32\_t baudrate, uint8\_t pinCFG, uint8\_t pinRST, uint8\_t pinCTS, uint8\_t pinRTS) <br> |
|  uint8\_t | [**available**](#function-available) () <br> |
|  void | [**begin**](#function-begin) () <br> |
|  void | [**flush**](#function-flush) () <br> |
|  uint8\_t | [**get\_ADDRESS\_MODE**](#function-get_address_mode) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_BID**](#function-get_bid) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_CRC\_MODE**](#function-get_crc_mode) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_DID**](#function-get_did) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_LED\_CONTROL**](#function-get_led_control) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_PACKET\_END\_CHARACTER**](#function-get_packet_end_character) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_PACKET\_LENGTH**](#function-get_packet_length) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_PACKET\_TIMEOUT**](#function-get_packet_timeout) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_RF\_CHANNEL**](#function-get_rf_channel) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_RF\_DATA\_RATE**](#function-get_rf_data_rate) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_RF\_POWER**](#function-get_rf_power) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_RSSI\_MODE**](#function-get_rssi_mode) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_SID**](#function-get_sid) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_SLEEP\_MODE**](#function-get_sleep_mode) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_UART\_BAUD\_RATE**](#function-get_uart_baud_rate) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_UART\_FLOW\_CONTROL**](#function-get_uart_flow_control) (uint8\_t \* result) <br> |
|  uint8\_t | [**get\_UID**](#function-get_uid) (uint8\_t \* result) <br> |
|  uint8\_t | [**memoryReset**](#function-memoryreset) () <br> |
|  uint8\_t | [**ping**](#function-ping) () <br> |
|  void | [**read**](#function-read-12) (uint8\_t \* bytes, uint8\_t length) <br> |
|  uint8\_t | [**read**](#function-read-22) () <br> |
|  uint8\_t | [**read\_RSSI**](#function-read_rssi) (float \* result) <br> |
|  uint8\_t | [**read\_TEMPERATURE**](#function-read_temperature) (int8\_t \* result) <br> |
|  uint8\_t | [**read\_VOLTAGE**](#function-read_voltage) (float \* result) <br> |
|  uint8\_t | [**resetHard**](#function-resethard) () <br> |
|  uint8\_t | [**resetSoft**](#function-resetsoft) () <br> |
|  void | [**send**](#function-send-12) (uint8\_t \* bytes, uint8\_t length) <br> |
|  void | [**send**](#function-send-22) (uint8\_t byte) <br> |
|  uint16\_t | [**serialWait**](#function-serialwait) (uint32\_t delayMicroseconds) <br> |
|  uint8\_t | [**set\_ADDRESS\_MODE**](#function-set_address_mode) (uint8\_t value) <br> |
|  uint8\_t | [**set\_BID**](#function-set_bid) (uint8\_t value) <br> |
|  uint8\_t | [**set\_CRC\_MODE**](#function-set_crc_mode) (uint8\_t value) <br> |
|  uint8\_t | [**set\_DID**](#function-set_did) (uint8\_t value) <br> |
|  uint8\_t | [**set\_LED\_CONTROL**](#function-set_led_control) (uint8\_t value) <br> |
|  uint8\_t | [**set\_PACKET\_END\_CHARACTER**](#function-set_packet_end_character) (uint8\_t value) <br> |
|  uint8\_t | [**set\_PACKET\_LENGTH**](#function-set_packet_length) (uint8\_t value) <br> |
|  uint8\_t | [**set\_PACKET\_TIMEOUT**](#function-set_packet_timeout) (uint8\_t value) <br> |
|  uint8\_t | [**set\_RF\_CHANNEL**](#function-set_rf_channel) (uint8\_t value) <br> |
|  uint8\_t | [**set\_RF\_DATA\_RATE**](#function-set_rf_data_rate) (uint8\_t value) <br> |
|  uint8\_t | [**set\_RF\_POWER**](#function-set_rf_power) (uint8\_t value) <br> |
|  uint8\_t | [**set\_RSSI\_MODE**](#function-set_rssi_mode) (uint8\_t value) <br> |
|  uint8\_t | [**set\_SID**](#function-set_sid) (uint8\_t value) <br> |
|  uint8\_t | [**set\_SLEEP\_MODE**](#function-set_sleep_mode) (uint8\_t value) <br> |
|  uint8\_t | [**set\_UART\_BAUD\_RATE**](#function-set_uart_baud_rate) (uint8\_t value) <br> |
|  uint8\_t | [**set\_UART\_FLOW\_CONTROL**](#function-set_uart_flow_control) (uint8\_t value) <br> |
|  uint8\_t | [**set\_UID**](#function-set_uid) (uint8\_t value) <br> |




























## Public Functions Documentation




### function RC17xxHP\_RC232 

```C++
RC17xxHP_RC232::RC17xxHP_RC232 (
    HardwareSerial * serial,
    uint8_t pinTX,
    uint8_t pinRX,
    uint32_t baudrate,
    uint8_t pinCFG,
    uint8_t pinRST,
    uint8_t pinCTS,
    uint8_t pinRTS
) 
```




<hr>



### function available 

```C++
uint8_t RC17xxHP_RC232::available () 
```




<hr>



### function begin 

```C++
void RC17xxHP_RC232::begin () 
```




<hr>



### function flush 

```C++
void RC17xxHP_RC232::flush () 
```




<hr>



### function get\_ADDRESS\_MODE 

```C++
uint8_t RC17xxHP_RC232::get_ADDRESS_MODE (
    uint8_t * result
) 
```




<hr>



### function get\_BID 

```C++
uint8_t RC17xxHP_RC232::get_BID (
    uint8_t * result
) 
```




<hr>



### function get\_CRC\_MODE 

```C++
uint8_t RC17xxHP_RC232::get_CRC_MODE (
    uint8_t * result
) 
```




<hr>



### function get\_DID 

```C++
uint8_t RC17xxHP_RC232::get_DID (
    uint8_t * result
) 
```




<hr>



### function get\_LED\_CONTROL 

```C++
uint8_t RC17xxHP_RC232::get_LED_CONTROL (
    uint8_t * result
) 
```




<hr>



### function get\_PACKET\_END\_CHARACTER 

```C++
uint8_t RC17xxHP_RC232::get_PACKET_END_CHARACTER (
    uint8_t * result
) 
```




<hr>



### function get\_PACKET\_LENGTH 

```C++
uint8_t RC17xxHP_RC232::get_PACKET_LENGTH (
    uint8_t * result
) 
```




<hr>



### function get\_PACKET\_TIMEOUT 

```C++
uint8_t RC17xxHP_RC232::get_PACKET_TIMEOUT (
    uint8_t * result
) 
```




<hr>



### function get\_RF\_CHANNEL 

```C++
uint8_t RC17xxHP_RC232::get_RF_CHANNEL (
    uint8_t * result
) 
```




<hr>



### function get\_RF\_DATA\_RATE 

```C++
uint8_t RC17xxHP_RC232::get_RF_DATA_RATE (
    uint8_t * result
) 
```




<hr>



### function get\_RF\_POWER 

```C++
uint8_t RC17xxHP_RC232::get_RF_POWER (
    uint8_t * result
) 
```




<hr>



### function get\_RSSI\_MODE 

```C++
uint8_t RC17xxHP_RC232::get_RSSI_MODE (
    uint8_t * result
) 
```




<hr>



### function get\_SID 

```C++
uint8_t RC17xxHP_RC232::get_SID (
    uint8_t * result
) 
```




<hr>



### function get\_SLEEP\_MODE 

```C++
uint8_t RC17xxHP_RC232::get_SLEEP_MODE (
    uint8_t * result
) 
```




<hr>



### function get\_UART\_BAUD\_RATE 

```C++
uint8_t RC17xxHP_RC232::get_UART_BAUD_RATE (
    uint8_t * result
) 
```




<hr>



### function get\_UART\_FLOW\_CONTROL 

```C++
uint8_t RC17xxHP_RC232::get_UART_FLOW_CONTROL (
    uint8_t * result
) 
```




<hr>



### function get\_UID 

```C++
uint8_t RC17xxHP_RC232::get_UID (
    uint8_t * result
) 
```




<hr>



### function memoryReset 

```C++
uint8_t RC17xxHP_RC232::memoryReset () 
```




<hr>



### function ping 

```C++
uint8_t RC17xxHP_RC232::ping () 
```




<hr>



### function read [1/2]

```C++
void RC17xxHP_RC232::read (
    uint8_t * bytes,
    uint8_t length
) 
```




<hr>



### function read [2/2]

```C++
uint8_t RC17xxHP_RC232::read () 
```




<hr>



### function read\_RSSI 

```C++
uint8_t RC17xxHP_RC232::read_RSSI (
    float * result
) 
```




<hr>



### function read\_TEMPERATURE 

```C++
uint8_t RC17xxHP_RC232::read_TEMPERATURE (
    int8_t * result
) 
```




<hr>



### function read\_VOLTAGE 

```C++
uint8_t RC17xxHP_RC232::read_VOLTAGE (
    float * result
) 
```




<hr>



### function resetHard 

```C++
uint8_t RC17xxHP_RC232::resetHard () 
```




<hr>



### function resetSoft 

```C++
uint8_t RC17xxHP_RC232::resetSoft () 
```




<hr>



### function send [1/2]

```C++
void RC17xxHP_RC232::send (
    uint8_t * bytes,
    uint8_t length
) 
```




<hr>



### function send [2/2]

```C++
void RC17xxHP_RC232::send (
    uint8_t byte
) 
```




<hr>



### function serialWait 

```C++
uint16_t RC17xxHP_RC232::serialWait (
    uint32_t delayMicroseconds
) 
```




<hr>



### function set\_ADDRESS\_MODE 

```C++
uint8_t RC17xxHP_RC232::set_ADDRESS_MODE (
    uint8_t value
) 
```




<hr>



### function set\_BID 

```C++
uint8_t RC17xxHP_RC232::set_BID (
    uint8_t value
) 
```




<hr>



### function set\_CRC\_MODE 

```C++
uint8_t RC17xxHP_RC232::set_CRC_MODE (
    uint8_t value
) 
```




<hr>



### function set\_DID 

```C++
uint8_t RC17xxHP_RC232::set_DID (
    uint8_t value
) 
```




<hr>



### function set\_LED\_CONTROL 

```C++
uint8_t RC17xxHP_RC232::set_LED_CONTROL (
    uint8_t value
) 
```




<hr>



### function set\_PACKET\_END\_CHARACTER 

```C++
uint8_t RC17xxHP_RC232::set_PACKET_END_CHARACTER (
    uint8_t value
) 
```




<hr>



### function set\_PACKET\_LENGTH 

```C++
uint8_t RC17xxHP_RC232::set_PACKET_LENGTH (
    uint8_t value
) 
```




<hr>



### function set\_PACKET\_TIMEOUT 

```C++
uint8_t RC17xxHP_RC232::set_PACKET_TIMEOUT (
    uint8_t value
) 
```




<hr>



### function set\_RF\_CHANNEL 

```C++
uint8_t RC17xxHP_RC232::set_RF_CHANNEL (
    uint8_t value
) 
```




<hr>



### function set\_RF\_DATA\_RATE 

```C++
uint8_t RC17xxHP_RC232::set_RF_DATA_RATE (
    uint8_t value
) 
```




<hr>



### function set\_RF\_POWER 

```C++
uint8_t RC17xxHP_RC232::set_RF_POWER (
    uint8_t value
) 
```




<hr>



### function set\_RSSI\_MODE 

```C++
uint8_t RC17xxHP_RC232::set_RSSI_MODE (
    uint8_t value
) 
```




<hr>



### function set\_SID 

```C++
uint8_t RC17xxHP_RC232::set_SID (
    uint8_t value
) 
```




<hr>



### function set\_SLEEP\_MODE 

```C++
uint8_t RC17xxHP_RC232::set_SLEEP_MODE (
    uint8_t value
) 
```




<hr>



### function set\_UART\_BAUD\_RATE 

```C++
uint8_t RC17xxHP_RC232::set_UART_BAUD_RATE (
    uint8_t value
) 
```




<hr>



### function set\_UART\_FLOW\_CONTROL 

```C++
uint8_t RC17xxHP_RC232::set_UART_FLOW_CONTROL (
    uint8_t value
) 
```




<hr>



### function set\_UID 

```C++
uint8_t RC17xxHP_RC232::set_UID (
    uint8_t value
) 
```




<hr>

------------------------------
The documentation for this class was generated from the following file `libraries/Radiocrafts_RC17xxHP_RC232/Radiocrafts_RC17xxHP_RC232.h`

