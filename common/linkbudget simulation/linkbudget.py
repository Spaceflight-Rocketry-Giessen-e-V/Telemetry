import matplotlib.pyplot as plt
import numpy as np

# Possible improvements of the calculation:
# - Qualified guess or even measurement of L_TX and L_RX
# - Specification receiver antenna gain G_RX
# - Inclusion of the real gain of the sending antenna G_TX
# - Realistic height profile
# - Incorporation of simulated flight data

f = 869.5e+6                # 869.5 MHz radio frequency

P_TX = 27                   # Transmit signal strength RC1780HP-RC232
G_TX = 0                    # QFH-antenna gain (real gain not equal to 0 and dependant on the angle)
L_TX = 3                    # Transmit (cable, ...) losses (guess)

P_RX = -114                 # Minimum receive signal strength RC1780HP-RC232, alternative: P_RX = -118
G_RX = 10                   # Helix antenna gain, first guess
L_RX = 3                    # Receive (cable, ...) losses (guess)

h_max = 9000                # Maximum height
d_start = 1000              # Horizontal distance at the beginning and during ascent
d_end = 19000               # Horizontal distance at the end
t_ascent = 20               # Ascent time fraction of the total time in %

time = np.linspace(0, 100, 100)
height = np.append(np.linspace(0, h_max, t_ascent), np.linspace(h_max, 0, 100 - t_ascent))      # vertical distance
displacement = np.linspace(d_start, d_end, 100)                                                 # horizontal distance
distance = np.sqrt(height**2 + displacement**2)                                                 # total distance

L_FS = 20 * np.log10((4 * np.pi * distance * f)/(2.998e+8))                                     # Free Space Attenuation

L_M = P_TX - P_RX + G_TX + G_RX - L_FS - L_TX - L_RX                                            # Link Margin

print(f'\nMinimal Link Margin during the flight: {np.min(L_M):.2f} dB')

# Plot

plt.figure(figsize=(12,4), dpi = 300)

plt.subplot(1, 3, 1)
plt.plot(time[:t_ascent], height[:t_ascent], c = 'tab:orange', label = 'Ascent')
plt.scatter(time[t_ascent], height[t_ascent], c = 'tab:green', zorder = 3, label = 'Apogee')
plt.plot(time[t_ascent:], height[t_ascent:], c = 'tab:blue', label = 'Descent')
plt.title('Height profile')
plt.xlabel('Elapsed time / %')
plt.ylabel('Height / m')
plt.legend()

plt.subplot(1, 3, 2)
plt.plot(time[:t_ascent], distance[:t_ascent], c = 'tab:orange', label = 'Ascent')
plt.scatter(time[t_ascent], distance[t_ascent], c = 'tab:green', zorder = 3, label = 'Apogee')
plt.plot(time[t_ascent:], distance[t_ascent:], c = 'tab:blue', label = 'Descent')
plt.title('Distance')
plt.xlabel('Elapsed time / %')
plt.ylabel('Distance / m')
plt.legend()

plt.subplot(1, 3, 3)
plt.plot(time[:t_ascent], L_M[:t_ascent], c = 'tab:orange', label = 'Ascent')
plt.scatter(time[t_ascent], L_M[t_ascent], c = 'tab:green', zorder = 3, label = 'Apogee')
plt.plot(time[t_ascent:], L_M[t_ascent:], c = 'tab:blue', label = 'Descent')
plt.title('$L_\mathrm{M}$ (Link Margin)')
plt.xlabel('Elapsed time / %')
plt.ylabel('$L_\mathrm{M}$ (Link Margin) / dB')
plt.legend()

plt.tight_layout()

plt.savefig('linkbudget.png', bbox_inches = 'tight')