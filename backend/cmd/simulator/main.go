package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
)

// Telemetry represents device sensor data
type Telemetry struct {
	TenantID   string    `json:"tenant_id"`
	DeviceID   string    `json:"device_id"`
	Timestamp  string    `json:"ts"`
	Metrics    Metrics   `json:"metrics"`
	BatteryPct int       `json:"battery_pct"`
	FWVersion  string    `json:"fw_version"`
}

type Metrics struct {
	HeartRate int     `json:"hr_bpm"`
	TempC     float64 `json:"temp_c"`
	SpO2      int     `json:"spo2_pct"`
	Steps     int     `json:"steps"`
}

var globalMetrics *MetricsTracker

func main() {
	// Command-line flags
	broker := flag.String("broker", "tcp://localhost:1883", "MQTT broker URL")
	numDevices := flag.Int("devices", 5, "Number of simulated devices")
	interval := flag.Duration("interval", 2*time.Second, "Publishing interval")
	tenantID := flag.String("tenant", "acme-clinic", "Tenant ID")
	duration := flag.Duration("duration", 0, "Test duration (0 = infinite)")
	metricsFile := flag.String("metrics", "simulator-metrics.csv", "Metrics output file")
	flag.Parse()

	log.Printf("🚀 Starting HealthSense Simulator")
	log.Printf("   Broker: %s", *broker)
	log.Printf("   Devices: %d", *numDevices)
	log.Printf("   Interval: %v", *interval)
	log.Printf("   Tenant: %s", *tenantID)
	if *duration > 0 {
		log.Printf("   Duration: %v", *duration)
	}

	// Initialize metrics
	var err error
	globalMetrics, err = NewMetrics(*metricsFile)
	if err != nil {
		log.Fatalf("❌ Failed to initialize metrics: %v", err)
	}
	defer globalMetrics.Flush()

	// Start metrics reporter
	go metricsReporter()

	// MQTT client options
	opts := mqtt.NewClientOptions()
	opts.AddBroker(*broker)
	opts.SetClientID(fmt.Sprintf("simulator-%d", time.Now().Unix()))
	opts.SetKeepAlive(60 * time.Second)
	opts.SetPingTimeout(10 * time.Second)
	opts.SetAutoReconnect(true)

	// Connect to broker
	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		log.Fatalf("❌ Failed to connect to broker: %v", token.Error())
	}
	log.Printf("✅ Connected to MQTT broker")

	// Wait group for graceful shutdown
	var wg sync.WaitGroup
	ctx, cancel := context.WithCancel(context.Background())

	// If duration is set, auto-cancel after duration
	if *duration > 0 {
		go func() {
			time.Sleep(*duration)
			log.Println("⏰ Test duration reached, shutting down...")
			cancel()
		}()
	}

	// Start device goroutines
	for i := 0; i < *numDevices; i++ {
		wg.Add(1)
		deviceID := fmt.Sprintf("watch-%04d", i)
		go publishTelemetry(ctx, &wg, client, *tenantID, deviceID, *interval)
	}

	// Wait for interrupt signal
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)
	
	select {
	case <-sigChan:
		log.Println("🛑 Received interrupt signal...")
	case <-ctx.Done():
		log.Println("🛑 Context cancelled...")
	}

	cancel()
	wg.Wait()
	client.Disconnect(250)
	
	// Print final metrics
	globalMetrics.PrintStats()
	log.Println("✅ Simulator stopped")
}

func publishTelemetry(ctx context.Context, wg *sync.WaitGroup, client mqtt.Client, tenantID, deviceID string, interval time.Duration) {
	defer wg.Done()

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	// Initialize baseline vitals
	baseHR := 70 + rand.Intn(30)
	baseTemp := 36.5 + rand.Float64()
	baseSpO2 := 95 + rand.Intn(5)
	steps := 0

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			startTime := time.Now()

			// Generate telemetry
			telemetry := Telemetry{
				TenantID:  tenantID,
				DeviceID:  deviceID,
				Timestamp: time.Now().UTC().Format(time.RFC3339),
				Metrics: Metrics{
					HeartRate: baseHR + rand.Intn(21) - 10,
					TempC:     baseTemp + (rand.Float64()*0.4 - 0.2),
					SpO2:      baseSpO2 + rand.Intn(3) - 1,
					Steps:     steps + rand.Intn(50),
				},
				BatteryPct: 100 - rand.Intn(30),
				FWVersion:  "1.3.2",
			}
			steps = telemetry.Metrics.Steps

			// Occasionally simulate anomalies (10% chance)
			if rand.Float32() < 0.1 {
				telemetry.Metrics.HeartRate = 150 + rand.Intn(30)
				telemetry.Metrics.TempC = 38.0 + rand.Float64()
			}

			// Publish
			topic := fmt.Sprintf("tenants/%s/devices/%s/telemetry", tenantID, deviceID)
			payload, _ := json.Marshal(telemetry)

			token := client.Publish(topic, 1, false, payload)
			token.Wait()

			latencyMs := time.Since(startTime).Milliseconds()
			success := token.Error() == nil

			// Record metrics
			globalMetrics.RecordPublish(deviceID, latencyMs, success)

			if !success {
				log.Printf("❌ [%s] Publish error: %v", deviceID, token.Error())
			}
		}
	}
}

// metricsReporter prints stats every 10 seconds
func metricsReporter() {
	ticker := time.NewTicker(10 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		stats := globalMetrics.GetStats()
		log.Printf("📊 Throughput: %.0f msg/s | Published: %d | Errors: %d | Avg Latency: %dms | P95: %dms",
			stats["messages_per_sec"],
			stats["total_published"],
			stats["total_errors"],
			stats["avg_latency_ms"],
			stats["p95_latency_ms"],
		)
	}
}