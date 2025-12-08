/*
    groundstation - main.cpp of the groundstation for the ASCENT II telemetry system.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Arduino.h"
#include "RC1780HP.h"
#include "Packet.h"

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

RC1780HP rc1780hp(SerialModule, cfgpin, rstpin, ctspin, rtspin);

// Data components received from sensors
uint8_t temperature = 0;
uint8_t subsystem_status = 0;
uint8_t flight_mode = 0;
uint8_t low_power_mode = 0;
uint8_t status_events = 0;
uint8_t send;
float height_pressure = 0;
float height_gnss = 0;
float lat_gnss = 0;
float lon_gnss = 0;
float acceleration = 0;
float battery_voltage = 0;
float rssi = 0;
uint32_t packet_time = 0;
uint32_t time_since_last_packet = 0;

// Incoming Data
uint8_t packet[16] = {0};
uint8_t incoming_Byte = 0;
uint8_t index = 0;

void setup()
{
  pinMode(ledpin1, OUTPUT); // Power on
  pinMode(ledpinR, OUTPUT); // Red
  pinMode(ledpinG, OUTPUT); // Green
  pinMode(ledpinB, OUTPUT); // Blue
  pinMode(ledpin5, OUTPUT); // Flight mode
  pinMode(ledpin6, OUTPUT); // Low-power-mode
  pinMode(ledpin7, OUTPUT); // Subsystem status
  pinMode(ledpin8, OUTPUT); // Battery voltage
  pinMode(d1pin, INPUT);
  pinMode(d2pin, INPUT);
  pinMode(d3pin, INPUT);
  pinMode(armpin, OUTPUT);
  pinMode(slppin, OUTPUT);

  // Only RGB LED is turned on
  digitalWrite(ledpin1, LOW);
  digitalWrite(ledpinR, HIGH);
  digitalWrite(ledpinG, HIGH);
  digitalWrite(ledpinB, HIGH);
  digitalWrite(ledpin5, LOW);
  digitalWrite(ledpin6, LOW);
  digitalWrite(ledpin7, LOW);
  digitalWrite(ledpin8, LOW);

  SerialPC1->begin(115200);// Connection to PC
  // SerialPC2->begin(19200);
  SerialModule->swap(1);// Swap RX/TX pins for module
  delay(100);
  rc1780hp.begin(19200);
  delay(100);
  rc1780hp.ping();
  
  rc1780hp.memory_Reset();
  while(rc1780hp.set_RF_DATA_RATE(0x05) != 0);
  while(rc1780hp.set_RSSI_Mode(0x01) != 0);
  while(rc1780hp.set_Packet_Timeout(0x00) != 0);
  while(rc1780hp.set_Packet_Length(0x01) != 0);
  while(rc1780hp.set_Address_Mode(0x00) != 0);
  while(rc1780hp.set_CRC_Mode(0x00) != 0);
  while(rc1780hp.set_LED_Control(0x01) != 0);

  rc1780hp.hard_reset();
  rc1780hp.serial_Flush();

  digitalWrite(ledpinR, LOW);
  digitalWrite(ledpinG, LOW);
  digitalWrite(ledpinB, LOW);
  digitalWrite(ledpin1, HIGH);
}

void loop()
{
  // Send data to rocket
  if(SerialPC1->available() != 0)
  { 
    send = SerialPC1->read(); 

    // Conversion of capital letters in lowercase letters
    if(send >= 'A' && send <= 'Z')
    {
      send = send - 'A' + 'a';
    }

    // Spam some parameters (to guarantee exchange during flight mode)
    if(send == 'p' || send == 'f' || send == 'a' || send == 'b' || send == 'c' || send == 'd')
    {
       SerialModule->write(send); 
    }
    else
    {
      for(int i = 0; i < 20; i++)
      {
        delay(5);
      
        SerialModule->write(send); 
      }
    }
  }

  while(SerialModule->available() != 0)
  {
    incoming_Byte = SerialModule->read();
    packet[index] = incoming_Byte;
    index++;

    if(packet[index- 2] == 0xEE)
    {
      Packet::decode(&packet[index - 16], &temperature, &subsystem_status, &flight_mode, &low_power_mode, &status_events, &acceleration, &height_pressure, &height_gnss, &lat_gnss, &lon_gnss, &battery_voltage, &rssi);
      
      SerialPC1->print("\ntemperature > 80 C: ");     SerialPC1->println(temperature);
      SerialPC1->print("subsystem_status: ");         SerialPC1->println(subsystem_status);
      SerialPC1->print("flight_mode: ");              SerialPC1->println(flight_mode);
      SerialPC1->print("low_power_mode: ");           SerialPC1->println(low_power_mode);
      SerialPC1->print("status_events: ");            SerialPC1->println(status_events);
      SerialPC1->print("acceleration: ");             SerialPC1->println(acceleration,4);
      SerialPC1->print("height_pressure: ");          SerialPC1->println(height_pressure);
      SerialPC1->print("height_gnss: ");              SerialPC1->println(height_gnss);
      SerialPC1->print("lat_gnss: ");                 SerialPC1->println(lat_gnss,7);
      SerialPC1->print("lon_gnss: ");                 SerialPC1->println(lon_gnss,7);
      SerialPC1->print("battery_voltage: ");          SerialPC1->println(battery_voltage);
      SerialPC1->print("rssi: ");                     SerialPC1->println(rssi);
      SerialPC1->print("time_since_last_packet: ");   SerialPC1->println(millis() - time_since_last_packet);

      index = 0;
      memset(packet, 0, sizeof(packet));
  
      time_since_last_packet = millis();
    }
  }
 
  // LED5 glows wenn flight-mode is active
  if(flight_mode == 1)
  {
    digitalWrite(ledpin5, HIGH);
  }
  else
  {
    digitalWrite(ledpin5, LOW);
  }

  // LED6 glows wenn low-power-mode is active
  if(low_power_mode == 1)
  {
    digitalWrite(ledpin6, HIGH);
  }
  else
  {
    digitalWrite(ledpin6, LOW);
  }

  // LED7 glows wenn subsystems are ready
  if(subsystem_status == 0b111)
  {
    digitalWrite(ledpin7, HIGH);
  }
  else
  {
    digitalWrite(ledpin7, LOW);
  }

  // LED8 glows until battery-voltage gets lower than 6.0V
  if(battery_voltage > 6.0)
  {
    digitalWrite(ledpin8, HIGH);
  }
  else
  {
    digitalWrite(ledpin8, LOW);
  }
  
  // RGB LED (RSSI)
  if(rssi > -50 )// High signal strength --> LED glows green
  {
    digitalWrite(ledpinG, HIGH);
    digitalWrite(ledpinB, LOW);
    digitalWrite(ledpinR, LOW);
  }

  else if(rssi > -80)// Medium signal strength --> LED glows blue
  {
    digitalWrite(ledpinG, LOW);
    digitalWrite(ledpinB, HIGH);
    digitalWrite(ledpinR, LOW); 
  }

  else // Low signal strength --> LED glows red
  {
    digitalWrite(ledpinG, LOW);
    digitalWrite(ledpinB, LOW);
    digitalWrite(ledpinR, HIGH);
  }
}