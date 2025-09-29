#include "Arduino.h"
#include "Wire.h"
#include "RC1780HP.h"
#include "Packet.h"

// Configuration
const uint8_t time_between_packets_standby = 30;                                              // in seconds               
const uint8_t hz = 8;                                                                         // in Hz
const uint16_t flight_mode_max_duration = 360 - 3600 / time_between_packets_standby / hz;     // in seconds

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

HardwareSerial* SerialTTL = &Serial4;
HardwareSerial* SerialHeader = &Serial1;
HardwareSerial* SerialModule = &Serial0;

RC1780HP rc1780hp(SerialModule, cfgpin, rstpin, ctspin, rtspin);

void get_packet_data();

void send_packet();

// Data components
uint8_t flight_mode = 0;
uint8_t low_power_mode = 0;
uint8_t i2c_connections = 0b000;
uint8_t subsystem_status = 0b000;
uint8_t status_event = 0;
float height_pressure = 0;
float height_gnss = 0;
float lat_gnss = 0;
float lon_gnss = 0;
float acceleration = 0;
float battery_voltage = 0;

void setup()
{
  pinMode(ledpin1, OUTPUT);
  pinMode(ledpinR, OUTPUT);
  pinMode(ledpinG, OUTPUT);
  pinMode(ledpinB, OUTPUT);
  pinMode(ledpin5, OUTPUT);
  pinMode(ledpin6, OUTPUT);
  pinMode(ledpin7, OUTPUT);
  pinMode(ledpin8, OUTPUT);
  pinMode(d1pin, INPUT);
  pinMode(d2pin, INPUT);
  pinMode(d3pin, INPUT);
  pinMode(armpin, OUTPUT);
  pinMode(slppin, OUTPUT);

  digitalWrite(ledpin1, HIGH);
  digitalWrite(ledpinR, HIGH);
  digitalWrite(ledpinG, LOW);
  digitalWrite(ledpinB, LOW);
  digitalWrite(ledpin5, LOW);
  digitalWrite(ledpin6, LOW);
  digitalWrite(ledpin7, LOW);
  digitalWrite(ledpin8, LOW);

  // SerialTTL->begin(19200);
  // SerialHeader->begin(19200);
  SerialModule->swap(1);

  Wire.swap(2);
  Wire.begin();
  
  rc1780hp.begin(19200);
  while(rc1780hp.ping() != 0);

  rc1780hp.memory_Reset();
  while(rc1780hp.set_RSSI_Mode(0x01) != 0);
  while(rc1780hp.set_Packet_Timeout(0x00) != 0);
  while(rc1780hp.set_Packet_End_Character(0xEE) != 0);
  while(rc1780hp.set_Address_Mode(0x00) != 0);
  while(rc1780hp.set_CRC_Mode(0x00) != 0);
  while(rc1780hp.set_LED_Control(0x01) != 0);

  rc1780hp.serial_Flush();
}

uint32_t loop_start_time;
uint8_t loop_count = 0;
uint8_t led_switch = 0;
uint32_t flight_mode_start_time;

