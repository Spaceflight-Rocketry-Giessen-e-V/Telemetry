#include "Arduino.h"
#include "RC232.h"

void setup()
{
  RC232 rc1780;
  rc1780.begin(19200, 19200, 19200);
}

void loop()
{

}
