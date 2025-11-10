import time
import redis
import subprocess
import csv
from datetime import datetime

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

results = []

def get_latest_counts():
    """Get number of devices with recent data in Redis"""
    keys = r.keys('latest:*')
    return len(keys)

def run_test():
    print("=" * 70)
    print("FAILURE RECOVERY TEST")
    print("=" * 70)
    
    # Phase 1: Normal operation (30 seconds)
    print("\n📊 Phase 1: Normal Operation (30s)")
    print("   Measuring baseline...")
    time.sleep(30)
    
    baseline = get_latest_counts()
    print(f"   ✅ Baseline: {baseline} devices with cached data")
    
    results.append({
        'timestamp': datetime.now().isoformat(),
        'phase': 'baseline',
        'devices_cached': baseline,
        'notes': 'Normal operation'
    })
    
    # Phase 2: Kill consumer
    print("\n💥 Phase 2: Simulating Consumer Failure")
    print("   ⚠️  MANUALLY STOP THE CONSUMER NOW (Ctrl+C in consumer terminal)")
    print("   Press Enter once consumer is stopped...")
    input()
    
    failure_time = datetime.now()
    print(f"   🕐 Failure recorded at: {failure_time.strftime('%H:%M:%S')}")
    
    results.append({
        'timestamp': failure_time.isoformat(),
        'phase': 'failure',
        'devices_cached': get_latest_counts(),
        'notes': 'Consumer stopped'
    })
    
    # Phase 3: Wait during failure (60 seconds)
    print("\n⏳ Phase 3: Downtime Period (60s)")
    print("   Messages are piling up in MQTT broker...")
    
    for i in range(12):
        time.sleep(5)
        cached = get_latest_counts()
        age = (datetime.now() - failure_time).seconds
        print(f"   [{age}s] Cached devices: {cached}")
        
        results.append({
            'timestamp': datetime.now().isoformat(),
            'phase': 'downtime',
            'devices_cached': cached,
            'notes': f'Downtime {age}s'
        })
    
    # Phase 4: Restart consumer
    print("\n🔄 Phase 4: Recovery")
    print("   ⚡ MANUALLY RESTART THE CONSUMER NOW")
    print("   Press Enter once consumer is restarted...")
    input()
    
    recovery_start = datetime.now()
    print(f"   🕐 Recovery started at: {recovery_start.strftime('%H:%M:%S')}")
    
    results.append({
        'timestamp': recovery_start.isoformat(),
        'phase': 'recovery_start',
        'devices_cached': get_latest_counts(),
        'notes': 'Consumer restarted'
    })
    
    # Phase 5: Monitor recovery (90 seconds)
    print("\n📈 Phase 5: Monitoring Recovery (90s)")
    print("   Watching cache repopulation...")
    
    for i in range(18):
        time.sleep(5)
        cached = get_latest_counts()
        age = (datetime.now() - recovery_start).seconds
        
        # Check if fully recovered
        if cached >= baseline:
            print(f"   [{age}s] ✅ FULLY RECOVERED! All {cached} devices cached")
            results.append({
                'timestamp': datetime.now().isoformat(),
                'phase': 'recovered',
                'devices_cached': cached,
                'notes': f'Full recovery in {age}s'
            })
            break
        else:
            print(f"   [{age}s] Cached devices: {cached}/{baseline} ({cached/baseline*100:.1f}%)")
            results.append({
                'timestamp': datetime.now().isoformat(),
                'phase': 'recovering',
                'devices_cached': cached,
                'notes': f'Recovery progress {age}s'
            })
    
    # Save results
    with open('../../docs/recovery-test-results.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'phase', 'devices_cached', 'notes'])
        writer.writeheader()
        writer.writerows(results)
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"📊 Results saved to: docs/recovery-test-results.csv")
    print(f"\n🔍 Summary:")
    print(f"   Baseline devices: {baseline}")
    print(f"   Downtime: 60 seconds")
    print(f"   Recovery time: {(datetime.now() - recovery_start).seconds}s")

if __name__ == "__main__":
    try:
        run_test()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        # Save partial results
        if results:
            with open('../../docs/recovery-test-results-partial.csv', 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'phase', 'devices_cached', 'notes'])
                writer.writeheader()
                writer.writerows(results)
            print("📊 Partial results saved")