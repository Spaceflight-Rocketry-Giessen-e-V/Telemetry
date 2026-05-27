/*
    onboard - main.cpp of the board computer for the ASCENT III telemetry system.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Arduino.h"
#include "Wire.h"
#include "Radiocrafts_RC17xxHP_RC232.h"
#include "Packet.h"
#include "i2c_connectivity.h"
#include "utility.h"

int main(void)
{
  init();

  // Buzzersound On Bootup #1

  // Configuration Variables Declarations + Initialisations (Standby Packet Frequency, Loop Packet Frequency etc.)

  // Pin Declarations
  // Pin Initialisations
  // UART Declarations
  // I2C Declarations

  // Buzzersound On Bootup #2

  // Radiomodules Initialisations
  // Radiomodules Configurations

  // Buzzersound On Bootup #3
  
  // Data Arrays Preparations
  // Subsystems Initialisations

  // Buzzersound On Bootup #4

  // Loop Variables Declarations + Initialisations (Loop Count, Loop Start Time etc.)
  
  while(true)
  {
    // Subsystem Connection Check

    // Subsystem Data Request

    // Receiving Commands (Packet Library Function)
    // Execute Commands (Distribute Data To Subsystems etc.)

    // Sending Data (Telemetry Packet Or Sensorics Packet)
    // Save Data On Flash Chip

    // Delay
    // Update Loop Variables
  }

  return 0;
}