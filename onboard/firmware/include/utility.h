#include "Arduino.h"
#include "Radiocrafts_RC17xxHP_RC232.h"
#include "Packet.h"

// LEDs states
#define SETUPBEGIN 1
#define SETUPRADIOMODULS 2
#define SETUPEND 3
#define RADIOMODUL_ONE 4
#define RADIOMODUL_TWO 5

class ledStruct;
class dataStruct;

void buzzerSound(uint8_t pinBuzzer);

void buzzerSoundError(uint8_t pinBuzzer);

void radioModulesSetup(RC17xxHP_RC232 rc1780hp, RC17xxHP_RC232 rc1701hp, ledStruct pinLed, uint8_t pinBuzzer); // Wenn Error: buzzerSoundError();
// ledUpdate aufrufen: ledUpdate(4): radiomodul 1 funktioniert: D2 anschalten, ledUpdate(5): radiomodul 2 funktioniert: D3 anschalten

uint8_t commandReceive(RC17xxHP_RC232 radioModule); // Aufruf Packet Library Function, return 0 wenn kein Command, sonst return command

void commandExecute(uint8_t command); //  Distribute Data To Subsystems etc.. Check for 0 (-> no command)

uint8_t packetSendCheck(uint8_t *flightmode, uint8_t loopFrequency, uint8_t timeBetweenStandbyPackets, uint16_t loopCount);

void packetSend(RC17xxHP_RC232 *radioModule, dataStruct dataVariables, uint8_t packetIdentifier);

void flashWrite(dataStruct dataVariables);

void loopVariablesUpdate(uint16_t *loopCount, uint32_t *loopStartTime, uint8_t loopFrequency, uint8_t pinLedLoop);

void ledUpdate(uint8_t state, ledStruct &pinLed); // Switch Case

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

    void pinMode();
};

class dataStruct // :)
{
public:
    uint8_t statePower;
    uint8_t stateSens;
    uint8_t stateControl;
    // Define Variables here: height, latitude, longitude etc.
};
