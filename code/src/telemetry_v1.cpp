#include <Arduino.h>

//Pin allocation
int ledpin1 = PIN_PD3;
int ledpin2 = 1;
int ledpin3 = 2;
int ledpin4 = 13;
int rstpin = 3;
int cfgpin = PIN_PD6;
int rtspin = 5;

int serial_pc_wait(uint32_t delay_microsec);
int serial_rf_wait(uint32_t delay_microsec);

void setup()
{
  //Pin initialisation
  {
    pinMode(ledpin1, OUTPUT);
    // pinMode(ledpin2, OUTPUT);
    // pinMode(ledpin3, OUTPUT);
    // pinMode(ledpin4, OUTPUT);
    // pinMode(rstpin, OUTPUT);
    pinMode(cfgpin, OUTPUT);
    // pinMode(rtspin, OUTPUT);
  }
  
  //Pin standard mode
  {
    // digitalWrite(rstpin, HIGH);
    digitalWrite(cfgpin, HIGH);
    // digitalWrite(rtspin, HIGH);
    
    digitalWrite(ledpin1, HIGH);
    // digitalWrite(ledpin2, LOW);
    // digitalWrite(ledpin3, LOW);
    // digitalWrite(ledpin4, HIGH);
  }

  //Serial configuration
  {
    Serial2.begin(19200);
    //Serial0.setRX(7);
    Serial0.begin(19200);
  }
  
  //Waiting for first user input
  {
    while(Serial2.available() == 0);
    Serial2.read();
    Serial2.print("Setup complete. Entering normal operation mode. | ");
  }
}

