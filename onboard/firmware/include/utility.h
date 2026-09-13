#include "header.h"
#include "i2c_connectivity.h"

/**
 * @defgroup onboard Onboard Firmware
 * @brief Functions and data structures used by the onboard firmware.
 */
// LEDs states
#define SETUPBEGIN 1
#define SETUPRADIOMODULS 2
#define SETUPEND 3
#define RADIOMODUL_ONE 4
#define RADIOMODUL_TWO 5
#define UPDATE 255

class ledStruct;
class dataStruct;

/**
 * @brief Function to play a sound when the setup is completed.
 *
 * @param pinBuzzer
 * @ingroup onboard
 */
void buzzerSound(uint8_t pinBuzzer);

/**
 * @brief Function to play a sound according to a error during setup.
 *
 * @param pinBuzzer
 * @ingroup onboard
 */
void buzzerSoundError(uint8_t pinBuzzer);

/**
 * @brief Configures both radio modules; lights each module's status LED on success and sounds buzzzer
 *
 * @param rc1780hp
 * @param rc1701hp
 * @param pinLed
 * @param pinBuzzer
 * @ingroup onboard
 */
void radioModulesSetup(RC17xxHP_RC232 *rc1780hp, RC17xxHP_RC232 *rc1701hp, ledStruct *pinLed, uint8_t pinBuzzer); // Wenn Error: buzzerSoundError();
// ledUpdate aufrufen: ledUpdate(4): radiomodul 1 funktioniert: D2 anschalten,
// ledUpdate(5): radiomodul 2 funktioniert: D3 anschalten

/**
 * @brief Returns the latest single-byte command from the uplink module (rc1701hp, on Serial3), or 0 if command is bad/unknown
 *
 * @param radioModule
 * @return uint8_t
 * @ingroup onboard
 */
void commandReceive(RC17xxHP_RC232 *radioModule, Packet *commandPacket); // Aufruf Packet Library Function, return 0
                                                     // wenn kein Command, sonst return command

/**
 * @brief Changes the values of the loop variables and therefore the state of flight computer.
 *
 * @param command
 * @param radioModule
 * @param dataVariables
 * @param pinLed
 * @param flightMode
 * @param subsystemsList
 * @param subsystemsCount
 * @param subsystemSens
 * @param subsystemControl
 * @param pinArm
 * @param pinSleep
 * @ingroup onboard
 */
void commandExecute(uint8_t command, RC17xxHP_RC232 *radioModule, dataStruct *dataVariables, ledStruct *pinLed, uint8_t *flightMode, Subsystem **subsystemsList, uint8_t subsystemsCount, Subsystem *subsystemSens, Subsystem *subsystemControl, Packet *flightDataPacket, Packet *telemetryDataPacket, uint8_t pinArm, uint8_t pinSleep); //  Distribute Data To Subsystems etc..
                                                                                                                                                                                                                                                                                    //  Check for 0 (-> no command)

/**
 * @brief Function that handle the decision of sending a package depending on the timeBetweenStandbyPackets. In addition handles the decision of sending either the telemetry or flight package.
 *
 * @param flightmode
 * @param loopFrequency
 * @param timeBetweenStandbyPackets
 * @param loopCount
 * @return uint8_t
 * @ingroup onboard
 */
uint8_t packetSendCheck(uint8_t *flightmode, uint8_t loopFrequency, uint8_t timeBetweenStandbyPackets, uint32_t loopCount);

/**
 * @brief Function to build up the package depending on an identifyer.
 *
 * @param radioModule
 * @param dataVariables
 * @param pinLed
 * @param packetIdentifier
 * @ingroup onboard
 */
void packetSend(RC17xxHP_RC232 *radioModule, uint8_t packetType, Packet *flightDataPacket, Packet *telemetryDataPacket);

/**
 * @brief Function to write to the onbaord flash. f
 *
 * @param dataVariables
 * @ingroup onboard
 */
void flashWrite(dataStruct *dataVariables);

/**
 * @brief Function that update the loop variables.
 *
 * @param loopCount
 * @param loopStartTime
 * @param loopFrequency
 * @param pinLedLoop
 * @ingroup onboard
 */
void loopVariablesUpdate(uint32_t *loopCount, uint32_t *loopStartTime, uint8_t loopFrequency, uint8_t pinLedLoop);

/**
 * @brief Function to update LEDs to display different states of the system.
 *
 * @param state
 * @param pinLed
 * @ingroup onboard
 */
void ledUpdate(uint8_t state, ledStruct *pinLed); // Switch Case

/**
 * @brief Class for all LEDs
 *
 * @ingroup onboard
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
  uint8_t Debug1;
  uint8_t Debug2;
  uint8_t Power;
  uint8_t Sens;
  uint8_t Control;
  uint8_t *lowPowerMode;
  void pinMode();
};

/**
 * @brief Class for the telemetry and flight data
 *
 * @ingroup onboard
 */
class dataStruct // :)
{
public:

  uint8_t command;

  // Subsystem States

  uint8_t stateTelemetry;
  uint8_t statePower;
  uint8_t stateSens;
  uint8_t stateControl;

  // Flight Data

  float acceleration;
  float heightPressure;
  uint8_t flightEvents;
  float latitude;
  float longitude;

  // Telemetry Data

  float heightGNSS;
  uint8_t satCountGNSS;
  float hdopGNSS;
  uint8_t temperatureElectronics;
  uint8_t temperatureBattery;
  uint8_t stateCapacitors;
  uint8_t continuityPyros;
  uint8_t pressureDecoupler;
  uint8_t ldrDecoupler;
  float voltageBattery;
  float currentBattery;
  float currentUmbilical;
  uint8_t stateUmbilical;
  float voltageBatteryCOTS;
};
