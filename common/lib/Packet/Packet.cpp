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
    packet[0] |= (0x0F & address) << 4;

    // Status
    packet[1] |= (0x01 & flight_mode) << 7;
    packet[1] |= (0x01 & low_power_mode) << 6;
    packet[1] |= (0x01 & subsystem_status) << 5;
    packet[1] |= (0x07 & status_events) << 2;

    // Acceleration
    if (acceleration < 0)
    {
        packet[1] |= 1 << 1;
        acceleration = -acceleration;
    }
    if (acceleration >= 31.9375)
    {
        acceleration = 31.9375;
    }
    packet[1] |= (0x0100 & (uint16_t)(acceleration / 0.0625 + 0.5)) >> 8;
    packet[2] |= 0x00FF & (uint16_t)(acceleration / 0.0625 + 0.5);

    // Height (Pressure)
    if (height_pressure < 0)
    {
        height_pressure = 0;
    }
    else if (height_pressure > 16383.75)
    {
        height_pressure = 16383.75;
    }
    packet[3] |= (0xFF00 & (uint16_t)(height_pressure / 0.25 + 0.5)) >> 8;
    packet[4] |= 0x00FF & (uint16_t)(height_pressure / 0.25 + 0.5);

    // Height (GNSS)
    if (height_gnss < 0)
    {
        height_gnss = 0;
    }
    else if (height_gnss > 16383.75)
    {
        height_gnss = 16383.75;
    }
    packet[5] |= (0xFF00 & (uint16_t)(height_gnss / 0.25 + 0.5)) >> 8;
    packet[6] |= 0x00FF & (uint16_t)(height_gnss / 0.25 + 0.5);

    // Lat (GNSS)
    if (lat_gnss < 0)
    {
        packet[7] |= 1 << 7;
        lat_gnss = -lat_gnss;
    }
    packet[7] |= (0x1FC0000 & (uint32_t)(lat_gnss / 0.0000026823 + 0.5)) >> 18;
    packet[8] |= (0x3FC00 & (uint32_t)(lat_gnss / 0.0000026823 + 0.5)) >> 10;
    packet[9] |= (0x3FC & (uint32_t)(lat_gnss / 0.0000026823 + 0.5)) >> 2;
    packet[10] |= (0x3 & (uint32_t)(lat_gnss / 0.0000026823 + 0.5)) << 6;

    // Lon (GNSS)
    if (lon_gnss < 0)
    {
        packet[10] |= 1 << 5;
        lon_gnss = -lon_gnss;
    }
    packet[10] |= (0x1F00000 & (uint32_t)(lon_gnss / 0.0000053645 + 0.5)) >> 20;
    packet[11] |= (0xFF000 & (uint32_t)(lon_gnss / 0.0000053645 + 0.5)) >> 12;
    packet[12] |= (0xFF0 & (uint32_t)(lon_gnss / 0.0000053645 + 0.5)) >> 4;
    packet[13] |= (0x0F & (uint32_t)(lon_gnss / 0.0000053645 + 0.5)) << 4;

    // Battery Voltage
    if (battery_voltage < 5.4)
    {
        battery_voltage = 5.4;
    }
    else if (battery_voltage > 8.4)
    {
        battery_voltage = 8.4;
    }
    packet[13] |= 0x0F & (uint8_t)((battery_voltage - 5.4) / 0.2 + 0.5);

    // End Byte
    packet[14] |= 0xEE;

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
    if (packet[14] != 0xEE)
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
    if ((packet[1] & (0x01 << 1)) != 0)
        *acceleration = -*acceleration;

    *height_pressure = (float)((uint16_t)(packet[3]) << 8 | (uint16_t)(packet[4])) * 0.25;

    *height_gnss = (float)((uint16_t)(packet[5]) << 8 | (uint16_t)(packet[6])) * 0.25;

    *lat_gnss = (float)((uint32_t)(packet[7] & 0x7F) << 18 | (uint32_t)(packet[8]) << 10 | (uint32_t)(packet[9]) << 2 | (uint32_t)(packet[10] & 0xC0) >> 6) * 0.0000026823;
    if ((packet[7] & (0x01 << 7)) != 0)
        *lat_gnss = -*lat_gnss;

    *lon_gnss = (float)((uint32_t)(packet[10] & 0x1F) << 20 | (uint32_t)(packet[11]) << 12 | (uint32_t)(packet[12]) << 4 | (uint32_t)(packet[13] & 0xF0) >> 4) * 0.0000053645;
    if ((packet[10] & (0x01 << 5)) != 0)
        *lon_gnss = -*lon_gnss;

    *battery_voltage = (float)((uint8_t)(packet[13]) & 0x0F) * 0.2 + 5.4;

    *rssi = -0.5 * (float)(packet[15]);
}