void loop()
{
  // [1xxx] Serial from module
  if(Serial0.available() != 0)
  {
    while(serial_rf_wait(600) != 0)
    {
      Serial2.write(Serial0.read());
    }
    Serial2.write('\n');
  }

  // [2xxx] Serial from user
  if(Serial2.available() != 0)
  {
    char inByte = Serial2.read();

    // [21xx] Sending mode
    if(inByte == 's' || inByte == 'S')
    {
      Serial2.print("Entered sending mode. Enter the string to be transmitted. ");
      char inBuffer[129] = {0};
      while(Serial2.available() == 0);
      while(Serial2.available() != 0)
      {
        int i = 0;
        for(i = 0; i < 128 && serial_pc_wait(600); i++)
        {
          inBuffer[i] = Serial2.read();
        }
        Serial2.print("Successfully transmitted ");
        for(int j = 0; j < i; j++)
        {
          Serial0.write(inBuffer[j]);
          Serial2.write(inBuffer[j]);
        }
        Serial2.print(". ");
        delay(20);
      }
      Serial2.print("Sending complete. Entering normal operation mode. | ");
    }

    // [22xx] Configuration mode
    else if(inByte == 'c' || inByte == 'C')
    {
      digitalWrite(cfgpin, LOW);
      serial_rf_wait(5000);
      digitalWrite(cfgpin, HIGH);
      //Check for regular feedback from module
      if(Serial0.available() == 1 && Serial0.read() == '>')
      {
        Serial2.print("Entered configuration mode. Enter the desired command. Enter X to exit. ");
        Serial2.write('>');
        //Entering communication loop
        while(true)
        {
          //Waiting for user input
          while(Serial2.available() == 0);
          Serial0.write(Serial2.read());

          //Waiting for module response
          serial_rf_wait(5000);
          if(Serial0.available() == 0)
          {
            break;
          }
          else
          {
            while(serial_rf_wait(5000) != 0)
            {
              Serial2.write(Serial0.read());
            }
          }
        }
        Serial2.print("Configuration finished. Entering normal operation mode. | ");
      }
      else
      {
        Serial0.write('X');
        Serial2.print("Error 2201 (received either no or irregular response from module). Entering normal operation mode. | ");
      }
    }

    // [23xx] Command mode
    else if(inByte == 'b' || inByte == 'B')
    {
      Serial2.print("Entered command mode. Enter M for memory reset, N for memory configuration, R for reset, S for RSSI reading, U for temperature reading, V for voltage reading, Z for sleep mode and 0 for non-volatile memory reading. Enter X to Exit. | ");
      while(!Serial2.available());
      inByte = Serial2.read();

      // [231x] Exit command mode
      if(inByte == 'x' || inByte == 'X')
      {
        Serial2.print("Entering normal operation mode. | ");
      }

      // [232x] Memory reset
      else if(inByte == 'm' || inByte == 'M')
      {
        digitalWrite(cfgpin, LOW);
        serial_rf_wait(5000);
        //Check for feedback from module
        if(Serial0.available() == 1 && Serial0.read() == '>')
        {
          Serial0.print("@RC");
          serial_rf_wait(50000);
          if(Serial0.available() == 1 && Serial0.read() == '>')
          {
            Serial2.print("Memory reset complete. Entering normal operation mode. | ");
          }
          else
          {
            Serial2.print("Error 2322 (received either no or irregular response from module). Entering normal operation mode. | ");
          }
        }
        else
        {
          Serial2.print("Error 2321 (received either no or irregular response from module). Entering normal operation mode. | ");
        }
        digitalWrite(cfgpin, HIGH);
        delay(500);
        Serial0.write('X');
      }

      // [233x] Memory configuration
      else if(inByte == 'n' || inByte == 'N')
      {
        digitalWrite(cfgpin, LOW);
        serial_rf_wait(5000);
        digitalWrite(cfgpin, HIGH);
        //Check for feedback from module
        if(Serial0.available() == 1 && Serial0.read() == '>')
        {
          Serial0.write('M');
          serial_rf_wait(5000);
          if(Serial0.available() == 1 && Serial0.read() == '>')
          {
            Serial2.print("Entered memory configuration. Enter the desired address. Enter X to exit. ");
            if(serial_pc_wait(20000000) != 0)
            {
              inByte = Serial2.read();
              if(inByte == 'X')
              {
                Serial2.print("Exiting memory configuration. Entering normal operation mode. | ");
              }
              else if(inByte <= 0x35)
              {
                Serial0.write(inByte);
                Serial2.print("Enter the desired value. ");
                if(serial_pc_wait(20000000) != 0)
                {
                  inByte = Serial2.read();
                  if(inByte <= 0x35)
                  {
                    Serial0.write(inByte);
                    Serial2.print("Finished memory configuration. Entering normal operation mode. | ");
                  }
                  else 
                  {
                    Serial2.print("Error 2334 (received irregular input from user). Entering normal operation mode. | ");
                  }
                }
              }
              else
              {
                Serial2.print("Error 2333 (received irregular input from user). Entering normal operation mode. | ");
              }
            }
            Serial0.write(0xFF);
            while(Serial0.available())
            {
              Serial0.read();
            }
          }
          else
          {
            Serial2.print("Error 2332 (received either no or irregular response from module). Entering normal operation mode. | ");
          }
        }
        else
        {
          Serial2.print("Error 2331 (received either no or irregular response from module). Entering normal operation mode. | ");
        }
        Serial0.write('X');
      }

      // [234x] Reset
      else if(inByte == 'r' || inByte == 'R')
      {
        digitalWrite(rstpin, LOW);
        delay(50);
        digitalWrite(rstpin, HIGH);
        delay(50);
        Serial2.print("Reset complete. Entering normal operation mode. | ");
      }

      // [235x] RSSI reading
      else if(inByte == 's' || inByte == 'S')
      {
        digitalWrite(cfgpin, LOW);
        serial_rf_wait(5000);
        digitalWrite(cfgpin, HIGH);
        //Check for feedback from module
        if(Serial0.available() == 1 && Serial0.read() == '>')
        {
          Serial0.print('S');
          serial_rf_wait(5000);
          if(Serial0.available() != 0)
          {
            inByte = Serial0.read();
            Serial2.print("RSSI-Reading:");
            Serial2.write(inByte);
            Serial2.print(" Signal Strength:");
            Serial2.print((double)((unsigned char)inByte) * -0.5, DEC);
            Serial2.print(" RSSI-Reading finished. Entering normal operation mode. | ");
          }
          else
          {
            Serial2.print("\nError 2352 (received no response from module). Entering normal operation mode. | ");
          }
        }
        else
        {
            Serial2.print("Error 2351 (received either no or irregular response from module). Entering normal operation mode. | ");
        }
        Serial0.write('X');
      }

      // [236x] Temperature reading
      else if(inByte == 'u' || inByte == 'U')
      {
        digitalWrite(cfgpin, LOW);
        serial_rf_wait(5000);
        digitalWrite(cfgpin, HIGH);
        //Check for feedback from module
        if(Serial0.available() == 1 && Serial0.read() == '>')
        {
          Serial0.print('U');
          serial_rf_wait(5000);
          if(Serial0.available() != 0)
          {
            inByte = Serial0.read();
            Serial2.print("TEMP-Reading:");
            Serial2.write(inByte);
            Serial2.print(" Temperature:");
            Serial2.print((unsigned char)inByte - 128, DEC);
            while(Serial0.available())
            {
              Serial0.read();
            }
            Serial2.print(" Temperature-Reading finished. Entering normal operation mode. | ");
          }
          else
          {
            Serial2.print("Error 2362 (received no response from module). Entering normal operation mode. | ");
          }
        }
        else
        {
            Serial2.print("Error 2361 (received either no or irregular response from module). Entering normal operation mode. | ");
        }
        Serial0.write('X');
      }

      // [237x] Voltage reading
      else if(inByte == 'v' || inByte == 'V')
      {
        digitalWrite(cfgpin, LOW);
        serial_rf_wait(5000);
        digitalWrite(cfgpin, HIGH);
        //Check for feedback from module
        if(Serial0.available() == 1 && Serial0.read() == '>')
        {
          Serial0.print('V');
          serial_rf_wait(5000);
          if(Serial0.available() != 0)
          {
            inByte = Serial0.read();
            Serial2.print("VCC-Reading:");
            Serial2.print(inByte);
            Serial2.print(" Voltage:");
            Serial2.print((double)inByte * 0.03, DEC);
            while(Serial0.available())
            {
              Serial0.read();
            }
            Serial2.print(" Voltage-Reading finished. Entering normal operation mode. | ");
          }
          else
          {
            Serial2.print("Error 2372 (received no response from module). Entering normal operation mode. | ");
          }
        }
        else
        {
            Serial2.print("Error 2371 (received either no or irregular response from module). Entering normal operation mode. | ");
        }
        Serial0.write('X');
      }

      // [238x] Sleep mode
      else if(inByte == 's' || inByte == 'S')
      {
        digitalWrite(rtspin, LOW);
        Serial2.print("Entered sleep mode. Press any character to exit. ");
        while(!Serial2.available());
        Serial2.read();
        digitalWrite(rtspin, HIGH);
        Serial2.print("Exited sleep mode. Entering normal operation mode. | ");
      }

      // [239x] Non-volatile memory reading
      else if(inByte == '0')
      {
        digitalWrite(cfgpin, LOW);
        serial_rf_wait(5000);
        digitalWrite(cfgpin, HIGH);
        //Check for feedback from module
        Serial2.write(Serial0.available());
        if(Serial0.available() == 1 && Serial0.read() == '>')
        {
          Serial0.write('0');
          serial_rf_wait(5000);
          if(Serial0.available() != 0)
          {
            char inBuffer[129] = {0};
            for(int i = 0; serial_rf_wait(5000) != 0; i++)
            {
              inBuffer[i] = Serial0.read();
            }
            Serial2.print(" (0x00) RF Channel [4,0x04]:");
            Serial2.write(inBuffer[0x00]);
            Serial2.print(" (0x01) RF Power [5,0x05]:");
            Serial2.write(inBuffer[0x01]);
            Serial2.print(" (0x02) RF Data rate [3,0x03]:");
            Serial2.write(inBuffer[0x02]);
            Serial2.print(" (0x04) SLEEP Mode [0,0x00]:");
            Serial2.write(inBuffer[0x04]);
            Serial2.print(" (0x05) RSSI Mode [0,0x00]:");
            Serial2.write(inBuffer[0x05]);
            Serial2.print(" (0x0E) Packet length high [0,0x00]:");
            Serial2.write(inBuffer[0x0E]);
            Serial2.print(" (0x0F) Packet length low [128,0x80]:");
            Serial2.write(inBuffer[0x0F]);
            Serial2.print(" (0x10) Packet timeout [124,0x7C]:");
            Serial2.write(inBuffer[0x10]);
            Serial2.print(" (0x11) Packet end character [0,0x00]:");
            Serial2.write(inBuffer[0x11]);
            Serial2.print(" (0x14) Address mode [2,0x02]:");
            Serial2.write(inBuffer[0x14]);
            Serial2.print(" (0x15) CRC mode [2,0x02]:");
            Serial2.write(inBuffer[0x15]);
            Serial2.print(" (0x19) Unique ID 1 [1,0x01]:");
            Serial2.write(inBuffer[0x19]);
            Serial2.print(" (0x1B) Unique ID 2 [1,0x01]:");
            Serial2.write(inBuffer[0x1B]);
            Serial2.print(" (0x1D) Unique ID 3 [1,0x01]:");
            Serial2.write(inBuffer[0x1D]);
            Serial2.print(" (0x1F) Unique ID 4 [1,0x01]:");
            Serial2.write(inBuffer[0x1F]);
            Serial2.print(" (0x1A) System ID 1 [1,0x01]:");
            Serial2.write(inBuffer[0x1A]);
            Serial2.print(" (0x1C) System ID 2 [1,0x01]:");
            Serial2.write(inBuffer[0x1C]);
            Serial2.print(" (0x1E) System ID 3 [1,0x01]:");
            Serial2.write(inBuffer[0x1E]);
            Serial2.print(" (0x20) System ID 4 [1,0x01]:");
            Serial2.write(inBuffer[0x20]);
            Serial2.print(" (0x21) Destination ID 1 [1,0x01]:");
            Serial2.write(inBuffer[0x21]);
            Serial2.print(" (0x22) Destination ID 2 [1,0x01]:");
            Serial2.write(inBuffer[0x22]);
            Serial2.print(" (0x23) Destination ID 3 [1,0x01]:");
            Serial2.write(inBuffer[0x23]);
            Serial2.print(" (0x24) Destination ID 4 [1,0x01]:");
            Serial2.write(inBuffer[0x24]);
            Serial2.print(" (0x28) Broadcast address [255,0xFF]:");
            Serial2.write(inBuffer[0x28]);
            Serial2.print(" (0x30) UART baud rate [5,0x05]:");
            Serial2.write(inBuffer[0x30]);
            Serial2.print(" (0x31) UART number of bits [8,0x08]:");
            Serial2.write(inBuffer[0x31]);
            Serial2.print(" (0x32) UART parity [0,0x00]:");
            Serial2.write(inBuffer[0x32]);
            Serial2.print(" (0x33) UART stop bits [1,0x01]:");
            Serial2.write(inBuffer[0x33]);
            Serial2.print(" (0x35) UART flow control [0,0x00]:");
            Serial2.write(inBuffer[0x35]);
            Serial2.print(" (0x3C - 0x49) Part number:");
            for(int i = 0x3C; i <= 0x49; i++)
            {
              Serial2.write(inBuffer[i]);
            }
            Serial2.print(" (0x4B - 0x4E) Hardware revision number:");
            for(int i = 0x4B; i <= 0x4E; i++)
            {
              Serial2.write(inBuffer[i]);
            }
            Serial2.print(" (0x50 - 0x53) Software revision number:");
            for(int i = 0x50; i <= 0x53; i++)
            {
              Serial2.write(inBuffer[i]);
            }
            Serial2.print(" Finished. Returning to normal operation mode. | ");
          }
          else
          {
            Serial2.print("Error 2392 (received no response from module). Entering normal operation mode. | ");
          }
        }
        else
        {
            Serial2.print("Error 2391 (received either no or irregular response from module). Entering normal operation mode. | ");
        }
        Serial0.write('X');
      }

      // [230x] Wrong input
      else
      {
        Serial2.print("Error 2301 (received irregular input from user). Entering normal operation mode. | ");
      }
    }

    // [20xx] Wrong input
    else
    {
      Serial2.print("Error 2001 (received irregular input from user). Entering normal operation mode. | ");
    }
  }
}

//Waiting whether Serial2.available() == true in given time
int serial_pc_wait(uint32_t delay_microsec)
{
  for(uint32_t i = 0; i < (delay_microsec / 10) && Serial2.available() == 0; i++)
  {
    delayMicroseconds(10);
  }
  return Serial2.available();
}

//Waiting whether Serial0.available() == true in given time
int serial_rf_wait(uint32_t delay_microsec)
{
  for(uint32_t i = 0; i < (delay_microsec / 10) && Serial0.available() == 0; i++)
  {
    delayMicroseconds(10);
  }
  return Serial0.available();
}