import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

### Figure Initialisation ###

fig = plt.figure(figsize = (20 / 2.54, 20 / 2.54), dpi = 100)
ax = fig.add_axes([0.0, 0.0, 1, 1])
ax.set_axis_off()
ax.set_xlim(-100, 100)    
ax.set_ylim(-100, 100)

### M8 Holes ###

for phi in range(0, 360, 45):
    
    x = 87.5 * np.cos(phi * np.pi / 180)
    y = 87.5 * np.sin(phi * np.pi / 180)
    
    ax.add_patch(patches.Circle((x, y), radius = 4.2, edgecolor = 'k', fill = False, linewidth = 0.3))
    ax.add_patch(patches.Circle((x, y), radius = 0.3, color = 'k', linewidth = 0))
    
### GFK Rod Hole ###

ax.add_patch(patches.Circle((0, 0), radius = 15.2, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((0, 0), radius = 0.3, color = 'k', linewidth = 0))

### SMA Connector ###

ax.add_patch(patches.Circle((49.42, 0), radius = 2.25, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((49.42, 0), radius = 0.3, color = 'k', linewidth = 0))

ax.add_patch(patches.Circle((49.42 + 8.64 / 2, +8.64 / 2), radius = 1.3, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((49.42 + 8.64 / 2, +8.64 / 2), radius = 0.3, color = 'k', linewidth = 0))

ax.add_patch(patches.Circle((49.42 + 8.64 / 2, -8.64 / 2), radius = 1.3, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((49.42 + 8.64 / 2, -8.64 / 2), radius = 0.3, color = 'k', linewidth = 0))

ax.add_patch(patches.Circle((49.42 - 8.64 / 2, +8.64 / 2), radius = 1.3, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((49.42 - 8.64 / 2, +8.64 / 2), radius = 0.3, color = 'k', linewidth = 0))

ax.add_patch(patches.Circle((49.42 - 8.64 / 2, -8.64 / 2), radius = 1.3, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((49.42 - 8.64 / 2, -8.64 / 2), radius = 0.3, color = 'k', linewidth = 0))
    
### Scale Bar ###

ax.plot([37.5, 87.5], [87.5, 87.5], color = 'k', lw = 1)
ax.annotate('5 cm', (62.5, 92.5), horizontalalignment = 'center', verticalalignment = 'center', fontsize = 'x-large')

### Groundplane Orientierung ###

ax.add_patch(patches.Rectangle((-97.5, 97.5), 20, -20, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.annotate('Groundplane\nOrientation', (-72, 87.5), horizontalalignment = 'left', verticalalignment = 'center', fontsize = 'x-large')
    
### Template Save ###

fig.savefig('drilling_template.pdf', bbox_inches = 'tight', pad_inches = 0)