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

