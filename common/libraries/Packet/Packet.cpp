/*
    Packet - Library for encoding and decoding telemetry packets for the ASCENT III telemetry system.
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Packet.h"

void Packet::encodeFrame(uint8_t *packet, uint8_t packetIdentifier)
{
    // Packet Identifier
    packet[0] |= (0x01 & packetIdentifier) << 2;

    // End Byte
    packet[11] = 0xEE;

    // COBS
    uint8_t cobsByte = 0;
    for (uint8_t bytePos = 1; bytePos < 11; bytePos++)
    {
        if (packet[bytePos] == 0xEE)
        {
            packet[bytePos] = 0;
            packet[cobsByte] |= (0x0F & bytePos) << 4;
            cobsByte = bytePos;
        }
    }

    // Parity Bit
    uint8_t parityBit = 0;
    for (uint8_t bytePos = 0; bytePos < 12; bytePos++)
    {
        uint8_t count = 0;
        for (uint8_t bitPos = 0; bitPos < 8; bitPos++) 
        {       
            if (packet[bytePos] & (1 << bitPos))
            {
                count++;
            }
        }
        parityBit ^= (count % 2 != 0);
    }
    packet[0] ^= (0x01 & parityBit) << 3;
}

uint8_t Packet::decodeFrame(uint8_t *packet, uint8_t *packetIdentifier)
{
    // Parity Bit
    uint8_t parityBit = 0;
    for (uint8_t bytePos = 0; bytePos < 12; bytePos++)
    {
        uint8_t count = 0;
        for (uint8_t bitPos = 0; bitPos < 8; bitPos++)
        {
            if (packet[bytePos] & (1 << bitPos))
            {
                count++;
            }
        }
        parityBit ^= (count % 2 != 0);
    }
    if (parityBit != 0)
    {
        return 1;
    }

    // End Byte
    if (packet[11] != 0xEE)
    {
        return 1;
    }

    // COBS
    uint8_t tmp1 = 0;
    uint8_t tmp2 = (packet[tmp1] & 0xF0) >> 4;
    while (tmp2 != 0x00)
    {
        tmp1 = tmp2;
        tmp2 = (packet[tmp1] & 0xF0) >> 4;
        packet[tmp1] = 0xEE;
    }

    // Packet Identifier
    *packetIdentifier = (packet[0] & 0x04) >> 2;

    // Success
    return 0;
}

void Packet::encodeFlightData(uint8_t* packet, float acceleration, float heightPressure, uint8_t flightEvents, float latitude, float longitude)
{
    // Acceleration
    if (acceleration < 0)
    {
        packet[0] |= 1 << 1;
        acceleration = -acceleration;
    }
    if (acceleration >= 16)
    {
        acceleration = 16;
    }
    packet[0] |= (0x0100 & (uint16_t)(acceleration / 0.033333333 + 0.5)) >> 8;
    packet[1] |= 0x00FF & (uint16_t)(acceleration / 0.033333333 + 0.5);

    // Height (Pressure)
    if (heightPressure < 0)
    {
        heightPressure = 0;
    }
    else if (heightPressure > 6500)
    {
        heightPressure = 6500;
    }
    packet[2] |= (0x7F80 & (uint32_t)(heightPressure / 0.2 + 0.5)) >> 7;
    packet[3] |= 0x007F & (uint32_t)(heightPressure / 0.2 + 0.5) << 1;

    //Status Events
    packet[3] |= (0x10 & flightEvents);
    packet[4] |= (0x0F & flightEvents) << 4;

    // Lat (GNSS)
    if (latitude < 0)
    {
        packet[4] |= 1 << 3;
        latitude = -latitude;
    }
    if (latitude > 90)
    {
        latitude = 90;
    }
    packet[4] |= (0x01C00000 & (uint32_t)(latitude / 0.0000026823 + 0.5)) >> 22;
    packet[5] |= (0x003FC000 & (uint32_t)(latitude / 0.0000026823 + 0.5)) >> 14;
    packet[6] |= (0x00003FC0 & (uint32_t)(latitude / 0.0000026823 + 0.5)) >> 6;
    packet[7] |= (0x0000003F & (uint32_t)(latitude / 0.0000026823 + 0.5)) << 2;

    // Lon (GNSS)
    if (longitude < 0)
    {
        packet[7] |= 1 << 1;
        longitude = -longitude;
    }
    if (longitude > 180)
    {
        longitude = 180;
    }
    packet[7] |= (0x01000000 & (uint32_t)(longitude / 0.0000053645 + 0.5)) >> 24;
    packet[8] |= (0x00FF0000 & (uint32_t)(longitude / 0.0000053645 + 0.5)) >> 16;
    packet[9] |= (0x0000FF00 & (uint32_t)(longitude / 0.0000053645 + 0.5)) >> 8;
    packet[10] |= (0x000000FF & (uint32_t)(longitude / 0.0000053645 + 0.5));

    // Packet Framing (COBS, Packet Identifier, End Byte, Parity)
    encodeFrame(packet, 0);
}

void Packet::decodeFlightData(uint8_t* packet, float* acceleration, float* heightPressure, uint8_t* flightEvents, float* latitude, float* longitude, float* rssi)
{
    // Acceleration
    *acceleration = (float)((uint32_t)(packet[0] & 0x01) << 8 | (uint32_t)(packet[1])) * 0.033333333;
    if ((packet[0] & (0x01 << 1)) != 0)
        *acceleration = -*acceleration;

    //height 
    *heightPressure = (float)((uint32_t)(packet[2]) << 7 | (uint32_t)(packet[3] >> 1)) * 0.2;

    //flightEvents
    *flightEvents = (uint32_t)((packet[3] & 0x01) << 4 | (uint32_t)(packet[4] >> 4));

    //Latitude
    *latitude = (float)((uint32_t)(packet[4] & 0x07) << 22 | (uint32_t)(packet[5]) << 14 | (uint32_t)(packet[6]) << 6 | (uint32_t)(packet[7] & 0xFC) >> 2) * 0.0000026823;
    if ((packet[4] & 0x08) != 0)
        *latitude = -*latitude;

    //Longitude
    *longitude = (float)((uint32_t)(packet[7] & 0x01) << 24 | (uint32_t)(packet[8]) << 16 | (uint32_t)(packet[9]) << 8 | (uint32_t)packet[10]) * 0.0000053645;
    if ((packet[7] & 0x02) != 0)
        *longitude = -*longitude;

    // RSSI
    *rssi = -0.5 * (float)(packet[12]);
}

void Packet::encodeTelemetryData(uint8_t *packet, uint8_t stateTelemetry, uint8_t statePower, uint8_t stateSens, uint8_t stateControl, float heightGNSS, uint8_t satCountGNSS, float hdopGNSS, uint8_t temperatureElectronics, uint8_t temperatureBattery, uint8_t stateCapacitors, uint8_t continuityPyros, uint8_t pressureDecoupler, uint8_t ldrDecoupler, float voltageBattery, float currentBattery, float currentUmbilical, uint8_t stateUmbilical, uint8_t lowPowerMode, float voltageBatteryCOTS)
{
    // Subsystem States
    packet[1] |= (0x03 & stateTelemetry) << 6;
    packet[1] |= (0x03 & statePower) << 4;
    packet[1] |= (0x03 & stateSens) << 2;
    packet[1] |= (0x03 & stateControl);

    // Height GNSS
    if (heightGNSS < 0)
    {
        heightGNSS = 0;
    }
    else if (heightGNSS > 6500)
    {
        heightGNSS = 6500;
    }
    packet[2] |= (0x7F00 & (uint16_t)(heightGNSS / 0.2 + 0.5)) >> 8;
    packet[3] |= (0x00FF & (uint16_t)(heightGNSS / 0.2 + 0.5));

    // GNSS Satellite Count
    if (satCountGNSS > 15)
    {
        satCountGNSS = 15;
    }
    packet[4] |= (0x0F & satCountGNSS) << 4;

    // GNSS HDOP
    if (hdopGNSS > 7.5)
    {
        hdopGNSS = 7.5;
    }
    packet[4] |= (0x0F & (uint8_t)(hdopGNSS / 0.5 + 0.5));

    // Elecronics Temperature
    if (temperatureElectronics > 150)
    {
        temperatureElectronics = 150;
    }
    packet[5] |= (0x0F & ((temperatureElectronics + 5) / 10)) << 4;

    // Battery Temperature
    if (temperatureBattery > 150)
    {
        temperatureBattery = 150;
    }
    packet[5] |= (0x0F & ((temperatureBattery + 5) / 10));

    // Capacitors State
    packet[6] |= (0x0F & stateCapacitors) << 4;

    // Pyros Continuity
    packet[6] |= (0x03 & continuityPyros) << 2;

    // Decoupler Pressure
    packet[6] |= (0x01 & pressureDecoupler) << 1;

    // Decoupler LDR
    packet[6] |= (0x01 & ldrDecoupler);

    // Battery Voltage
    if (voltageBattery < 5)
    {
        voltageBattery = 5;
    }
    else if (voltageBattery > 8.15)
    {
        voltageBattery = 8.15;
    }
    packet[7] |= (0x3F & (uint8_t)((voltageBattery - 5) / 0.05 + 0.5));

    // Battery Current
    if (currentBattery > 1.75)
    {
        currentBattery = 1.75;
    }
    else if (currentBattery < 0)
    {
        currentBattery = -currentBattery;
    }
    packet[8] |= (0x07 & (uint8_t)(currentBattery / 0.25 + 0.5)) << 5;

    // Umbilical Current
    if (currentUmbilical > 1.75)
    {
        currentUmbilical = 1.75;
    }
    else if (currentUmbilical < 0)
    {
        currentUmbilical = -currentUmbilical;
    }
    packet[8] |= (0x07 & (uint8_t)(currentUmbilical / 0.25 + 0.5)) << 2;

    // Umbilical State
    packet[8] |= (0x01 & stateUmbilical) << 1;

    // Low Power Mode
    packet[8] |= (0x01 & lowPowerMode);

    // COTS Battery Voltage
    if (voltageBatteryCOTS < 5)
    {
        voltageBatteryCOTS = 5;
    }
    else if (voltageBatteryCOTS > 11.2)
    {
        voltageBatteryCOTS = 11.2;
    }
    packet[9] |= (0x1F & (uint8_t)((voltageBatteryCOTS - 5) / 0.2 + 0.5)) << 3;

    // Packet Framing (COBS, Packet Identifier, End Byte, Parity)
    encodeFrame(packet, 1);
}

void Packet::decodeTelemetryData(uint8_t *packet, uint8_t *stateTelemetry, uint8_t *statePower, uint8_t *stateSens, uint8_t *stateControl, float *heightGNSS, uint8_t *satCountGNSS, float *hdopGNSS, uint8_t *temperatureElectronics, uint8_t *temperatureBattery, uint8_t *stateCapacitors, uint8_t *continuityPyros, uint8_t *pressureDecoupler, uint8_t *ldrDecoupler, float *voltageBattery, float *currentBattery, float *currentUmbilical, uint8_t *stateUmbilical, uint8_t *lowPowerMode, float *voltageBatteryCOTS, float *rssi)
{
    // Subsystem States
    *stateTelemetry = (0xC0 & packet[1]) >> 6;
    *statePower = (0x30 & packet[1]) >> 4;
    *stateSens = (0x0C & packet[1]) >> 2;
    *stateControl = (0x03 & packet[1]);

    // Height GNSS
    *heightGNSS = (float)((uint16_t)(0x7F & packet[2]) << 8 | (uint16_t)(packet[3])) * 0.2;

    // GNSS Satellite Count
    *satCountGNSS = (0xF0 & packet[4]) >> 4;

    // GNSS HDOP
    *hdopGNSS = (float)(0x0F & packet[4]) * 0.5;

    // Elecronics Temperature
    *temperatureElectronics = ((0xF0 & packet[5]) >> 4) * 10;

    // Elecronics Temperature
    *temperatureBattery = (0x0F & packet[5]) * 10;

    // Capacitors State
    *stateCapacitors = (0xF0 & packet[6]) >> 4;

    // Pyros Continuity
    *continuityPyros = (0x0C & packet[6]) >> 2;

    // Decoupler Pressure
    *pressureDecoupler = (0x02 & packet[6]) >> 1;

    // Decoupler LDR
    *ldrDecoupler = (0x01 & packet[6]);

    // Battery Voltage
    *voltageBattery = (float)((0x3F & packet[7])) * 0.05 + 5;

    // Battery Current
    *currentBattery = (float)((0xE0 & packet[8]) >> 5) * 0.25;

    // Umbilical Current
    *currentUmbilical = (float)((0x1C & packet[8]) >> 2) * 0.25;

    // Umbilical State
    *stateUmbilical = (0x02 & packet[8]) >> 1;

    // Low Power Mode
    *lowPowerMode = (0x01 & packet[8]);

    // COTS Battery Voltage
    *voltageBatteryCOTS = (float)((0xF8 & packet[9]) >> 3) * 0.2 + 5;

    // RSSI
    *rssi = -0.5 * (float)(packet[12]);
}

void Packet::encodeCommand(uint8_t input, uint8_t* output)
{
    uint8_t count = 0;

    //-------------Normalisation-------------
    if(input >= 'A' && input <= 'Z')
    {
        input = input - 'A' + 'a';
    }

    //-------------Parity-Endcoding-------------
    for (uint8_t i = 0; i < 7; i++) 
    {       
        if (input & (1 << i)) count++;
    }
    if (count % 2 != 0) 
    {
        input|= 0x80;                   
    }
    
    *output = input;
}
        
void Packet::decodeCommand(uint8_t input, uint8_t* output)
{
    uint8_t count = 0;

    //-------------Parity-Decoding-------------
    for (uint8_t i = 0; i < 8; i++)
    {
        if (input & (1 << i)) 
        {
            count++;
        }
    }

    if (count % 2 !=0)
    {
        input=0x00;
    }
    else
    {
        input &= 0x7F;
    }

    //-------------Normalisation-------------
    if(input >= 'A' && input <= 'Z')
    {
        input = input - 'A' + 'a';
    }

    *output = input;
}

