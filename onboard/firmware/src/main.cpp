/*
    onboard - main.cpp of the board computer for the ASCENT II telemetry system.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Arduino.h"
#include "Wire.h"
#include "Radiocrafts_RC17xxHP_RC232.h"
#include "Packet.h"

// Status events
// 0: 50 m
// 1: 100 m
// 2: 150 m
// 3: 200 m
// 4: Armed
// 5: Liftoff detected
// 6: Booster burnout detected
// 7: Drogue deployed (apogee)
// 8: Drogue deployed (timer)
// 9: Drogue deployed (command)
// 10: Main deployed (altitude)
// 11: Main deployed (timer)        // Not used
// 12: Main deployed (command)
// 13: Landing detected             // Not used

// Parity check
uint8_t incoming_data = 0;
uint8_t count = 0;

// Configuration
const uint8_t time_between_packets_standby = 15;                                              // in seconds   In standby, data packets are sent every 30 s   
const uint8_t hz = 8;                                                                         // in Hz        During flight, 8 Hz (125 ms interval)
const uint32_t flight_mode_max_duration = 360 - 3600 / time_between_packets_standby / hz;     // in seconds   6 min (360s) is max sending time

// Pin assignment
uint8_t ledpinR = PIN_PF0; // Red
uint8_t ledpinG = PIN_PE7; // Green
uint8_t ledpinB = PIN_PE6; // Blue
uint8_t ledpin1 = PIN_PF3; // Status
uint8_t ledpin2 = PIN_PF2; // Flight mode
uint8_t ledpin3 = PIN_PF1; // Not used so far
uint8_t ledpinDEBUG1 = PIN_PB6; // Not used so far
uint8_t ledpinDEBUG2 = PIN_PB7; // Not used so far
uint8_t ledpinSENS = PIN_PD4; // Sensor circuit board 1
uint8_t ledpinIGN = PIN_PD2; // Sensor circuit board 2
uint8_t ledpinPWR = PIN_PD3; // Landing systems, not used so far
uint8_t d4pin = PIN_PC6; // Not used so far
uint8_t d5pin = PIN_PC7; // Not used so far
uint8_t d26pin = PIN_PF4; // Not used so far
uint8_t d27pin = PIN_PF5; // Not used so far
uint8_t d28pin = PIN_PF6; // Not used so far
uint8_t arm1pin = PIN_PG1;
uint8_t slppin = PIN_PG0;

uint8_t buzzerpin = PIN_PB0; // Not used so far

uint8_t cfg1pin = PIN_PA5;
uint8_t rst1pin = PIN_PG7;
uint8_t cts1pin = PIN_PA3;
uint8_t rts1pin = PIN_PA4;

uint8_t cfg2pin = PIN_PB3; // Not used so far
uint8_t rst2pin = PIN_PG6; // Not used so far
uint8_t cts2pin = PIN_PB1; // Not used so far
uint8_t rts2pin = PIN_PB2; // Not used so far

HardwareSerial* SerialPC = &Serial4;
HardwareSerial* SerialUmbilical = &Serial1; // Not used so far
HardwareSerial* SerialModule1 = &Serial0;
HardwareSerial* SerialModule2 = &Serial3; // Not used so far

// Radio module initialisation
RC17xxHP_RC232 rc1780hp(SerialModule1, cfg1pin, rst1pin, cts1pin, rts1pin);

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
  pinMode(ledpinR, OUTPUT);
  pinMode(ledpinG, OUTPUT);
  pinMode(ledpinB, OUTPUT);
  pinMode(ledpin1, OUTPUT);
  pinMode(ledpin2, OUTPUT);
  pinMode(ledpin3, OUTPUT);
  pinMode(ledpinDEBUG1, OUTPUT);
  pinMode(ledpinDEBUG2, OUTPUT);
  pinMode(ledpinSENS, OUTPUT);
  pinMode(ledpinIGN, OUTPUT);
  pinMode(ledpinPWR, OUTPUT);
  pinMode(arm1pin, OUTPUT);
  pinMode(slppin, OUTPUT);

  // Only LED1 (power indicator) and RGB LED are turned on
  digitalWrite(ledpinR, HIGH);
  digitalWrite(ledpinG, LOW);
  digitalWrite(ledpinB, LOW);
  digitalWrite(ledpin1, HIGH);
  digitalWrite(ledpin2, LOW);
  digitalWrite(ledpin3, LOW);
  digitalWrite(ledpinDEBUG1, LOW);
  digitalWrite(ledpinDEBUG2, LOW);
  digitalWrite(ledpinSENS, LOW);
  digitalWrite(ledpinIGN, LOW);
  digitalWrite(ledpinPWR, HIGH);

  // Initialize UART
  //SerialPC->begin(115200);
  SerialPC->pins(PIN_PE4, PIN_PE5);// Swap RX/TX pins for radio module uart connection
  SerialUmbilical->pins(PIN_PE4, PIN_PE5);// Swap RX/TX pins for radio module uart connection
  SerialModule1->pins(PIN_PA0, PIN_PA1);// Swap RX/TX pins for radio module uart connection
  SerialModule2->pins(PIN_PC0, PIN_PC1);// Swap RX/TX pins for radio module uart connection
 
  // Initialize I2C
  Wire.pins(PIN_PC2, PIN_PC3);
  Wire.begin();
  
  // Initialize radio transceiver and wait until communication is established
  delay(3.2 * 50); // Necessary delay: t_{OFF-IDLE} = 3.2, safety factor 10
  rc1780hp.begin(19200);
  delay(3.2 * 50); // Necessary delay: t_{OFF-IDLE} = 3.2, safety factor 10
  rc1780hp.ping();

  digitalWrite(ledpinG, HIGH);

  // Before each flight memory is reset and non-standard settings are reconfigured
  //while(rc1780hp.memory_Reset() != 0);
  while(rc1780hp.set_RF_DATA_RATE(0x05) != 0);
  while(rc1780hp.set_PACKET_TIMEOUT(0x00) != 0);
  while(rc1780hp.set_PACKET_END_CHARACTER(0xEE) != 0);
  while(rc1780hp.set_ADDRESS_MODE(0x00) != 0);
  while(rc1780hp.set_CRC_MODE(0x00) != 0);
  while(rc1780hp.set_LED_CONTROL(0x01) != 0);
  rc1780hp.hard_Reset();
  rc1780hp.serial_Flush();
}

uint32_t loop_start_time;
uint8_t loop_count = 0;
uint8_t led_switch = 0;
uint32_t flight_mode_start_time;

void loop()
{
  loop_start_time = millis();

  // Check for incoming data from groundstation
  if(SerialModule1->available() != 0)
  {
    // Parity check
    incoming_data = SerialModule1->read();
    for (int z = 0; z < 8; z++) 
    {
        if (incoming_data & (1 << z))
        {
            count++;
        }
    }
    if (count % 2 == 0)
    {
        incoming_data &= 0x7F;
    }
    count = 0;

    // Process incoming serial commands from the groundstation
    // The command reference can be found under docs/commands.md
    switch (incoming_data)
    {
      // Flight computer ping

      case 'p':
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
          digitalWrite(ledpin2, LOW); 
          digitalWrite(ledpinSENS, LOW); 
          digitalWrite(ledpinIGN, LOW); 
          digitalWrite(ledpinPWR, LOW); 
          low_power_mode = 1;
        }
        break;
      
      case 'm': // deactivation
        if(low_power_mode == 1)
        {
          digitalWrite(slppin, LOW);
          low_power_mode = 0;
        }
        break;
      
      // Flight mode 

      case 'f': // activation
        if(flight_mode == 0)
        {
          digitalWrite(arm1pin, HIGH);
          // delay(1);
          //if(digitalRead(d3pin) == HIGH)  This connection is not planned anymore??
          // {
            digitalWrite(ledpin2, HIGH);
            flight_mode_start_time = millis();
            flight_mode = 1;
            Wire.beginTransmission(0x40);
            Wire.write('f');
            Wire.endTransmission();
          // }
          // else
          // {
          //   digitalWrite(arm1pin, LOW);
          // }
        }
        break;
      #if(0)
      case 'g': // deactivation
        if(flight_mode == 1)
        {
          digitalWrite(arm1pin, LOW);
          delay(1);
          if(digitalRead(d3pin) == LOW)
          {
            digitalWrite(ledpin2, LOW);
            flight_mode = 0;
            Wire.beginTransmission(0x40);
            Wire.write('g');
            Wire.endTransmission();
          }
          else
          {
            digitalWrite(arm1pin, HIGH);
          }
        }
        break;
#endif

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
    
    send_packet();
  }

  // Update variables from i2c connected systems at the beginning of each cycle
  get_packet_data();

  // Check if the other boards are connected and ready (When a system is connected or ready, a 1 is written to the respective position. E.g. 0b111 then means that all are connected)
  if(low_power_mode == 0)
  {
    if(flight_mode == 1)
    {
      digitalWrite(ledpin2, HIGH);
    }
    else
    {
      digitalWrite(ledpin2, LOW);
    }

    digitalWrite(ledpin1, 1 - led_switch);

    // Sensor circuit board 1
    if((i2c_connections & 0b001) != 0)
    {
      if((subsystem_status & 0b001) != 0)
      {
        digitalWrite(ledpinSENS, HIGH);
      }
      else
      {
        digitalWrite(ledpinSENS, led_switch);
      }
    }
    else
    {
      digitalWrite(ledpinSENS, LOW);
    }

    // Sensor circuit board 2
    if((i2c_connections & 0b010) != 0)
    {
      if((subsystem_status & 0b010) != 0)
      {
        digitalWrite(ledpinIGN, HIGH);
      }
      else
      {
        digitalWrite(ledpinIGN, led_switch);
      }
    }
    else
    {
      digitalWrite(ledpinIGN, LOW);
    }

    // POWER UNIT (no microcontroller yet)
    digitalWrite(ledpinPWR, HIGH);

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
    // Else
    else
    {
      digitalWrite(ledpinR, HIGH);
      digitalWrite(ledpinG, LOW);
      digitalWrite(ledpinB, LOW);
    }

    led_switch = 1 - led_switch;
  }

  // Send data to groundstation
  if(flight_mode == 1)
  {
    if(millis() - flight_mode_start_time > flight_mode_max_duration * 1000) // If the maximum legal transmission time is reached, the flight mode must be turned off
    {
      flight_mode = 0;
    }
    send_packet();
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
  // battery_voltage = (float)analogRead(d2pin) / 1023 * 3.3 * (18 + 10) / 10; Will not be used anymore due to power unit doing the measurement
  battery_voltage = 0;

  // Temperature
  // rc1780hp.read_Temperature(&temperature);
}

// Encodes current data into 15-Byte packet and transmits it
void send_packet()
{
  uint8_t packet[15] = { 0 };
  Packet::encode(packet, (float)temperature, subsystem_status, flight_mode, low_power_mode, status_events, acceleration, height_pressure, height_gnss, lat_gnss, lon_gnss, battery_voltage);
  SerialModule1->write(packet, 15);
}