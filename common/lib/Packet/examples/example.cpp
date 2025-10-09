#include <stdio.h>
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
    uint8_t packet[15];
    uint8_t address = 0x01;
    uint8_t flight_mode = 0b1;
    uint8_t low_power_mode = 0b1;
    uint8_t subsystem_status = 0b101 == 0b111;
    uint8_t status_event = 0b110;
    float acceleration = 16.625;
    float height_pressure = 3331.12;
    float height_gnss = 3431.12;
    float lat_gnss = 50.587128;
    float lon_gnss = 8.683172;
    float battery_voltage = 7.6;
    Packet::encode(packet, 0x01, flight_mode, low_power_mode, subsystem_status == 0b111, status_events, acceleration, height_pressure, height_gnss, lat_gnss, lon_gnss, battery_voltage);
    for(int i = 0; i < 15; i++)
    {
        binary_print(packet[i]);
        printf(" ");
    }
}