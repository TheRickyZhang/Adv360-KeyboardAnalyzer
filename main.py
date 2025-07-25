import json
import csv
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
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
        count = int(row['Keycount'])
        counts[key] = counts.get(key, 0) + count

total_presses = sum(counts.values())

# 3) Prepare colormap
all_counts = np.array(list(counts.values()))
norm = plt.Normalize(vmin=all_counts.min(), vmax=all_counts.max())
cmap = plt.get_cmap('hot')

# 4) Determine plot bounds, including split positions
xs, ys = [], []
for attrs in layout.values():
    if not attrs or attrs.get('show') is False:
        continue
    if 'split' in attrs:
        for part in attrs['split']:
            xs.append(part['x'])
            ys.append(part['y'])
    else:
        xs.append(attrs['x'])
        ys.append(attrs['y'])
max_x, max_y = max(xs) + 1, max(ys) + 1

# 5) Compute row percentages for y = 7,6,5,4,3
row_percent = {}
for y in [7, 6, 5, 4, 3]:
    row_sum = 0
    for key, attrs in layout.items():
        if not attrs or attrs.get('show') is False:
            continue
        positions = attrs.get('split', [{'x': attrs['x'], 'y': attrs['y']}])
        for pos in positions:
            if pos['y'] == y:
                row_sum += counts.get(key, 0)
    row_percent[y] = row_sum / total_presses * 100

# 6) Define column groups (finger zones)
column_groups = {
    'pinky':    lambda x, y: x in [0, 1],
    'ring':     lambda x, y: x == 2,
    'middle':   lambda x, y: x == 3,
    'index':    lambda x, y: x == 4 or (x == 5 and y > 2),
    'thumb':    lambda x, y: y <= 2 and 5 <= x <= 7,
    'thumb_r':  lambda x, y: y <= 2 and 9 <= x <= 11,
    'index_r':  lambda x, y: (x == 11 and y > 2) or x == 12,
    'middle_r': lambda x, y: x == 13,
    'ring_r':   lambda x, y: x == 14,
    'pinky_r':  lambda x, y: x in [15, 16],
}

col_counts = {name: [] for name in column_groups}
col_percent = dict.fromkeys(column_groups, 0)
group_x = {}

# Collect counts and x positions
for name, fn in column_groups.items():
    xs_group = []
    total = 0
    for key, attrs in layout.items():
        if not attrs or attrs.get('show') is False:
            continue
        positions = attrs.get('split', [{'x': attrs['x'], 'y': attrs['y']}])
        for pos in positions:
            if fn(pos['x'], pos['y']):
                total += counts.get(key, 0)
                xs_group.append(pos['x'])
    col_percent[name] = total / total_presses * 100
    group_x[name] = np.mean(xs_group) if xs_group else 0

# 7) Draw heatmap
fig, ax = plt.subplots(figsize=(max_x / 2, max_y / 2))
for key, attrs in layout.items():
    if not attrs or attrs.get('show') is False:
        continue
    color = cmap(norm(counts.get(key, 0)))
    positions = attrs.get('split', [{'x': attrs['x'], 'y': attrs['y']}])
    for pos in positions:
        x, y = pos['x'], pos['y']
        ax.add_patch(Rectangle((x, y), 1, 1, facecolor=color, edgecolor='black'))
        ax.text(x + 0.5, y + 0.5, key, ha='center', va='center', fontsize=6, color='white')

ax.set_xlim(0, max_x)
ax.set_ylim(0, max_y)
ax.set_aspect('equal')
ax.axis('off')

# 8) Overlay row percentages at center of each row
for y, pct in row_percent.items():
    ax.text(max_x / 2, y + 0.5, f"{pct:.1f}%", ha='center', va='center',
            fontsize=8, color='black', backgroundcolor='white')

# 9) Overlay column percentages at bottom
for name, pct in col_percent.items():
    x = group_x[name]
    ax.text(x + 0.5, -1, f"{pct:.1f}%", ha='center', va='top',
            fontsize=8, color='black', backgroundcolor='white')

plt.tight_layout()
plt.savefig('advantage-heatmap.png', dpi=200)

# 10) Print row and column distributions
print("Row distribution (% of total):")
for y, pct in row_percent.items():
    print(f" Row {y}: {pct:.1f}%")
print("\nColumn distribution (% of total):")
for name, pct in col_percent.items():
    print(f" {name}: {pct:.1f}%")
