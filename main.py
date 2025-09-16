import json
import csv
import matplotlib.pyplot as plt
from fontTools.ttLib.tables.S__i_l_f import attrs_attributes
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap, LogNorm, PowerNorm
import numpy as np

# 1) Load layout positions (only x, y)
with open('layout.json') as f:
    layout = json.load(f)

# 2) Load usage counts
counts = {}
with open('whatpulse-keyboard-heatmap.csv', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        key = row['Keyname']
        counts[key] = counts.get(key, 0) + int(row['Keycount'])
total_presses = sum(counts.values())

# 3) Prepare colormap (WhatPulse-like, gamma-scaled)
all_counts = np.array(list(counts.values()), dtype=float)
vmin = float(all_counts.min())
vmax = float(all_counts.max())
if vmin >= vmax: vmax = vmin + 1.0
cmap = LinearSegmentedColormap.from_list(
    'whatpulse', ['#000435', '#1F77B4', '#2CA02C', '#D62728'], N=256
)
norm = PowerNorm(gamma=0.6, vmin=vmin, vmax=vmax)

# 4) Determine plot bounds
xs, ys = [], []
for attrs in layout.values():
    if not attrs or attrs.get('show') is False:
        continue
    parts = attrs.get('split', [{'x': attrs['x'], 'y': attrs['y']}])
    for pos in parts:
        xs.append(pos['x'])
        ys.append(pos['y'])
max_x, max_y = max(xs) + 1, max(ys) + 1

# 5) Define arbitrary row groups
row_groups = {
    "7-8": [7, 8],
    "6":   [6],
    "5":   [5],
    "4":   [4],
    "3":   [3],
    "0-2": [0, 1, 2],
}
row_percent, row_ypos = {}, {}
for label, ys_grp in row_groups.items():
    tot = 0
    for key, attrs in layout.items():
        if not attrs or attrs.get('show') is False:
            continue
        for pos in attrs.get('split', [{'x': attrs['x'], 'y': attrs['y']}]):
            if pos['y'] in ys_grp:
                tot += counts.get(key, 0)
    row_percent[label] = tot / total_presses * 100
    row_ypos[label] = np.mean(ys_grp) + 0.5

# 6) Define column groups
column_groups = {
    'pinky':    lambda x, y: x <= 1,
    'ring':     lambda x, y: x == 2,
    'middle':   lambda x, y: x == 3,
    'index':    lambda x, y: x == 4 or (x == 5 and y > 2),
    'thumb':    lambda x, y: y <= 2 and 5 <= x <= 7,
    'thumb_r':  lambda x, y: y <= 2 and 9 <= x <= 11,
    'index_r':  lambda x, y: (x == 11 and y > 2) or x == 12,
    'middle_r': lambda x, y: x == 13,
    'ring_r':   lambda x, y: x == 14,
    'pinky_r':  lambda x, y: x >= 15,
}
col_percent = {}
group_x = {}
for name, fn in column_groups.items():
    total = 0
    xs_grp = []
    for key, attrs in layout.items():
        if not attrs or attrs.get('show') is False:
            continue
        for pos in attrs.get('split', [{'x': attrs['x'], 'y': attrs['y']}]):
            if fn(pos['x'], pos['y']):
                total += counts.get(key, 0)
                xs_grp.append(pos['x'])
    col_percent[name] = total / total_presses * 100
    group_x[name] = np.mean(xs_grp) if xs_grp else 0

# 7) Draw heatmap
fig, ax = plt.subplots(figsize=(max_x / 2, max_y / 2))
for key, attrs in layout.items():
    if not attrs or attrs.get('show') is False:
        continue
    color = cmap(norm(counts.get(key, 0)))
    for pos in attrs.get('split', [{'x': attrs['x'], 'y': attrs['y']}]):
        x, y = pos['x'], pos['y']
        ax.add_patch(Rectangle((x, y), 1, 1, facecolor=color, edgecolor='black'))
        ax.text(x + 0.5, y + 0.5, key, ha='center', va='center', fontsize=6, color='white')

ax.set_xlim(0, max_x)
ax.set_ylim(0, max_y)
ax.set_aspect('equal')
ax.axis('off')

# 8) Overlay row percentages
for label, pct in row_percent.items():
    ax.text(max_x / 2, row_ypos[label], f"{pct:.1f}%", ha='center', va='center',
            fontsize=8, color='black')

# 9) Overlay column percentages
for name, pct in col_percent.items():
    ax.text(group_x[name] + 0.5, -1, f"{pct:.1f}%", ha='center', va='top',
            fontsize=8, color='black')

plt.tight_layout()
plt.savefig('advantage-heatmap.png', dpi=200)

# 10) Print distributions
print("Row distribution (% of total):")
for label, pct in row_percent.items():
    print(f" Rows {label}: {pct:.1f}%")
print("\nColumn distribution (% of total):")
for name, pct in col_percent.items():
    print(f" {name}: {pct:.1f}%")