void loop()
{
  loop_start_time = millis();

  get_packet_data();

  if(SerialModule->available() != 0)
  {
    switch (SerialModule->read())
    {
      // Flight mode
      case 'f': 
        if(flight_mode == 1)
        {
          digitalWrite(armpin, LOW);
          digitalWrite(ledpin5, LOW);
          flight_mode = 0;
          send_packet();
        }
        else
        {
          digitalWrite(armpin, HIGH);
          flight_mode_start_time = millis();
          flight_mode = 1;
        }
        break;
      
      // Low power mode
      case 'l': 
        if(low_power_mode == 1)
        {
          digitalWrite(slppin, LOW);
          low_power_mode = 0;
          send_packet();
        }
        else
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
      
      // Flight computer ping
      case 'p':
        send_packet();
        break;
      
      // Unknown command
      default: 
        break;
    }
  }

  if(low_power_mode == 0)
  {
    if(flight_mode == 1)
    {
      digitalWrite(ledpin5, HIGH);
    }

    digitalWrite(ledpin1, 1 - led_switch);

    // Sensorik 1
    if(i2c_connections & 0b001 != 0)
    {
      if(subsystem_status & 0b001 != 0)
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

    // Sensorik 2
    if(i2c_connections & 0b010 != 0)
    {
      if(subsystem_status & 0b010 != 0)
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

    // Landesysteme
    if(i2c_connections & 0b100 != 0)
    {
      if(subsystem_status & 0b100 != 0)
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

    if(i2c_connections == 0b111 && subsystem_status != 0b111)
    {
      digitalWrite(ledpinR, LOW);
      digitalWrite(ledpinG, LOW);
      digitalWrite(ledpinB, HIGH);
    }
    else if(i2c_connections == 0b111 && subsystem_status == 0b111)
    {
      digitalWrite(ledpinR, LOW);
      digitalWrite(ledpinG, HIGH);
      digitalWrite(ledpinB, LOW);
    }

    led_switch = 1 - led_switch;
  }

  if(flight_mode == 1)
  {
    if(millis() - flight_mode_start_time > flight_mode_max_duration * 1000)
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
  else if(loop_count % (time_between_packets_standby * hz) == 0)
  {
    send_packet;
    loop_count = 0;
  }
  
  delay(1000 / hz - (millis() - loop_start_time));
  loop_count++;
}

void get_packet_data()
{
  if(i2c_connections & 0b001 == 0)
  {
      Wire.beginTransmission(0x20);                       // Sensorik 1
      i2c_connections |= (Wire.endTransmission() == 0) << 0; 
  }
  if(i2c_connections & 0b010 == 0)
  {
      Wire.beginTransmission(0x30);                       // Sensorik 2
      i2c_connections |= (Wire.endTransmission() == 0) << 1; 
  }
  if(i2c_connections & 0b100 == 0)
  {
      Wire.beginTransmission(0x40);                       // Landesysteme
      i2c_connections |= (Wire.endTransmission() == 0) << 2; 
  }

  // Sensorik 1: Status (1 Byte), Druckhöhe (4 Bytes), GNSS Höhe (4 Bytes), GNSS Lat (4 Bytes) + Lon (4 Bytes)
  if(i2c_connections & 0b001 != 0)
  {
    Wire.requestFrom(0x20, 17); 
    uint8_t result[17];
    for(int i = 0; i < 17; i++)
      result[i] = Wire.read();

    subsystem_status = (subsystem_status & 0b110) | (result[0] << 0);

    height_pressure = (float)((int32_t)result[1] << 8*0 | (int32_t)result[2] << 8*1 | (int32_t)result[3] << 8*2 | (int32_t)result[4] << 8*3) / 100;
    height_gnss = (float)((int32_t)result[5] << 8*0 | (int32_t)result[6] << 8*1 | (int32_t)result[7] << 8*2 | (int32_t)result[8] << 8*3) / 100;
    lat_gnss = (float)((int32_t)result[9] << 8*0 | (int32_t)result[10] << 8*1 | (int32_t)result[11] << 8*2 | (int32_t)result[12] << 8*3) / 1000000;
    lon_gnss = (float)((int32_t)result[13] << 8*0 | (int32_t)result[14] << 8*1 | (int32_t)result[15] << 8*2 | (int32_t)result[16] << 8*3) / 1000000;
  }

  // Sensorik 2: Status (1 Byte), Beschleunigung (2 Bytes)
  if(i2c_connections & 0b010 != 0)
  {
    Wire.requestFrom(0x30, 3); 
    uint8_t result[3];
    for(int i = 0; i < 3; i++)
      result[i] = Wire.read();

    subsystem_status = (subsystem_status & 0b101) | (result[0] << 1);

    acceleration = (float)((int16_t)result[1] << 8*0 | (int16_t)result[2] << 8*1) / 100;
  }

  // Landesysteme: Status (1 Byte), Statusereignisse (1 Byte)
  if(i2c_connections & 0b100 != 0)
  {
    Wire.requestFrom(0x40, 2); 
    uint8_t result[2];
    for(int i = 0; i < 2; i++)
      result[i] = Wire.read();

    subsystem_status = (subsystem_status & 0b011) | (result[0] << 2);

    status_event = result[1];
  }

  // Batteriespannung
  battery_voltage = (float)analogRead(d2pin) / 1023 * 3.3 * (18 + 10) / 10;
}

void send_packet()
{
  uint8_t packet[15];
  Packet::encode(packet, 0x01, flight_mode, low_power_mode, subsystem_status == 0b111, status_event, acceleration, height_pressure, height_gnss, lat_gnss, lon_gnss, battery_voltage);
  for(int i = 0; i < 15; i++)
  {
    SerialModule->write(packet[i]);
  }
}