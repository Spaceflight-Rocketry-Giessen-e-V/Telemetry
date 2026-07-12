import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

### Parameters ###

screw_diameter = 109.746
gfk_diameter = 31.4

screw_radius = screw_diameter / 2
gfk_radius = gfk_diameter / 2

### Figure Initialisation ###

fig = plt.figure(figsize = (20 * 0.8 / 2.54, 20 * 0.8 / 2.54), dpi = 100)
ax = fig.add_axes([0.0, 0.0, 1, 1])
ax.set_axis_off()
ax.set_xlim(-80, 80)    
ax.set_ylim(-80, 80)

### M8 Holes ###

for phi in range(0, 360, 45):
    
    if phi % 180 == 0:
        continue
    
    x = screw_radius * np.cos(phi * np.pi / 180)
    y = screw_radius * np.sin(phi * np.pi / 180)
    
    ax.add_patch(patches.Circle((x, y), radius = 4.2, edgecolor = 'k', fill = False, linewidth = 0.3))
    ax.add_patch(patches.Circle((x, y), radius = 0.3, color = 'k', linewidth = 0))
    
### GFK Rod Hole ###

ax.add_patch(patches.Circle((0, 0), radius = gfk_radius, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((0, 0), radius = 0.3, color = 'k', linewidth = 0))

### SMA Connector ###

ax.add_patch(patches.Circle((screw_radius, 0), radius = 2.25, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((screw_radius, 0), radius = 0.3, color = 'k', linewidth = 0))

ax.add_patch(patches.Circle((screw_radius + 8.64 / 2, + 8.64 / 2), radius = 1.3, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((screw_radius + 8.64 / 2, + 8.64 / 2), radius = 0.3, color = 'k', linewidth = 0))

ax.add_patch(patches.Circle((screw_radius + 8.64 / 2, - 8.64 / 2), radius = 1.3, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((screw_radius + 8.64 / 2, - 8.64 / 2), radius = 0.3, color = 'k', linewidth = 0))

ax.add_patch(patches.Circle((screw_radius - 8.64 / 2, + 8.64 / 2), radius = 1.3, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((screw_radius - 8.64 / 2, + 8.64 / 2), radius = 0.3, color = 'k', linewidth = 0))

ax.add_patch(patches.Circle((screw_radius - 8.64 / 2, - 8.64 / 2), radius = 1.3, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.add_patch(patches.Circle((screw_radius - 8.64 / 2, - 8.64 / 2), radius = 0.3, color = 'k', linewidth = 0))
    
### Scale Bar ###

ax.plot([20, 70], [70, 70], color = 'k', lw = 1)
ax.annotate('5 cm', (45, 74), horizontalalignment = 'center', verticalalignment = 'center', fontsize = 'large')

### Groundplane Orientierung ###

ax.add_patch(patches.Rectangle((-80, 80), 20, -20, edgecolor = 'k', fill = False, linewidth = 0.3))
ax.annotate('Groundplane\nOrientation', (-55, 70), horizontalalignment = 'left', verticalalignment = 'center', fontsize = 'large')
    
### Template Save ###

fig.savefig('drilling_template.pdf', bbox_inches = 'tight', pad_inches = 0.1)