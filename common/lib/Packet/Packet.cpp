/*
    Packet - Library for encoding and decoding telemetry packets for the ASCENT II telemetry system.
    Created by Felix Seene and Benjamin Bauersfeld
    Spaceflight Rocketry Giessen e.V.
    Published under the CERN OHL-S v2 license at https://github.com/Spaceflight-Rocketry-Giessen-e-V/Telemetry.
*/

#include "Packet.h"

void Packet::encode(uint8_t* packet, uint8_t address, uint8_t flight_mode, uint8_t low_power_mode, uint8_t subsystem_status, uint8_t status_events, float acceleration, float height_pressure, float height_gnss, float lat_gnss, float lon_gnss, float battery_voltage)
{
    // Address
    packet[0] |= address << 4;
    
    // Status
    packet[1] |= flight_mode << 7;
    packet[1] |= low_power_mode << 6;
    packet[1] |= subsystem_status << 5;
    packet[1] |= (0b111 & status_events) << 2;
    
    // Acceleration
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
    
    // Height (Pressure)
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

    // Height (GNSS)
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

    // Lat (GNSS)
    if (lat_gnss < 0)
    {
        packet[7] |= 1 << 7;
        lat_gnss = -lat_gnss;
    }
    packet[7] |= ((0xFF << 18) & (uint32_t)(lat_gnss / 0.0000026823)) >> 18;
    packet[8] = ((0xFF << 10) & (uint32_t)(lat_gnss / 0.0000026823)) >> 10;
    packet[9] = ((0xFF << 2) & (uint32_t)(lat_gnss / 0.0000026823)) >> 2;
    packet[10] |= ((0xFF >> 6) & (uint32_t)(lat_gnss / 0.0000026823)) << 6;

    // Lon (GNSS)
    if (lon_gnss < 0)
    {
        packet[10] |= 1 << 5;
        lon_gnss = -lon_gnss;
    }
    packet[10] |= ((0xFF << 20) & (uint32_t)(lon_gnss / 0.00000134115)) >> 20;
    packet[11] = ((0xFF << 12) & (uint32_t)(lon_gnss / 0.00000134115)) >> 12;
    packet[12] = ((0xFF << 4) & (uint32_t)(lon_gnss / 0.00000134115)) >> 4;
    packet[13] |= ((0xFF >> 4) & (uint32_t)(lon_gnss / 0.00000134115)) << 4;
    
    // Battery Voltage
    if( 5.4 < battery_voltage && battery_voltage < 8.4)
    {
        packet[13] |= 0x0F & (uint8_t)((battery_voltage - 5.4) / 0.2);
    }
    else if(battery_voltage <= 5.4)
    {
        packet[13] |= 0x00;
    }
    else
    {
        packet[13] |= 0x0F;
    }

    // End Byte
    packet[14] = 0xEE;

    // COBS
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

void Packet::decode(uint8_t* packet, uint8_t* address, uint8_t* flight_mode, uint8_t* low_power_mode, uint8_t* subsystem_status, uint8_t* status_events, float* acceleration, float* height_pressure, float* height_gnss, float* lat_gnss, float* lon_gnss, float* battery_voltage, float* rssi)
{
    // End Byte
    if(packet[14] != 0xEE)
        return;

    // COBS
    uint8_t tmp1 = 0;
    uint8_t tmp2 = packet[tmp1] & 0x0F;
    while (tmp2 != 0x00)
    {
        tmp1 = tmp2;
        tmp2 = packet[tmp1] & 0x0F;
        packet[tmp1] = 0xEE;
    }

    *address = (packet[0] & 0xF0) >> 4;

    *flight_mode = (packet[1] & 0x80) >> 7;

    *low_power_mode = (packet[1] & 0x40) >> 6;

    *subsystem_status = (packet[1] & 0x20) >> 5;

    *status_events = (packet[1] & 0x1C) >> 2;

    *acceleration = (float)((uint16_t)(packet[1] & 0x01) << 8 | (uint16_t)(packet[2])) * 0.0625;
    if((packet[1] & 0x02) != 0)
        *acceleration = -*acceleration;

    *height_pressure = (float)((uint16_t)(packet[3]) << 8 | (uint16_t)(packet[4])) * 0.25;

    *height_gnss = (float)((uint16_t)(packet[5]) << 8 | (uint16_t)(packet[6])) * 0.25;

    *lat_gnss = (float)((uint32_t)(packet[7] & 0x7F) << 18 | (uint32_t)(packet[8]) << 10 | (uint32_t)(packet[9]) << 2 | (uint32_t)(packet[10] & 0xC0) >> 6) * 0.0000026823;
    if((packet[7] & 0x80) != 0)
        *lat_gnss = -*lat_gnss;

    *lon_gnss = (float)((uint32_t)(packet[10] & 0x1F) << 20 | (uint32_t)(packet[11]) << 12 | (uint32_t)(packet[12]) << 4 | (uint32_t)(packet[13] & 0xF0) >> 4) * 0.00000134115;
    if((packet[10] & 0x20) != 0)
        *lon_gnss = -*lon_gnss;

    *battery_voltage = (float)((uint8_t)(packet[13]) & 0x0F) * 0.2 + 5.4;

    *rssi = -0.5 * (float)(packet[15]);
}
