# Operations cheatsheet / manual for the ASCENT II telemetry system

## Radio command reference

The command input can be in either lower or upper case letters.
Upper case letters will be converted to lower case letters before transmission.

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

**0**: Pad idle
**1**: Main deployment altitude set
**2**: Positive continuity test
**3**: Armed
**4**: Liftoff detected
**5**: Booster burnout detected
**6**: Apogee detected
**7**: Pyro 1 signal sent (drogue)
**8**: Pyro 2 signal sent (drogue)
**9**: Drogue deployment detected
**10**: Pyro 3 signal sent (main)
**11**: Pyro 4 signal sent (main)
**12**: Main deployment detected
**13**: Landing detected
**14**: ABORT - Initialization failed
**15**: ABORT - Negative continuity test