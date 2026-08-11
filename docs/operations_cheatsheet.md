# Operations cheatsheet / operations manual

- [Radio Command Reference](#radio-command-reference)
- [Status Events Reference](#status-events-reference)
- [Groundstation LED Reference](#groundstation-led-reference)

---

## Radio Command Reference

The command input can be in either lower or upper case letters.
Upper case letters will be converted to lower case letters before transmission.
|Char|Function|Subsystem|
|:---:|---|---|
|`a`|Arming|All|
|`b`|Dearming|All|
|`f`|Flight Mode Activation|Telemetry|
|`g`|Flight Mode Deactivation|Telemetry|
|`h`|Change Pressure Sensor|Sensorics|
|`i`|Change Acceleration Sensor|Sensorics|
|`j`|Change GNSS Receiver|Sensorics|
|`l`|Low Power Mode Activation|All|
|`m`|Low Power Mode Dectivation|All|
|`p`|Ping (Request Both Data Packets)|Telemetry|
|`q`|Drogue Parachute Ejection|Flight Control|
|`r`|Main Parachute Ejection|Flight Control|
|`s`|Decoupler Decoupling|Flight Control|
|`t`|Change Main Parachute Ejection Height|Flight Control|
|`v`|Delete Flash Content|Sensorics|
|`w`|Enter Flash Write Mode|Sensorics|

## Status Events Reference

> Status events are not yet defined.

|Event|Description||Event|Description|
|:---:|---|---|:---:|---|
|`0`|||`16`||
|`1`|||`17`||
|`2`|||`18`||
|`3`|||`19`||
|`4`|||`20`||
|`5`|||`21`||
|`6`|||`22`||
|`7`|||`23`||
|`8`|||`24`||
|`9`|||`25`||
|`10`|||`26`||
|`11`|||`27`||
|`12`|||`28`||
|`13`|||`29`||
|`14`|||`30`||
|`15`|||`31`||

## Groundstation LED Reference

|LED|Indication|
|:---:|---|
|`D11`|+3V3|
|`D12`|+5V|
|`D1`|General Status LED|
|`D2`|Radio module 1 initialised|
|`D3`|Radio module 2 initialised|
|`D4`|Red: Setup begin <br> Blue: Setup radio modules <br> Green: Setup complete|
|`D27` - `D34`|RSSI Indication <br> All LEDs lit: RSSI > -40 dBm <br> No LED lit: RSSI < -110 dBm <br> One LED = $\pm$10 dBm|