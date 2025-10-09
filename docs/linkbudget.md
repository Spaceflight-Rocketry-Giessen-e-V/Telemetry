# Link Budget

By calculating the link budget of the telemetry system, either the maximum range of the system or individual parameters, such as transmit power, can be determined at a fixed range. A detailed explanation of the link budget can be found [here](https://s.campbellsci.com/documents/us/technical-papers/link-budget.pdf). Additional informations are available [here](https://de.wikipedia.org/wiki/Leistungs%C3%BCbertragungsbilanz), [here](https://en.wikipedia.org/wiki/Link_budget), and [here](https://www.sss-mag.com/pdf/an9804.pdf).

The general formula for a link budget describes the signal strength at the receiver and includes components that either increase (positive sign) or decrease (negative sign) the received strength. All values are given in dB (or dBm and dBi).

$P_\text{RX} = P_\text{TX} + G_\text{TX} - L_\text{TX} - L_\text{FS} - L_\text{M} + G_\text{RX} - L_\text{RX}$

## Transmitter Parameters:
- Transmit Power $P_\text{TX}$ 
Specified in the data sheet of the radio module: $P_\text{TX} = 27$ dBm
- Gain of the Transmitting Antenna $G_\text{TX}$ 
The selected transmitting antenna, a QFH antenna, has negligible gain: $G_\text{TX} = 0$
- Transmission Losses on the Transmitting Side $L_\text{TX}$ 
Includes losses in cables and traces as well as transition losses at connectors or other components. These losses depend on the coaxial cable used, the connectors, and much more, and can only be estimated or measured: $L_\text{TX} < 5$ dB

## Receiver Parameters:
- Signal Strength at the Receiver $P_\text{RX}$ 
The minimum signal strength of the radio module is specified in the data sheet: $P_\text{RX, typ} = -118$ dBm, $P_\text{RX, min} = -114$ dBm
- Gain of the Receiving Antenna $G_\text{RX}$ 
The chosen receiving antenna, a helical antenna, can be designed based on the required gain, with higher gain requiring more precise alignment of the antenna. A good estimate is: $G_\text{RX} = 10$ dBi
- Transmission Losses on the Receiving Side $L_\text{RX}$ 
See $L_\text{TX}$: $L_\text{RX} < 5$ dB

## Path Loss:
- Free Space Attenuation $L_\text{FS}$ 
The free space attenuation describes the reduced power density of an EM wave as the distance from the source increases. The formula is: $L_\text{FS} = 20 \cdot \text{log}\left(\frac{4 \pi r f}{c}\right)$ (with $r$ as the distance to the transmitting antenna and $f$ as the frequency used). For a maximum range of $18$ km, this yields: $L_\text{FS} \approx 116$ dB
- Additional Losses During Propagation $L_\text{M}$ 
These losses include absorption losses in the atmosphere, losses due to diffraction and shadowing, as well as losses due to diffraction at obstacles within the Fresnel zone (potentially occurring as fading). They are difficult to estimate and can only be verified through measurements.

Reflection effects can potentially be calculated and included as described [here](https://s.campbellsci.com/documents/us/technical-papers/link-budget.pdf) in Chapter 5.3. These likely have no effect in our case due to the height of the antennas.

The formula for the link budget can be rearranged to calculate the maximum tolerable losses due to transmission for the maximum desired range. $L_\text{TX} + L_\text{RX} + L_\text{M}$ are the unknown losses here.

$L_\text{TX} + L_\text{RX} + L_\text{M} = P_\text{TX} - P_\text{RX} + G_\text{TX} + G_\text{RX} - L_\text{FS}$

Thus, $L_\text{TX} + L_\text{RX} + L_\text{M} \approx 39$ dB for $P_\text{RX, typ}$ and $L_\text{TX} + L_\text{RX} + L_\text{M} \approx 35$ dB for $P_\text{RX, min}$.

The actual values for $L_\text{TX}$ and $L_\text{RX}$ can be determined through measurements, and the entire formula can be validated and adjusted step by step. If $L_\text{TX}$ and $L_\text{RX}$ are either estimated concretely or measured, only $L_\text{M}$ remains.

For $L_\text{TX} = L_\text{RX} = 3$ dB and $P_\text{RX, min}$, we have $L_\text{M} \approx 29$ dB. This value can be understood as a sort of safety buffer (link margin) for adverse atmospheric conditions, poor estimates, or measurements of other parameters and guarantees a reliable connection. This buffer should never be smaller than $10$ dB and should be greater than $20$ dB or $30$ dB for reliable connections.

If the link margin is too small, the received signal can be amplified using a stronger directional reception antenna or by incorporating an amplifier. If the link margin is comparatively large, for example, the data rate can be increased or the directivity of the receiving antenna can be reduced.

# Link Budget Simulation

[In the simulations folder](../simulations/linkbudget.py), a Python script for a simple link budget simulation based on our expected flight profile is included.
It generates the following graphical output:
<img src="media/images/linkbudget.png" width="400"/>