import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Read results
df = pd.read_csv('../../docs/recovery-test-results.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['seconds'] = (df['timestamp'] - df['timestamp'].iloc[0]).dt.total_seconds()

# Create visualization
fig, ax = plt.subplots(figsize=(12, 6))

# Plot cached devices over time
ax.plot(df['seconds'], df['devices_cached'], 
        marker='o', linewidth=2, markersize=6, color='#3b82f6')

# Mark phases
phases = df.groupby('phase')['seconds'].agg(['min', 'max'])

# Shade regions
if 'baseline' in phases.index:
    ax.axvspan(phases.loc['baseline', 'min'], phases.loc['baseline', 'max'], 
               alpha=0.2, color='green', label='Normal Operation')

if 'downtime' in phases.index:
    ax.axvspan(phases.loc['downtime', 'min'], phases.loc['downtime', 'max'], 
               alpha=0.3, color='red', label='Consumer Down')

if 'recovering' in phases.index or 'recovered' in phases.index:
    recovery_start = df[df['phase'] == 'recovery_start']['seconds'].iloc[0] if 'recovery_start' in df['phase'].values else phases.loc['recovering', 'min']
    recovery_end = df[df['phase'].isin(['recovering', 'recovered'])]['seconds'].max()
    ax.axvspan(recovery_start, recovery_end, 
               alpha=0.2, color='yellow', label='Recovery')

# Annotations
failure_point = df[df['phase'] == 'failure']['seconds'].iloc[0] if 'failure' in df['phase'].values else None
if failure_point:
    ax.axvline(failure_point, color='red', linestyle='--', linewidth=2)
    ax.text(failure_point, ax.get_ylim()[1] * 0.9, 
            '💥 Consumer Stopped', 
            ha='right', fontsize=11, fontweight='bold', color='red')

recovery_point = df[df['phase'] == 'recovery_start']['seconds'].iloc[0] if 'recovery_start' in df['phase'].values else None
if recovery_point:
    ax.axvline(recovery_point, color='green', linestyle='--', linewidth=2)
    ax.text(recovery_point, ax.get_ylim()[1] * 0.8, 
            '🔄 Consumer Restarted', 
            ha='left', fontsize=11, fontweight='bold', color='green')

ax.set_xlabel('Time (seconds)', fontsize=12)
ax.set_ylabel('Devices with Cached Data', fontsize=12)
ax.set_title('HealthSense Failure Recovery Test', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(loc='lower left', fontsize=10)

plt.tight_layout()
plt.savefig('../../docs/recovery-test-visualization.png', dpi=300, bbox_inches='tight')
print("✅ Visualization saved: docs/recovery-test-visualization.png")
plt.show()