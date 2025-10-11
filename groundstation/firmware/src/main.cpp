#include "Arduino.h"
#include "RC1780HP.h"
#include "Packet.h"

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

// Data components
uint8_t address = 0;
uint8_t flight_mode = 0;
uint8_t low_power_mode = 0;
uint8_t subsystem_status = 0;
uint8_t status_events = 0;
float height_pressure = 0;
float height_gnss = 0;
float lat_gnss = 0;
float lon_gnss = 0;
float acceleration = 0;
float battery_voltage = 0;
float rssi = 0;

//incoming Data
uint8_t packet[15] = 0;
uint8_t incoming_Byte = 0;
uint8_t index = 0;

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

  SerialTTL->begin(19200);
  // SerialHeader->begin(19200);
  SerialModule->swap(1);

  rc1780hp.begin(19200);
  while(rc1780hp.ping() != 0);

  rc1780hp.memory_Reset();
  while(rc1780hp.set_RSSI_Mode(0x01) != 0);
  while(rc1780hp.set_Packet_Timeout(0x00) != 0);
  while(rc1780hp.set_Packet_End_Character(0xEE) != 0);
  while(rc1780hp.set_Address_Mode(0x00) != 0);
  while(rc1780hp.set_CRC_Mode(0x00) != 0);
  while(rc1780hp.set_LED_Control(0x01) != 0);

  rc1780hp.hard_reset();
  rc1780hp.serial_Flush();

  digitalWrite(ledpinR, LOW);
  digitalWrite(ledpinG, HIGH);
}

void loop()
{
  if(SerialTTL->available() != 0)
  {
    SerialModule->write(SerialTTL->read());
  }

  if(Serial.available() != 0)
  {
    while(incoming_Byte != 0xEE)
    {
      incoming_Byte = Serial.read();
      packet[index] = incoming_Byte;
      index++;
    }
    incoming_Byte = Serial.read();
    packet[index] = incoming_Byte;

    if(packet[index - 1] == 0xEE)
    {
      Packet::decode(packet, &address, &flight_mode, &low_power_mode, &subsystem_status, &status_events, &acceleration, &height_pressure, &height_gnss, &lat_gnss, &lon_gnss, &battery_voltage, &rssi);
      SerialTTL->print("address:");            SerialTTL->println(address);
      SerialTTL->print("flight_mode:");        SerialTTL->println(flight_mode);
      SerialTTL->print("low_power_mode:");     SerialTTL->println(low_power_mode);
      SerialTTL->print("subsystem_status:");   SerialTTL->println(subsystem_status);
      SerialTTL->print("status_events:");      SerialTTL->println(status_events);
      SerialTTL->print("acceleration:");       SerialTTL->println(acceleration);
      SerialTTL->print("height_pressure:");    SerialTTL->println(height_pressure);
      SerialTTL->print("height_gnss:");        SerialTTL->println(height_gnss);
      SerialTTL->print("lat_gnss:");           SerialTTL->println(lat_gnss);
      SerialTTL->print("lon_gnss:");           SerialTTL->println(lon_gnss);
      SerialTTL->print("battery_voltage:");    SerialTTL->println(battery_voltage);
      SerialTTL->print("rssi:");               SerialTTL->println(rssi);

      //LED5 (subsystem_status)
      if(subsystem_status == 0b111)
      {
        digitalWrite(ledpin5, HIGH);
      }
      else
      {
        digitalWrite(ledpin5, LOW);
      }

      //LED6 (battery_voltage)
      if(battery_voltage > 7.2)
      {
        digitalWrite(ledpin6, HIGH);
      }
      else
      {
        digitalWrite(ledpin6, LOW);
      }
      
      //Main LED (RSSI)
      if(rssi > -50 )
      {
        digitalWrite(ledpinG, HIGH);
        digitalWrite(ledpinB, LOW);
        digitalWrite(ledpinR, LOW);
      }

      else if(rssi > -80)
      {
        digitalWrite(ledpinG, LOW);
        digitalWrite(ledpinB, HIGH);
        digitalWrite(ledpinR, LOW); 
      }

      else
      {
        digitalWrite(ledpinG, LOW);
        digitalWrite(ledpinB, LOW);
        digitalWrite(ledpinR, HIGH);
      }

    }
    index = 0;
    incoming_Byte = 0;
    memset(packet, 0, sizeof(packet));
  }
  
}