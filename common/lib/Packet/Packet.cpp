/*
    Packet - Library for encoding and decoding telemetry packets for the ASCENT II telemetry system.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Packet.h"

void Packet::encode(uint8_t* packet, uint8_t address, uint8_t flight_mode, uint8_t low_power_mode, uint8_t subsystem_status, uint8_t status_events, float acceleration, float height_pressure, float height_gnss, float lat_gnss, float lon_gnss, float battery_voltage)
{
    packet[0] |= address << 4;
    
    packet[1] |= flight_mode << 7;
    packet[1] |= low_power_mode << 6;
    packet[1] |= subsystem_status << 5;
    packet[1] |= (0b111 & status_events) << 2;
    
    if(acceleration < 0) 
    {
       packet[1] |= 1 << 1;
       acceleration = -acceleration;
    }
    if(acceleration >= 31.9375)
    {
       packet[1] |= 1 << 0;
       packet[2] = 0xFF;
    }
    else
    {
        packet[2] = 0xFF & (uint16_t)(acceleration / 0.0625);
        packet[1] |=  (0x0100 & (uint16_t)(acceleration / 0.0625)) >> 8;
    }
    
    if(0 < height_pressure && height_pressure < 65535 / 4 )
    {
        packet[4] = 0xFF & (uint16_t)(height_pressure / 0.25);
        packet[3] = (0xFF00 & (uint16_t)(height_pressure / 0.25)) >> 8;
    } 
    else if (height_pressure <= 0)
    {
        packet[4] = 0x00;
        packet[3] = 0x00;
    }
    else
    {
        packet[4] = 0xFF;
        packet[3] = 0xFF;
    }

    if(0 < height_gnss && height_gnss < 65535 / 4 )
    {
        packet[6] = 0xFF & (uint16_t)(height_gnss / 0.25);
        packet[5] = (0xFF00 & (uint16_t)(height_gnss / 0.25)) >> 8;
    } 
    else if (height_gnss <= 0)
    {
        packet[6] = 0x00;
        packet[5] = 0x00;
    }
    else
    {
        packet[6] = 0xFF;
        packet[5] = 0xFF;
    }

    if(lat_gnss < 0)
    {
        packet[7] |= 1 << 7;
        lat_gnss = -lat_gnss;
    }
    packet[7]   |=  (0x1FC0000 & (uint32_t)(lat_gnss / 0.0000026822)) >> 18;
    packet[8]   =  (0x1FC00 & (uint32_t)(lat_gnss / 0.0000026822)) >> 10;
    packet[9]   =  (0x1FC & (uint32_t)(lat_gnss / 0.0000026822)) >> 2;
    packet[10] |=  (0x03 & (uint32_t)(lat_gnss / 0.0000026822)) << 6;
    
    if(lon_gnss < 0)
    {
        packet[10] |= 1 << 5;
        lon_gnss = -lon_gnss;
    }
    packet[10]   |=  (0x1F00000 & (uint32_t)(lon_gnss / 0.0000013411)) >> 20;
    packet[11]   =  (0x1F000 & (uint32_t)(lon_gnss / 0.0000013411)) >> 12;
    packet[12]   =  (0x1F0 & (uint32_t)(lon_gnss / 0.0000013411)) >> 4;
    packet[13] |=  (0x0F & (uint32_t)(lon_gnss / 0.0000013411)) << 4;
    
    if( 5.4 < battery_voltage && battery_voltage < 8.4)
    {
        packet[13] |= 0x0F & (uint8_t)(battery_voltage / 0.2);
    }
    else if(battery_voltage <= 5.4)
    {
        packet[13] |= 0x00;
    }
    else
    {
        packet[13] |= 0x0F;
    }

    packet[14] = 0xEE;

    uint8_t cobs_byte = 0;
    for (uint8_t i = 1; i < 14; i++)
    {
        if (packet[i] == 0xEE)
        {
            packet[i] = 0;
            packet[cobs_byte] |= 0x0F & i;
            cobs_byte = i;
        }
    }
}

void Packet::decode(uint8_t packet, uint8_t* address, uint8_t* flight_mode, uint8_t* low_power_mode, uint8_t* subsystem_status, uint8_t* status_events, float* acceleration, float* height_pressure, float* height_gnss, float* lat_gnss, float* lon_gnss, float* battery_voltage, float* rssi)
{

}
