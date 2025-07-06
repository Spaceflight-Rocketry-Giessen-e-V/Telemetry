import matplotlib.pyplot as plt
import numpy as np

f = 869.5e+6

P_TX = 27
G_TX = 0
P_RX = -118
G_RX = 10

L_TX = 3
L_RX = 3
L_M = 6

displacement = np.append(np.linspace(1000, 1000, 100), np.linspace(1000, 19000, 100))       # Horizontaler Abstand
height = np.append(np.linspace(0, 9000, 100), np.linspace(9000, 0, 100))                    # Vertikaler Abstand
distance = np.sqrt(height**2 + displacement**2)                                             # Abstand

L_FS = 20 * np.log10((4 * np.pi * distance * f)/(2.998e+8))
fade_margin = P_TX - P_RX + G_TX + G_RX - L_FS - L_TX - L_RX - L_M

print('\nMinimale Fade Margin während des Flugprofils: ' + str(np.min(fade_margin)) + ' dB')

# Graphische Darstellung

plt.figure(figsize=(8,4), dpi = 300)

plt.subplot(1, 2, 1)
plt.plot(displacement[:100], height[:100], c = 'tab:orange', label = 'Ascent')
plt.scatter(displacement[100], height[100], c = 'tab:green', zorder = 3, label = 'Apogee')
plt.plot(displacement[100:], height[100:], c = 'tab:blue', label = 'Descent')
plt.title('Flugprofil')
plt.xlabel('Horizontaler Abstand (m)')
plt.ylabel('Höhe (m)')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(height[:100], fade_margin[:100], c = 'tab:orange', label = 'Ascent')
plt.scatter(height[100], fade_margin[100], c = 'tab:green', zorder = 3, label = 'Apogee')
plt.plot(height[100:], fade_margin[100:], c = 'tab:blue', label = 'Descent')
plt.title('Fade Margin')
plt.xlabel('Höhe (m)')
plt.ylabel('Fade Margin (dB)')
plt.legend()

plt.tight_layout()

plt.savefig('linkbudget_beispiel.png', bbox_inches = 'tight')