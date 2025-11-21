/*
    onboard - main.cpp of the board computer for the ASCENT II telemetry system.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Arduino.h"
#include "Wire.h"
#include "RC1780HP.h"
#include "Packet.h"

// Configuration
const uint8_t time_between_packets_standby = 15;                                              // in seconds   In standby, data packets are sent every 30 s   
const uint8_t hz = 8;                                                                         // in Hz        During flight, 8 Hz (125 ms interval)
const uint32_t flight_mode_max_duration = 360 - 3600 / time_between_packets_standby / hz;     // in seconds   6 min (360s) is max sending time

// Pin assignment
uint8_t ledpin1 = PIN_PG3;
uint8_t ledpinR = PIN_PG2;
uint8_t ledpinG = PIN_PG1;
uint8_t ledpinB = PIN_PG0;
uint8_t ledpin5 = PIN_PF2;
uint8_t ledpin6 = PIN_PE7;
uint8_t ledpin7 = PIN_PE5;
uint8_t ledpin8 = PIN_PE3;
uint8_t d1pin = PIN_PC6;
uint8_t d2pin = PIN_PD0;
uint8_t d3pin = PIN_PD2;
uint8_t armpin = PIN_PD6;
uint8_t slppin = PIN_PD4;

uint8_t cfgpin = PIN_PB6;
uint8_t rstpin = PIN_PF4;
uint8_t ctspin = PIN_PB5;
uint8_t rtspin = PIN_PB7;

HardwareSerial* SerialPC1 = &Serial4;
HardwareSerial* SerialPC2 = &Serial1;
HardwareSerial* SerialModule = &Serial0;

// Radio module initialisation
RC1780HP rc1780hp(SerialModule, cfgpin, rstpin, ctspin, rtspin);

// Functions declaration
void get_packet_data();
void send_packet();

// Data components
int8_t temperature = 0;
uint8_t subsystem_status = 0b000;
uint8_t flight_mode = 0;
uint8_t low_power_mode = 0;
uint8_t i2c_connections = 0b000;
uint8_t status_events = 0;
float height_pressure = 0;
float height_gnss = 0;
float lat_gnss = 0;
float lon_gnss = 0;
float acceleration = 0;
float battery_voltage = 0;

void setup()
{
  pinMode(ledpin1, OUTPUT); // Power on
  pinMode(ledpinR, OUTPUT); // Red
  pinMode(ledpinG, OUTPUT); // Green
  pinMode(ledpinB, OUTPUT); // Blue
  pinMode(ledpin5, OUTPUT); // Flight mode
  pinMode(ledpin6, OUTPUT); // Sensor circuit board 1
  pinMode(ledpin7, OUTPUT); // Sensor circuit board 2
  pinMode(ledpin8, OUTPUT); // Landing systems
  pinMode(d1pin, INPUT);
  pinMode(d2pin, INPUT);
  pinMode(d3pin, INPUT);
  pinMode(armpin, OUTPUT);
  pinMode(slppin, OUTPUT);

  // Only LED1 (power indicator) and RGB LED are turned on
  digitalWrite(ledpin1, HIGH);
  digitalWrite(ledpinR, HIGH);
  digitalWrite(ledpinG, LOW);
  digitalWrite(ledpinB, LOW);
  digitalWrite(ledpin5, LOW);
  digitalWrite(ledpin6, LOW);
  digitalWrite(ledpin7, LOW);
  digitalWrite(ledpin8, LOW);

  // Initialize UART
  //SerialPC1->begin(115200);
  //SerialPC2->begin(115200);
  SerialModule->swap(1);// Swap RX/TX pins for radio module uart connection
 
  // Initialize I2C
  Wire.swap(2);
  Wire.begin();
  
  // Initialize radio transceiver and wait until communication is established
  delay(3.2 * 2); // Necessary delay: t_{OFF-IDLE} = 3.2, safety factor 2
  rc1780hp.begin(19200);
  delay(3.2 * 2); // Necessary delay: t_{OFF-IDLE} = 3.2, safety factor 2
  rc1780hp.ping();

  // Before each flight memory is reset and non-standard settings are reconfigured
  while(rc1780hp.memory_Reset() != 0);
  while(rc1780hp.set_RSSI_Mode(0x01) != 0);
  while(rc1780hp.set_Packet_Timeout(0x00) != 0);
  while(rc1780hp.set_Packet_End_Character(0xEE) != 0);
  while(rc1780hp.set_Address_Mode(0x00) != 0);
  while(rc1780hp.set_CRC_Mode(0x00) != 0);
  while(rc1780hp.set_LED_Control(0x01) != 0);
  rc1780hp.hard_reset();
  rc1780hp.serial_Flush();
}

uint32_t loop_start_time;
uint8_t loop_count = 0;
uint8_t led_switch = 0;
uint32_t flight_mode_start_time;

void loop()
{
  loop_start_time = millis();

  // Update variables from i2c connected systems at the beginning of each cycle
  get_packet_data();

  // MISSING: De-arming after landing (status_event == 13)
  
  // Check for incoming data from groundstation
  if(SerialModule->available() != 0)
  {
    // MISSING: Parity check

    // Process incoming serial commands from the groundstation
    // The command reference can be found under docs/commands.md
    switch (SerialModule->read())
    {

      // Flight computer ping

      case 'p':
        send_packet();
        break;

      // Main parachute height adjustment

      case 'a': // 50 m
        Wire.beginTransmission(0x40);
        Wire.write('a');
        Wire.endTransmission();
        break;
      
      case 'b': // 100 m
        Wire.beginTransmission(0x40);
        Wire.write('b');
        Wire.endTransmission();
        break;

      case 'c': // 150 m
        Wire.beginTransmission(0x40);
        Wire.write('c');
        Wire.endTransmission();
        break;

      case 'd': // 200 m
        Wire.beginTransmission(0x40);
        Wire.write('d');
        Wire.endTransmission();
        break;
      
      // Low power mode 

      case 'l': // activation
        if(low_power_mode == 0)
        {
          digitalWrite(slppin, HIGH);
          digitalWrite(ledpin1, LOW);
          digitalWrite(ledpinR, LOW);
          digitalWrite(ledpinG, LOW); 
          digitalWrite(ledpinB, LOW);
          digitalWrite(ledpin5, LOW); 
          digitalWrite(ledpin6, LOW); 
          digitalWrite(ledpin7, LOW); 
          digitalWrite(ledpin8, LOW); 
          low_power_mode = 1;
          send_packet();
        }
        break;
      
      case 'm': // deactivation
        if(low_power_mode == 1)
        {
          digitalWrite(slppin, LOW);
          low_power_mode = 0;
          send_packet();
        }
        break;
      
      // Flight mode 

      case 'f': // activation
        if(flight_mode == 0)
        {
          digitalWrite(armpin, HIGH);
          delay(1);
          if(digitalRead(d3pin) == HIGH)
          {
            digitalWrite(ledpin5, HIGH);
            flight_mode_start_time = millis();
            flight_mode = 1;
            Wire.beginTransmission(0x40);
            Wire.write('f');
            Wire.endTransmission();
          }
          else
          {
            digitalWrite(armpin, LOW);
          }
        }
        break;
      
      case 'g': // deactivation
        if(flight_mode == 1)
        {
          digitalWrite(armpin, LOW);
          delay(1);
          if(digitalRead(d3pin) == LOW)
          {
            digitalWrite(ledpin5, LOW);
            flight_mode = 0;
            Wire.beginTransmission(0x40);
            Wire.write('g');
            Wire.endTransmission();
          }
          else
          {
            digitalWrite(armpin, HIGH);
          }
          send_packet();
        }
        break;

      // Drogue parachute ejection

      case 'q':
        Wire.beginTransmission(0x40);
        Wire.write('q');
        Wire.endTransmission();
        break;

      // Main parachute ejection

      case 'r':
        Wire.beginTransmission(0x40);
        Wire.write('r');
        Wire.endTransmission();
        break;
      
      // Unknown command

      default: 
        break;
    }
  }

  // Check if the other boards are connected and ready (When a system is connected or ready, a 1 is written to the respective position. E.g. 0b111 then means that all are connected)
  if(low_power_mode == 0)
  {
    if(flight_mode == 1)
    {
      digitalWrite(ledpin5, HIGH);
    }

    digitalWrite(ledpin1, 1 - led_switch);

    // Sensor circuit board 1
    if((i2c_connections & 0b001) != 0)
    {
      if((subsystem_status & 0b001) != 0)
      {
        digitalWrite(ledpin6, HIGH);
      }
      else
      {
        digitalWrite(ledpin6, led_switch);
      }
    }
    else
    {
      digitalWrite(ledpin6, LOW);
    }

    // Sensor circuit board 2
    if((i2c_connections & 0b010) != 0)
    {
      if((subsystem_status & 0b010) != 0)
      {
        digitalWrite(ledpin7, HIGH);
      }
      else
      {
        digitalWrite(ledpin7, led_switch);
      }
    }
    else
    {
      digitalWrite(ledpin7, LOW);
    }

    // Landing systems
    if((i2c_connections & 0b100) != 0)
    {
      if((subsystem_status & 0b100) != 0)
      {
        digitalWrite(ledpin8, HIGH);
      }
      else
      {
        digitalWrite(ledpin8, led_switch);
      }
    }
    else
    {
      digitalWrite(ledpin8, LOW);
    }

    // All boards connected but not ready (RGB_LED turns blue)
    if(i2c_connections == 0b111 && subsystem_status != 0b111)
    {
      digitalWrite(ledpinR, LOW);
      digitalWrite(ledpinG, LOW);
      digitalWrite(ledpinB, HIGH);
    }
    // All connected and ready (RGB_LED turns green)
    else if(i2c_connections == 0b111 && subsystem_status == 0b111)
    {
      digitalWrite(ledpinR, LOW);
      digitalWrite(ledpinG, HIGH);
      digitalWrite(ledpinB, LOW);
    }

    led_switch = 1 - led_switch;
  }

  // Send data to groundstation
  if(flight_mode == 1)
  {
    if(millis() - flight_mode_start_time > flight_mode_max_duration * 1000) // If the maximum legal transmission time is reached, the flight mode must be turned off
    {
      // Sollte Arming Pin auf Low?
      flight_mode = 0;
      digitalWrite(ledpin5, LOW);
      send_packet();
    }
    else
    {
      send_packet();
    }
  }
  else if(loop_count % (time_between_packets_standby * hz) == 0) // Sending in non-flight mode
  {
    send_packet();
    loop_count = 0;
  }
  
  delay(1000 / hz - (millis() - loop_start_time)); // Waits until the iteration has taken 125ms
  loop_count++;
}

void get_packet_data()
{
  // If sensor board not yet confirmed connected, test I²C response
  if((i2c_connections & 0b001) == 0)
  {
      Wire.beginTransmission(0x20);                       // Sensor circuit board 1
      i2c_connections |= ((Wire.endTransmission() == 0) << 0); 
  }
  if((i2c_connections & 0b010) == 0)
  {
      Wire.beginTransmission(0x30);                       // Sensor circuit board 2
      i2c_connections |= ((Wire.endTransmission() == 0) << 1); 
  }
  if((i2c_connections & 0b100) == 0)
  {
      Wire.beginTransmission(0x40);                       // Landing systems
      i2c_connections |= ((Wire.endTransmission() == 0) << 2); 
  }

  uint32_t tmp;

  // Sensor circuit board 1: status (1 Byte), height pressure (4 Bytes), GNSS height (4 Bytes), GNSS Lat (4 Bytes) + Lon (4 Bytes)
  if((i2c_connections & 0b001) != 0)
  {
    Wire.requestFrom(0x20, 17); 
    uint8_t result[17];
    for(int i = 0; i < 17; i++)
      result[i] = Wire.read();

    subsystem_status = (subsystem_status & 0b110) | ((result[0] == 0x01) << 0);

    // Turns 4-Byte data into float

    tmp = ((uint32_t)result[4] << 24) | ((uint32_t)result[3] << 16) | ((uint32_t)result[2] << 8) | ((uint32_t)result[1]);
    height_pressure = *(float*)&tmp;

    tmp = ((uint32_t)result[8] << 24) | ((uint32_t)result[7] << 16) | ((uint32_t)result[6] << 8) | ((uint32_t)result[5]);
    height_gnss = *(float*)&tmp;

    tmp = ((uint32_t)result[12] << 24) | ((uint32_t)result[11] << 16) | ((uint32_t)result[10] << 8) | ((uint32_t)result[9]);
    lat_gnss = *(float*)&tmp;

    tmp = ((uint32_t)result[16] << 24) | ((uint32_t)result[15] << 16) | ((uint32_t)result[14] << 8) | ((uint32_t)result[13]);
    lon_gnss = *(float*)&tmp;
  }

  // Sensor circuit board 2: status (1 Byte), acceleration (4 Bytes)
  if((i2c_connections & 0b010) != 0)
  {
    Wire.requestFrom(0x30, 5); 
    uint8_t result[5];
    for(int i = 0; i < 5; i++)
      result[i] = Wire.read();

    subsystem_status = (subsystem_status & 0b101) | ((result[0] == 0x01) << 1);

    // Turns 4-Byte data into float

    tmp = ((uint32_t)result[4] << 24) | ((uint32_t)result[3] << 16) | ((uint32_t)result[2] << 8) | ((uint32_t)result[1]);
    acceleration = *(float*)&tmp;
  }

  // Landing systems: status (1 Byte), status events (1 Byte)
  if((i2c_connections & 0b100) != 0)
  {
    Wire.requestFrom(0x40, 2); 
    uint8_t result[2];
    for(int i = 0; i < 2; i++)
      result[i] = Wire.read();

    subsystem_status = (subsystem_status & 0b011) | ((result[0] == 0x01) << 2);

    status_events = result[1];
  }

  // Battery_voltage (Voltage divider)
  battery_voltage = (float)analogRead(d2pin) / 1023 * 3.3 * (18 + 10) / 10;

  #if(0)
  // Temperature
  rc1780hp.read_Temperature(&temperature);
  #endif
}

// Encodes current data into 15-Byte packet and transmits it
void send_packet()
{
  uint8_t packet[15] = { 0 };
  Packet::encode(packet, (float)temperature, subsystem_status, flight_mode, low_power_mode, status_events, acceleration, height_pressure, height_gnss, lat_gnss, lon_gnss, battery_voltage);
  SerialModule->write(packet, 15);
}