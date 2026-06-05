#include "Arduino.h"
#include "utility.h"
#include "Radiocrafts_RC17xxHP_RC232.h"
#include "Packet.h"

uint8_t packetSendCheck(uint8_t *flightmode, uint8_t loopFrequency, uint8_t timeBetweenStandbyPackets, uint16_t loopCount)
{
  static uint16_t loopCountWhenFlightmodeStarts = 0;
  static uint8_t lastValueOfFlightmode = 0;

  if(*flightmode == 1 && lastValueOfFlightmode == 0 )
  {
    loopCountWhenFlightmodeStarts = loopCount;
  }  
  lastValueOfFlightmode = *flightmode;

  if(*flightmode == 1) 
  {

    if((loopCount - loopCountWhenFlightmodeStarts) / loopFrequency >= 360 - 3600 / timeBetweenStandbyPackets / loopFrequency)
    {
      *flightmode = 0;
      return 0;
    }
    
    if(loopCount % 10 == 0)
    {
      return 2;
    }
    else
    {
      return 1;
    }
  }
  else
  {
   
    if(loopCount % (uint16_t) timeBetweenStandbyPackets * loopFrequency == 0)
    {
     
      return (loopCount % 2) + 1;
    }
    else
    {
      return 0;
    }

  }
}  

void packetSend(RC17xxHP_RC232 *radioModule, dataStruct dataVariables, uint8_t packetIdentifier)
{
  if (packetIdentifier == 0)
  {
      return;
  }

  uint8_t packet[12] = { 0 };

  if (packetIdentifier == 1)
  {
      Packet::encodeFlightData(packet, dataVariables);
  }
  else if (packetIdentifier == 2)
  {
      Packet::encodeTelemetryData(packet, dataVariables);
  } 
  radioModule->send(packet, 12);
}
void loopVariablesUpdate(uint16_t* loopCount, uint32_t* loopStartTime, uint8_t loopFrequency, uint8_t pinLedLoop)
{
  *loopCount= *loopCount + 1;

  if (*loopCount % 2 == 1)
    digitalWrite(pinLedLoop,HIGH);

  else
    digitalWrite(pinLedLoop,LOW);

  delay(1000 / loopFrequency - (millis() - *loopStartTime));
  *loopStartTime = millis();
}

void ledUpdate(uint8_t state, ledStruct &pinLed)
{
  switch (state)
    {
      case SETUPBEGIN:

        digitalWrite(pinLed.B,LOW);
        digitalWrite(pinLed.G,LOW);
        digitalWrite(pinLed.R,HIGH);

        break;

      case SETUPRADIOMODULS:

        digitalWrite(pinLed.R,LOW);
        digitalWrite(pinLed.G,LOW);
        digitalWrite(pinLed.B,HIGH);

        break;

      case SETUPEND:

        digitalWrite(pinLed.R,LOW);
        digitalWrite(pinLed.B,LOW);
        digitalWrite(pinLed.G,HIGH);

        break;

      case RADIOMODUL_ONE:

        digitalWrite(pinLed.D2,HIGH);

        break;

      case RADIOMODUL_TWO:

        digitalWrite(pinLed.D3,HIGH);

        break;  

      default:

        break;
    }
}

void buzzerSound(uint8_t pinBuzzer)
{
  tone(pinBuzzer,1260,50);
}

void buzzerSoundError(uint8_t pinBuzzer)
{
  tone(pinBuzzer,1400,50);
  delay(20);
  tone(pinBuzzer,1400,50);
  delay(40);
  tone(pinBuzzer,1400,50);
  delay(20);
  tone(pinBuzzer,1400,50);
}

void ledStruct::pinMode()
{

  ::pinMode(R, OUTPUT);       digitalWrite(R, LOW);
  ::pinMode(G, OUTPUT);       digitalWrite(G, LOW);
  ::pinMode(B, OUTPUT);       digitalWrite(B, LOW);

  ::pinMode(D1, OUTPUT);      ::digitalWrite(D1, LOW);
  ::pinMode(D2, OUTPUT);      ::digitalWrite(D2, LOW);
  ::pinMode(D3, OUTPUT);      ::digitalWrite(D3, LOW);

  ::pinMode(Sens, OUTPUT);    ::digitalWrite(Sens, LOW);
  ::pinMode(Power, OUTPUT);   ::digitalWrite(Power, LOW);
  ::pinMode(Control, OUTPUT);    ::digitalWrite(Control, LOW);

  ::pinMode(Debug1, OUTPUT);    ::digitalWrite(Debug1, LOW);
  ::pinMode(Debug2, OUTPUT);    ::digitalWrite(Debug2, LOW);

}
