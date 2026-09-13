#include "header.h"

/**
 * @brief Class to dynamically initialise different subsystems.
 *
 */
class Subsystem
{
public:
    // Konstruktoren Überladungen möglich
    Subsystem(uint8_t i2cAddress, uint8_t *pinLed, uint8_t *subsystemStatus, uint8_t **uint8List, uint8_t uint8Count, float **floatList, uint8_t floatCount);

    void write(uint8_t byte);
    void connectionCheck();
    void dataGet();
    void ledUpdate(uint8_t lowPowerMode);
    uint8_t statusGet();

private:
    float bytesToFloat(uint8_t *bytes);

    uint8_t _i2cAddress;
    uint8_t *_pinLed;
    uint8_t _stateLed;
    uint8_t *_subsystemState;
    uint8_t **_uint8List;
    uint8_t _uint8Count;
    float **_floatList;
    uint8_t _floatCount;
};

/**
 * @brief Function to check if a system is connected.
 *
 * @param subsystemsList
 * @param subsystemsCount
 */
void subsystemsConnCheck(Subsystem **subsystemsList, uint8_t subsystemsCount);

/**
 * @brief Function to request data from the Subsystems.
 *
 * @param subsystemsList
 * @param subsystemsCount
 */
void subsystemsDataGet(Subsystem **subsystemsList, uint8_t subsystemsCount);

/**
 * @brief Function to update the sub systems LEDs.
 *
 * @param subsystemsList
 * @param subsystemsCount
 * @param lowPowerMode
 */
void subsystemsLedUpdate(Subsystem **subsystemsList, uint8_t subsystemsCount, uint8_t lowPowerMode);