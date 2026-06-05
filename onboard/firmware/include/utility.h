#include "Arduino.h"
#include "Radiocrafts_RC17xxHP_RC232.h"
#include "Packet.h"
void buzzerSound(uint8_t pinBuzzer);

void buzzerSoundError(uint8_t pinBuzzer);

void radioModulesSetup(RC17xxHP_RC232 rc1780hp, RC17xxHP_RC232 rc1701hp);  // Wenn Error: buzzerSoundError();
// ledUpdate aufrufen: ledUpdate(4): radiomodul 1 funktioniert: D2 anschalten, ledUpdate(5): radiomodul 2 funktioniert: D3 anschalten

uint8_t commandReceive(RC17xxHP_RC232 radioModule); // Aufruf Packet Library Function, return 0 wenn kein Command, sonst return command

void commandExecute(uint8_t command); //  Distribute Data To Subsystems etc.. Check for 0 (-> no command)

uint8_t packetSendCheck(uint8_t flightmode, uint8_t loopFrequency, uint8_t timeBetweenStandbyPackets, uint8_t loopCount);
// Ausrechnen:   const uint32_t flight_mode_max_duration = 360 - 3600 / time_between_packets_standby / hz;     // in seconds   6 min (360s) is max sending time
// Return: 0 wenn kein Paket, 1 wenn Sensorikpaket, 2 wenn Telemetriepaket

void packetSend(RC17xxHP_RC232 radioModule, dataStruct dataVariables, uint8_t packetIdentifier); // packetIdentifier auswerten: 0 wenn kein Paket, 1 wenn Sensorikpaket, 2 wenn Telemetriepaket. Entsprechende Encode Funktion in Packet Library aufrufen

void flashWrite(dataStruct dataVariables);

void loopVariablesUpdate(uint8_t* loopCount, uint32_t* loopStartTime, uint8_t loopFrequency, uint8_t pinLedLoop); 
// Delay, count++, loopStartTime aktualisieren, led blinken lassen (loopCount % 2)

void ledUpdate(uint8_t state, ledStruct pinLed); // Switch Case

class ledStruct // :) // An Niklas: Makro für digitalWrite einrichten
{
    public:
        void pinMode(); // Bei allen Pins pinMode(..., OUTPUT) und digitalWrite(..., LOW);

        uint8_t R;
        uint8_t G;
        uint8_t B;
        uint8_t D1;
        uint8_t D2;
        uint8_t D3;
        uint8_t D18;
        uint8_t D19;
        uint8_t Power;
        uint8_t Sens;
        uint8_t Control;
};

class dataStruct // :)
{
    public:
        uint8_t statusPower;
        uint8_t statusSens;
        uint8_t statusControl;
        // Define Variables here: height, latitude, longitude etc.
};