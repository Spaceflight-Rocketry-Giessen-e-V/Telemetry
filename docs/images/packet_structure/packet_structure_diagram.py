import numpy as np
import matplotlib.pyplot as plt
from matplotlib import patches

### Figure ###

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial"]

fig = plt.figure(figsize = (12, 5.25), dpi = 300)
ax1 = fig.add_axes([0, 2.75/5.5, 1, 2.5/5.25])
ax2 = fig.add_axes([0, 0, 1, 2.75/5.25], sharex = ax1)
ax1.set_axis_off()
ax2.set_axis_off()
ax1.set_xlim(-0.01, 12.01)
ax1.set_ylim(-0.8, 1.7)
ax2.set_ylim(-0.8, 2.05)

ax1.annotate('Flight Data Packet', (0, 1.45), c = '#555555', ha = 'left', va = 'center', fontsize = 'xx-large', fontweight = 'bold')
ax2.annotate('Telemetry Data Packet', (0, 1.45), c = '#555555', ha = 'left', va = 'center', fontsize = 'xx-large', fontweight = 'bold')

### Flight Data Packet ###

# Component Colors

BitPositions = np.array([0, 6, 16, 31, 36, 88, 96]) / 8
# Colors = ['#E4BEC5', '#A4BCB0', '#66BFCC', '#BEE9B9', '#85AFDB', '#E4BEC5']
Colors = ['#FFB8B8', '#FFD09B', '#FCE77A', '#9BE2AF', '#9DB8F5', '#FFB8B8']

for i in range(len(BitPositions) - 1):
    ax1.fill_between([BitPositions[i], BitPositions[i + 1]], 0, 1, color = Colors[i])

# Byte Frames

for i in range(12):
    frame = patches.FancyBboxPatch((i + 0.1, 0.1), 1 - 0.2, 0.8, 
                                   fill = False, boxstyle = 'round', mutation_scale = 0.33,
                                   color = '#555555', linewidth = 2)
    ax1.add_patch(frame)
    ax1.annotate('0x0' + hex(i)[2:3].upper(), (i + 0.5, 1.125), ha = 'center', va = 'center', c = '#555555', fontsize = 'large')
    
# Component Names

ax1.annotate('Packet Frame', (BitPositions[0], -0.25), c = Colors[0], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax1.annotate('Acceleration', (BitPositions[1], -0.5), c = Colors[1], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax1.annotate('Height', (BitPositions[2], -0.25), c = Colors[2], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax1.annotate('Flight Events', (BitPositions[3], -0.25), c = Colors[3], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax1.annotate('GNSS Position', (BitPositions[4], -0.5), c = Colors[4], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax1.annotate('Packet Frame', (BitPositions[6], -0.25), c = Colors[5], ha = 'right', va = 'center', fontsize = 'x-large', fontweight = 'bold')
    
### Telemetry Data Packet ###

# Component Colors

BitPositions = np.array([0, 6, 8, 16, 17, 40, 48, 56, 58, 77, 88, 96]) / 8
# Colors = ['#E4BEC5', '#FFFFFF', '#A4BCB0', '#FFFFFF', '#66BFCC', '#BEE9B9', '#85AFDB', '#FFFFFF', '#7FE08C', '#FFFFFF', '#E4BEC5']
Colors = ['#FFB8B8', '#FFFFFF', '#FFD09B', '#FFFFFF', '#FCE77A', '#9BE2AF', '#9DB8F5', '#FFFFFF', '#C697CD', '#FFFFFF', '#FFB8B8']

for i in range(len(BitPositions) - 1):
    ax2.fill_between([BitPositions[i], BitPositions[i + 1]], 0, 1, color = Colors[i])

# Byte Frames

for i in range(12):
    frame = patches.FancyBboxPatch((i + 0.1, 0.1), 1 - 0.2, 0.8, 
                                   fill = False, boxstyle = 'round', mutation_scale = 0.33,
                                   color = '#555555', linewidth = 2)
    ax2.add_patch(frame)
    ax2.annotate('0x0' + hex(i)[2:3].upper(), (i + 0.5, 1.125), ha = 'center', va = 'center', c = '#555555', fontsize = 'large')

# Component Names

ax2.annotate('Packet Frame', (BitPositions[0], -0.25), c = Colors[0], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax2.annotate('Subsystem States', (BitPositions[2], -0.5), c = Colors[2], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax2.annotate('GNNS Status', (BitPositions[4], -0.25), c = Colors[4], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax2.annotate('Temperatures', (BitPositions[5], -0.25), c = Colors[5], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax2.annotate('Flight Control Status', (BitPositions[6], -0.5), c = Colors[6], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax2.annotate('Power Supply Status', (BitPositions[8], -0.25), c = Colors[8], ha = 'left', va = 'center', fontsize = 'x-large', fontweight = 'bold')
ax2.annotate('Packet Frame', (BitPositions[11], -0.25), c = Colors[10], ha = 'right', va = 'center', fontsize = 'x-large', fontweight = 'bold')

### Figure Save ###

fig.savefig('packet_structure_diagram.png', bbox_inches = 'tight', pad_inches = 0.1)