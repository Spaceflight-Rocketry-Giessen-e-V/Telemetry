import matplotlib.pyplot as plt
import numpy as np

# Verbesserungen an der Berechnung:
# - Fundierte Abschätzung L_TX und L_RX
# - Festlegung auf Gewinn der Empfängerantenne
# - Einbeziehung des realen Gewinns der Senderantenne
# - Realistisches Höhenprofil

f = 869.5e+6                # 869.5 MHz

P_TX = 27                   # Datenblatt RC1780HP-RC232
G_TX = 0                    # QFH-Antenne (tatsächlicher Gewinn ungleich 0 und abhängig vom Winkel)
L_TX = 3                    # Abschätzung

P_RX = -114                 # Datenblatt RC1780HP-RC232, alternativ: P_RX = -118
G_RX = 10                   # Helixantenne, erste Abschätzung
L_RX = 3                    # Abschätzung

displacement = np.append(np.linspace(1000, 1000, 100), np.linspace(1000, 19000, 100))       # Horizontaler Abstand
height = np.append(np.linspace(0, 9000, 100), np.linspace(9000, 0, 100))                    # Vertikaler Abstand
distance = np.sqrt(height**2 + displacement**2)                                             # Abstand

L_FS = 20 * np.log10((4 * np.pi * distance * f)/(2.998e+8))                                 # Freiraumdämpfung

L_M = P_TX - P_RX + G_TX + G_RX - L_FS - L_TX - L_RX                                        # Link Margin

print('\nMinimale Link Margin während des Flugprofils: ' + str(np.min(L_M)) + ' dB')

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
plt.plot(height[:100], L_M[:100], c = 'tab:orange', label = 'Ascent')
plt.scatter(height[100], L_M[100], c = 'tab:green', zorder = 3, label = 'Apogee')
plt.plot(height[100:], L_M[100:], c = 'tab:blue', label = 'Descent')
plt.title('Berechnung $L_\mathrm{M}$ (Link Margin)')
plt.xlabel('Höhe (m)')
plt.ylabel('$L_\mathrm{M}$ (Link Margin) (dB)')
plt.legend()

plt.tight_layout()

# plt.savefig('linkbudget_beispiel.png', bbox_inches = 'tight')