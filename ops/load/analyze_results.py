import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

# Read all test CSV files
csv_files = glob.glob('../../docs/test*.csv')

if not csv_files:
    print("❌ No test CSV files found in docs/")
    exit(1)

print(f"📊 Found {len(csv_files)} test result files")

# Parse results
results = []

for csv_file in sorted(csv_files):
    df = pd.read_csv(csv_file)
    
    # Calculate metrics
    total_messages = len(df)
    success_rate = (df['success'].sum() / total_messages) * 100
    avg_latency = df['publish_latency_ms'].mean()
    p50_latency = df['publish_latency_ms'].quantile(0.50)
    p95_latency = df['publish_latency_ms'].quantile(0.95)
    p99_latency = df['publish_latency_ms'].quantile(0.99)
    
    # Extract device count from filename
    filename = os.path.basename(csv_file)
    if 'baseline' in filename or '10' in filename:
        devices = 10
    elif '50' in filename:
        devices = 50
    elif '100' in filename:
        devices = 100
    elif '500' in filename:
        devices = 500
    elif '1000' in filename:
        devices = 1000
    else:
        devices = 0
    
    results.append({
        'devices': devices,
        'total_messages': total_messages,
        'success_rate': success_rate,
        'avg_latency': avg_latency,
        'p50_latency': p50_latency,
        'p95_latency': p95_latency,
        'p99_latency': p99_latency,
        'throughput': total_messages / 120  # 2 min = 120 sec
    })
    
    print(f"✅ Processed: {filename} ({devices} devices)")

# Create DataFrame
results_df = pd.DataFrame(results).sort_values('devices')

print("\n" + "="*70)
print("LOAD TEST SUMMARY")
print("="*70)
print(results_df.to_string(index=False))
print("="*70)

# Generate graphs
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('HealthSense Load Test Results', fontsize=16, fontweight='bold')

# Graph 1: Throughput vs Devices
axes[0, 0].plot(results_df['devices'], results_df['throughput'], 
                marker='o', linewidth=2, markersize=8, color='#2563eb')
axes[0, 0].set_xlabel('Number of Devices', fontsize=12)
axes[0, 0].set_ylabel('Throughput (msg/sec)', fontsize=12)
axes[0, 0].set_title('Throughput vs Device Scale', fontsize=13, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)

# Graph 2: Latency Percentiles
axes[0, 1].plot(results_df['devices'], results_df['avg_latency'], 
                marker='o', label='Avg', linewidth=2, markersize=8)
axes[0, 1].plot(results_df['devices'], results_df['p50_latency'], 
                marker='s', label='P50', linewidth=2, markersize=8)
axes[0, 1].plot(results_df['devices'], results_df['p95_latency'], 
                marker='^', label='P95', linewidth=2, markersize=8)
axes[0, 1].plot(results_df['devices'], results_df['p99_latency'], 
                marker='d', label='P99', linewidth=2, markersize=8)
axes[0, 1].set_xlabel('Number of Devices', fontsize=12)
axes[0, 1].set_ylabel('Latency (ms)', fontsize=12)
axes[0, 1].set_title('Latency Distribution vs Device Scale', fontsize=13, fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# Graph 3: Success Rate
axes[1, 0].bar(results_df['devices'], results_df['success_rate'], 
               color='#10b981', alpha=0.7, edgecolor='black')
axes[1, 0].set_xlabel('Number of Devices', fontsize=12)
axes[1, 0].set_ylabel('Success Rate (%)', fontsize=12)
axes[1, 0].set_title('Message Success Rate', fontsize=13, fontweight='bold')
axes[1, 0].set_ylim([95, 101])
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Graph 4: Scalability Efficiency
ideal_throughput = results_df['devices'] * (results_df.iloc[0]['throughput'] / results_df.iloc[0]['devices'])
efficiency = (results_df['throughput'] / ideal_throughput) * 100

axes[1, 1].plot(results_df['devices'], efficiency, 
                marker='o', linewidth=2, markersize=8, color='#8b5cf6')
axes[1, 1].axhline(y=100, color='red', linestyle='--', label='Ideal (100%)')
axes[1, 1].set_xlabel('Number of Devices', fontsize=12)
axes[1, 1].set_ylabel('Scaling Efficiency (%)', fontsize=12)
axes[1, 1].set_title('Scalability Efficiency', fontsize=13, fontweight='bold')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('../../docs/load-test-results.png', dpi=300, bbox_inches='tight')
print(f"\n📈 Graph saved: docs/load-test-results.png")

plt.show()