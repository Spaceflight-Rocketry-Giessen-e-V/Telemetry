#include "header.h"

/**
 * @defgroup groundstation Ground Station Firmware
 * @brief Functions and data structures used by the ground-station firmware.
 */

// LEDs states
#define SETUPBEGIN 1
#define SETUPRADIOMODULS 2
#define SETUPEND 3
#define RADIOMODUL_ONE 4
#define RADIOMODUL_TWO 5

class dataStruct;
class ledStruct;
class buttonStruct;

/**
 * @brief Configures both radio modules; lights each module's status LED on success and sounds buzzzer
 *
 * @param rc1780hp
 * @param rc1701hp
 * @param pinLed
 * @ingroup groundstation
 */
void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct *pinLed);

/**
 * @brief Function that reads the USB serial input.
 *
 * @param serialUSB
 * @return uint8_t
 * @ingroup groundstation
 */
uint8_t commandReceive(HardwareSerial *serialUSB);

/**
 * @brief Function to send the received command via USB.
 *
 * @param command
 * @param radioModule
 * @ingroup groundstation
 */
void commandExecute(RC17xxHP_RC232 *radioModule, uint8_t command, Packet *commandPacket);

/**
 * @brief Function that reads the received data from the Rocket and updates the data variables.
 *
 * @param radioModule
 * @param packetBuffer
 * @param packetBufferIndex
 * @param dataVariables
 * @return uint8_t
 * @ingroup groundstation
 */
uint8_t packetReceive(RC17xxHP_RC232 *radioModule, uint8_t *packetBuffer, uint8_t *packetBufferIndex, dataStruct *dataVariables, Packet *framePacket, Packet *flightDataPacket, Packet *telemetryDataPacket);

/**
 * @brief Serial output function via USB.
 *
 * @param serialUSB
 * @param dataVariables
 * @ingroup groundstation
 */
void dataSendUsb(HardwareSerial *serialUSB, dataStruct *dataVariables);

/**
 * @brief
 *
 * @param state
 * @param pinLed
 * @ingroup groundstation
 */
void ledUpdate(uint8_t state, ledStruct *pinLed);

/**
 * @brief Function to display the rssi level via a LED array.
 *
 * @param rssi
 * @param pinLed
 * @ingroup groundstation
 */
void ledRssiUpdate(float rssi, ledStruct *pinLed);

/**
 * @brief Function to display Vlaues on a external Display
 *
 * @param address
 * @param dataVariables
 *
 * @todo Has to be implemented in the future.
 * @ingroup groundstation
 */
void displayUpdate(uint8_t address, dataStruct *dataVariables);

/**
 * @brief Function to use buttons as an
 *
 * @param pinButton
 *
 * @todo Has to be implemented in the future.
 * @ingroup groundstation
 */
void buttonCheck(buttonStruct pinButton);

/**
 * @brief Function to connect to the control box.
 *
 * @param pin1
 * @param pin2
 *
 * @todo Has to be implemented in the future.
 * @ingroup groundstation
 */
void controlBoxCheck(uint8_t pin1, uint8_t pin2);

/**
 * @brief Stores the latest housekeeping, subsystem, flight, and telemetry data.
 * @ingroup groundstation
 */
class dataStruct // :)
{
public:
  // Housekeeping Data

  float rssi = 0;
  uint32_t timestampLastPacket = 0;
  uint32_t timeSinceLastPacket = 0;
  uint8_t command = 0;
  uint8_t packetIdentifier = 0;

  // Subsystem States

  uint8_t stateTelemetry = 0;
  uint8_t statePower = 0;
  uint8_t stateSens = 0;
  uint8_t stateControl = 0;

  // Flight Data

  float acceleration = 0;
  float heightPressure = 0;
  uint8_t flightEvents = 0;
  float latitude = 0;
  float longitude = 0;

  // Telemetry Data

  float heightGNSS = 0;
  uint8_t satCountGNSS = 0;
  float hdopGNSS = 0;
  uint8_t temperatureElectronics = 0;
  uint8_t temperatureBattery = 0;
  uint8_t stateCapacitors = 0;
  uint8_t continuityPyros = 0;
  uint8_t pressureDecoupler = 0;
  uint8_t ldrDecoupler = 0;
  float voltageBattery = 0;
  float currentBattery = 0;
  float currentUmbilical = 0;
  uint8_t stateUmbilical = 0;
  uint8_t lowPowerMode = 0;
  float voltageBatteryCOTS = 0;
};

/**
 * @brief Stores the debug and LED pins for.
 * @ingroup groundstation
 */
class ledStruct
{
public:
  uint8_t R;
  uint8_t G;
  uint8_t B;
  uint8_t D1;
  uint8_t D2;
  uint8_t D3;
  uint8_t rssi_1;
  uint8_t rssi_2;
  uint8_t rssi_3;
  uint8_t rssi_4;
  uint8_t rssi_5;
  uint8_t rssi_6;
  uint8_t rssi_7;
  uint8_t rssi_8;

  void pinMode();
};

/**
 * @brief Stores the pins for the control buttons.
 * @ingroup groundstation
 */
class buttonStruct // :)
{
public:
  uint8_t sw1;
  uint8_t sw2;
  uint8_t sw3;
  uint8_t sw4;
  uint8_t sw5;
  uint8_t sw6;

  void pinMode();
};
