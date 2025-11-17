import matplotlib.pyplot as plt
import numpy as np

# Possible improvements of the calculation:
# - Qualified guess or even measurement of L_TX and L_RX
# - Specification receiver antenna gain G_RX
# - Inclusion of the real gain of the sending antenna G_TX
# - Realistic height profile

f = 869.5e+6                # 869.5 MHz radio frequency

P_TX = 27                   # Transmit signal strength RC1780HP-RC232
G_TX = 0                    # QFH-antenna gain (real gain not equal to 0 and dependant on the angle)
L_TX = 3                    # Transmit (cable, ...) losses (guess)

P_RX = -114                 # Minimum receive signal strength RC1780HP-RC232, alternative: P_RX = -118
G_RX = 10                   # Helix antenna gain, first guess
L_RX = 3                    # Receive (cable, ...) losses (guess)

displacement = np.append(np.linspace(1000, 1000, 100), np.linspace(1000, 19000, 100))       # Horizontaler Abstand
height = np.append(np.linspace(0, 9000, 100), np.linspace(9000, 0, 100))                    # Vertikaler Abstand
distance = np.sqrt(height**2 + displacement**2)                                             # Abstand

L_FS = 20 * np.log10((4 * np.pi * distance * f)/(2.998e+8))                                 # Freiraumdämpfung

L_M = P_TX - P_RX + G_TX + G_RX - L_FS - L_TX - L_RX                                        # Link Margin

print('\nMinimal Link Margin during the flight: ' + str(np.min(L_M)) + ' dB')

# Plot

plt.figure(figsize=(8,4), dpi = 300)

plt.subplot(1, 2, 1)
plt.plot(displacement[:100], height[:100], c = 'tab:orange', label = 'Ascent')
plt.scatter(displacement[100], height[100], c = 'tab:green', zorder = 3, label = 'Apogee')
plt.plot(displacement[100:], height[100:], c = 'tab:blue', label = 'Descent')
plt.title('Flight profile')
plt.xlabel('Horizontal displacement / m')
plt.ylabel('Height / m')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(height[:100], L_M[:100], c = 'tab:orange', label = 'Ascent')
plt.scatter(height[100], L_M[100], c = 'tab:green', zorder = 3, label = 'Apogee')
plt.plot(height[100:], L_M[100:], c = 'tab:blue', label = 'Descent')
plt.title('Calculation $L_\mathrm{M}$ (Link Margin)')
plt.xlabel('Height / m')
plt.ylabel('$L_\mathrm{M}$ (Link Margin) / dB')
plt.legend()

plt.tight_layout()

plt.savefig('linkbudget.png', bbox_inches = 'tight')