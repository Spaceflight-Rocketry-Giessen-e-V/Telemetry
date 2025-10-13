#include <stdio.h>
#include <iostream>
#include <iomanip>
#include "../Packet.h"

void binary_print(uint8_t var)
{
    uint8_t mask = 1 << ((sizeof(uint8_t) << 3) - 1);
    while (mask) 
    {
        printf("%d", (var & mask ? 1 : 0));
        mask >>= 1;
    }
}

int main()
{
    uint8_t packet[16] = { 0 };
    uint8_t address = 0x01;
    uint8_t flight_mode = 0b1;
    uint8_t low_power_mode = 0b1;
    uint8_t subsystem_status = 0b111 == 0b111;
    uint8_t status_events = 0b011;
    float acceleration = 21.32;
    float height_pressure = 2000.2;
    float height_gnss = 2363.5;
    float lat_gnss = 50.587128;
    float lon_gnss = 8.683172;
    float battery_voltage = 7.6;
    float rssi = -105.123;

    std::cout << "Before transmitting:\n" << (uint16_t)address << " " << (uint16_t)flight_mode << " " << (uint16_t)low_power_mode << " " << (uint16_t)subsystem_status << " " << (uint16_t)status_events << " " << acceleration << " " << height_pressure << " " << height_gnss << " " << std::fixed << std::setprecision(6) << lat_gnss << " " << lon_gnss << std::defaultfloat << " " << battery_voltage << " " << rssi << "\n\n";

    Packet::encode(packet, address, flight_mode, low_power_mode, subsystem_status, status_events, acceleration, height_pressure, height_gnss, lat_gnss, lon_gnss, battery_voltage);
    packet[15] = (uint8_t)(-2 * rssi);

    std::cout << "Transmitted Packet:\n";
    for (int i = 0; i < 16; i++)
    {
        binary_print(packet[i]);
        printf(" ");
    }

    address = 0;
    flight_mode = 0;
    low_power_mode = 0;
    subsystem_status = 0;
    status_events = 0;
    acceleration = 0;
    height_pressure = 0;
    height_gnss = 0;
    lat_gnss = 0;
    lon_gnss = 0;
    battery_voltage = 0;
    rssi = 0;

    Packet::decode(packet, &address, &flight_mode, &low_power_mode, &subsystem_status, &status_events, &acceleration, &height_pressure, &height_gnss, &lat_gnss, &lon_gnss, &battery_voltage, &rssi);

    std::cout << "\n\nAfter receiving:\n" << (uint16_t)address << " " << (uint16_t)flight_mode << " " << (uint16_t)low_power_mode << " " << (uint16_t)subsystem_status << " " << (uint16_t)status_events << " " << acceleration << " " << height_pressure << " " << height_gnss << " " << std::fixed << std::setprecision(6) << lat_gnss << " " << lon_gnss << std::defaultfloat << " " << battery_voltage << " " << rssi << "\n\n";

    system("Pause");
}