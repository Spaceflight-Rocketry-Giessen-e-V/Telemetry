/*
    RC232.h - Library for using Radiocrafts RC232 RF modules.
    Created by ..., xx.xx.2025.
    Spaceflight Rocketry Giessen e.V.
    Licence...
*/

#include "Arduino.h"
#include "RC232.h"

RC232::RC232()
{  
    ledpin1 = PIN_PG3;
    ledpin2 = PIN_PG2;
    ledpin3 = PIN_PG1;
    ledpin4 = PIN_PG0;
    ledpin5 = PIN_PF2;
    ledpin6 = PIN_PE7;
    ledpin7 = PIN_PE5;
    ledpin8 = PIN_PE3;
    d1pin = PIN_PC6;
    d2pin = PIN_PD0;
    d3pin = PIN_PD2;
    armpin = PIN_PD6;
    slppin = PIN_PD4;
    rstpin = PIN_PF4;
    ctspin = PIN_PB5;
    cfgpin = PIN_PB6;
    rtspin = PIN_PB7;
    SerialModule = &Serial0;
    SerialTTL = &Serial4;
    SerialHeader = &Serial1;
}

uint16_t RC232::serial_wait(HardwareSerial* SerialTmp, uint32_t delay_microsecond)
{
    for(uint32_t i = 0; i < (delay_microsecond / 10) && SerialTmp->available() == 0; i++)
    {
        delayMicroseconds(10);
    }
    return SerialTmp->available();
}

uint8_t RC232::enter_config_mode()
{
    digitalWrite(cfgpin, LOW);
    serial_wait(SerialModule, 2 * (590 + 8 * 1000000 / baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{CONFIG-PROMPT} = 590 us), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
    digitalWrite(cfgpin, HIGH);
    if(SerialModule->available() != 0)
    {
        if(SerialModule->read() == '>')
        {
            // Erfolg
            return 0;
        }
        else
        {
            // Error 2: Falsche Antwort vom Modul
            return 2;
        }
    }
    else
    {
        // Error 1: Keine Antwort vom Modul
        return 1;
    }
}

uint8_t RC232::exit_config_mode()
{
    SerialModule->write('X');
    serial_wait(SerialModule, 2 * (1420 + 8 * 1000000 / baud_module)); // Nötige Wartezeit: Reaktionszeit vom Modul (t_{CONFIG-IDLE} = 1420 us), UART-Übertragungsgeschwindigkeit eines Bytes: 8 / baud (in s!), Pufferfaktor 2
    if(SerialModule->available() == 0)
    {
        // Erfolg
        return 0;
    }
    else
    {
        if(SerialModule->read() == '>')
        {
            // Error 2: Falsche Antwort ('>') vom Modul
            return 2;
        }
        else
        {
            // Error 1: Falsche Antwort vom Modul
            return 1;
        }
    }
}

void RC232::begin(uint32_t baud_module, uint32_t baud_ttl, uint32_t baud_header)
{
    pinMode(ledpin1, OUTPUT);
    pinMode(ledpin2, OUTPUT);
    pinMode(ledpin3, OUTPUT);
    pinMode(ledpin4, OUTPUT);
    pinMode(ledpin5, OUTPUT);
    pinMode(ledpin6, OUTPUT);
    pinMode(ledpin7, OUTPUT);
    pinMode(ledpin8, OUTPUT);
    pinMode(d1pin, INPUT);
    pinMode(d2pin, INPUT);
    pinMode(d3pin, INPUT);
    pinMode(armpin, INPUT);
    pinMode(slppin, INPUT);
    pinMode(rstpin, OUTPUT);
    pinMode(ctspin, INPUT);
    pinMode(cfgpin, OUTPUT);
    pinMode(rtspin, OUTPUT);

    digitalWrite(ledpin1, LOW);
    digitalWrite(ledpin2, LOW);
    digitalWrite(ledpin3, LOW);
    digitalWrite(ledpin4, LOW);
    digitalWrite(ledpin5, LOW);
    digitalWrite(ledpin6, LOW);
    digitalWrite(ledpin7, LOW);
    digitalWrite(ledpin8, LOW);
    digitalWrite(rstpin, HIGH);
    digitalWrite(cfgpin, HIGH);
    digitalWrite(rtspin, HIGH);

    delayMicroseconds(3200);                // t_{OFF-IDLE} = 3.2 ms

    SerialModule->begin(baud_module);
    SerialTTL->begin(baud_ttl);
    SerialHeader->begin(baud_header);

    this->baud_module = baud_module;
    this->baud_ttl = baud_ttl;
    this->baud_header = baud_header;

    digitalWrite(ledpin5, HIGH);                // LED 5: begin() complete
}
