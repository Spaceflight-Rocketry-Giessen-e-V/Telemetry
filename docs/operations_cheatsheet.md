# Operations cheatsheet / manual for the ASCENT II telemetry system

## Radio command reference

The command input can be in either lower or upper case letters.
Upper case letters will be converted to lower case letters before transmission.
|Char|Function|
|---|---|
|`p`|Ping(Request both data packets)|
|`l`|activates the low power mode|
|`m`|deactivates the low power mode|
|`f`|activates the flight mode|
|`g`|deactivates the flight mode|
|`q`|ejects the drogue parachute immediately|
|`r`|ejects the main parachute immediately|
|`a`|Arming|
|`b`|Dearming|
|`h`|Change pressure sensor|
|`i`|Change acceleration sensor|
|`j`|Change GNSS|
|`s`|Decoupler decoupling|
|`t`|Switch main parachute ejection height|


### Ping

**'p'**: Requests data packet from flight computer.

### Main parachute height adjustment

Sets the altitude for the ejection of the main parachute.

**'a'**: 50 m <br>
**'b'**: 100 m <br>
**'c'**: 150 m <br>
**'d'**: 200 m

### Low power mode

Activating the low power mode deactivates most of the onboard LEDs and has potentially more features in the future.

**'l'**: activates the low power mode <br>
**'m'**: deactivates the low power mode

### Flight mode

Activating the flight mode arms the rocket and activates the continous data transmission

**'f'**: activates the flight mode <br>
**'g'**: deactivates the flight mode

### Drogue Parachute Ejection

**'q'**: ejects the drogue parachute immediately

### Main Parachute Ejection

**'r'**: ejects the main parachute immediately

## Status events reference

**0**: Pad idle, main parachute deployment altitude: 50 m <br>
**1**: Pad idle, main parachute deployment altitude: 100 m <br>
**2**: Pad idle, main parachute deployment altitude: 150 m <br>
**3**: Pad idle, main parachute deployment altitude: 200 m <br>
**4**: System armed <br>
**5**: Liftoff detected <br>
**6**: Booster burnout detected <br>
**7**: Drogue parachute deployed (apogee) <br>
**8**: Drogue parachute deployed (timer) <br>
**9**: Drogue parachute deployed (command) <br>
**10**: Main parachute deployed (altitude) <br>
**11**: Main parachute deployed (timer) (not used) <br>
**12**: Main parachute deployed (command) <br>
**13**: Landing detected (not used) <br>
**14**: Not used <br>
**15**: Not used <br>

## Ground Station LED reference

### LED 1 (Status LED)

Is lit, when the groundstation is in operation. If it is not lit, unplug and replug the groundstation

### LED 2,3,4 (RGB LED)

Indicates the signal strength

**Green**: Good signal strength (RSSI > -50 dB) <br>
**Blue**: Medium signal strength (RSSI > -80 dB) <br>
**Red**: Bad signal strength (RSSI < -80 dB) <br>

### LED 5

Is lit, when flight mode is active

### LED 6

Is lit, when low power mode is active

### LED 7

Is lit, when the two sensorics subsystems are operational

### LED 8

Is lit, when the battery voltage drops below 6.0 V
