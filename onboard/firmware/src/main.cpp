#include "Arduino.h"
#include "Wire.h"
#include "RC1780HP.h"

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
  pinMode(armpin, INPUT);
  pinMode(slppin, INPUT);

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

  Wire.swap(2);
  Wire.begin();
  
  rc1780hp.begin(19200);
  
  rc1780hp.memory_Reset();
  while(rc1780hp.set_RSSI_Mode(0x01) != 0);
  while(rc1780hp.set_Packet_Timeout(0x00) != 0);
  while(rc1780hp.set_Packet_End_Character(0xEE) != 0);
  while(rc1780hp.set_Address_Mode(0x00) != 0);
  while(rc1780hp.set_CRC_Mode(0x00) != 0);
  while(rc1780hp.set_LED_Control(0x01) != 0);

  uint8_t i2c_connections = 0b000;
  while(i2c_connections != 0b111)
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
  }
  
  digitalWrite(ledpinR, LOW);
  digitalWrite(ledpinB, HIGH);
}

void loop()
{
  
}
