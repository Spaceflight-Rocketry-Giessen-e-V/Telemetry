#include "Arduino.h"
#include "RC1780HP.h"

void setup()
{
  uint8_t ledpin1 = PIN_PG3;
  uint8_t ledpin2 = PIN_PG2;
  uint8_t ledpin3 = PIN_PG1;
  uint8_t ledpin4 = PIN_PG0;
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
    
  pinMode(ledpin1, OUTPUT);
  pinMode(ledpin2, OUTPUT);
  pinMode(ledpin3, OUTPUT);
  pinMode(ledpin4, OUTPUT);
  pinMode(ledpin5, OUTPUT);
  pinMode(ledpin6, OUTPUT);
  pinMode(ledpin7, OUTPUT);
  pinMode(ledpin8, OUTPUT);
  pinMode(d1pin, INPUT);
  pinMode(d2pin, INPUT);
  pinMode(d3pin, INPUT);
  pinMode(armpin, INPUT);
  pinMode(slppin, INPUT);

  digitalWrite(ledpin1, LOW);
  digitalWrite(ledpin2, LOW);
  digitalWrite(ledpin3, LOW);
  digitalWrite(ledpin4, LOW);
  digitalWrite(ledpin5, LOW);
  digitalWrite(ledpin6, LOW);
  digitalWrite(ledpin7, LOW);
  digitalWrite(ledpin8, LOW);

  HardwareSerial* SerialTTL = &Serial4;
  HardwareSerial* SerialHeader = &Serial1;
  HardwareSerial* SerialModule = &Serial0;

  SerialTTL->begin(19200);
  SerialHeader->begin(19200);

  RC1780HP rc1780hp(SerialModule, cfgpin, rstpin, ctspin, rtspin);
  rc1780hp.begin(19200);

  digitalWrite(ledpin5, HIGH);                // LED 5: begin() complete
}

void loop()
{

}
