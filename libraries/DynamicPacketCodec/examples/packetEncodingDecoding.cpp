#include "Arduino.h"
#include "DynamicPacketCodec.h"

int main()
{
    uint8_t comp1 = 42;
    float comp2 = 4.2;

    Packet myPacket;
    myPacket.addComponent(new const_Component(0xFF, 8, 255)); // Constant start byte
    myPacket.addComponent(new parity_Component()); // Parity bit
    myPacket.addComponent(new uint8_t_Component(&comp1, 6, 0, 50)); // uint8_t component with a size of 6 bits, a minimum value of 0 and a maximum value of 50
    myPacket.addComponent(new float_Component(&comp2, 15, 0, 10)); // float component with a size of 15 bits, a minimum value of 0 and a maximum value of 10

    uint8_t *packetBufferTX = myPacket.encode();

    uint8_t *packetBufferRX = packetBufferTX; // Transmission

    if(myPacket.decode(packetBufferRX) != 0)
    {
        // Error
    }
}
