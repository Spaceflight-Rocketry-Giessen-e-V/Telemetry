/*
    groundstation - main.cpp of the groundstation for the ASCENT III telemetry system.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Arduino.h"
#include "Radiocrafts_RC17xxHP_RC232.h"
#include "Packet.h"
#include "utility.h"

int main(void)
{
  init();

  // Use RSSI LEDs As Setup Progress Indication

  // Configuration Variables Declarations + Initialisations

  // Pin Declarations
  // Pin Initialisations
  // UART Declarations

  // Radiomodules Initialisations
  // Radiomodules Configurations
  
  // Data Arrays Preparations
  
  while(true)
  {
    // Receiving Commands
    // Process Commands (Execute Or Encode With Packet Library)
    // Send Commands
    
    // Check Buttons
    // Check DSUB-9 Connector

    // Receiving Data Packets
    // Decode Data Packets (With Packet Library)
    // Send Data To Computer

    // Update LEDs
    // Update Display
  }

  return 0;
}