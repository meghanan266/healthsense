package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"sync"
	"time"
	"strings"
)

// MetricsTracker tracks simulator performance
type MetricsTracker struct {
	mu                sync.RWMutex
	publishCount      int64
	publishErrors     int64
	totalLatencyMs    int64
	startTime         time.Time
	latencies         []int64
	csvWriter         *csv.Writer
	csvFile           *os.File
}

// NewMetrics creates a new metrics tracker
func NewMetrics(outputFile string) (*MetricsTracker, error) {
	file, err := os.Create(outputFile)
	if err != nil {
		return nil, fmt.Errorf("failed to create metrics file: %w", err)
	}

	writer := csv.NewWriter(file)
	// Write CSV header
	writer.Write([]string{"timestamp", "device_id", "publish_latency_ms", "success"})
	writer.Flush()

	return &MetricsTracker{
		startTime: time.Now(),
		csvWriter: writer,
		csvFile:   file,
		latencies: make([]int64, 0, 10000),
	}, nil
}

// RecordPublish records a publish event
func (m *MetricsTracker) RecordPublish(deviceID string, latencyMs int64, success bool) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if success {
		m.publishCount++
		m.totalLatencyMs += latencyMs
		m.latencies = append(m.latencies, latencyMs)
	} else {
		m.publishErrors++
	}

	// Write to CSV
	successStr := "1"
	if !success {
		successStr = "0"
	}
	m.csvWriter.Write([]string{
		time.Now().Format(time.RFC3339),
		deviceID,
		fmt.Sprintf("%d", latencyMs),
		successStr,
	})
}

// GetStats returns current statistics
func (m *MetricsTracker) GetStats() map[string]interface{} {
	m.mu.RLock()
	defer m.mu.RUnlock()

	elapsed := time.Since(m.startTime).Seconds()
	avgLatency := int64(0)
	if m.publishCount > 0 {
		avgLatency = m.totalLatencyMs / m.publishCount
	}

	p50, p95, p99 := m.calculatePercentiles()

	return map[string]interface{}{
		"total_published":  m.publishCount,
		"total_errors":     m.publishErrors,
		"messages_per_sec": float64(m.publishCount) / elapsed,
		"avg_latency_ms":   avgLatency,
		"p50_latency_ms":   p50,
		"p95_latency_ms":   p95,
		"p99_latency_ms":   p99,
		"elapsed_sec":      elapsed,
	}
}

// calculatePercentiles calculates latency percentiles
func (m *MetricsTracker) calculatePercentiles() (p50, p95, p99 int64) {
	if len(m.latencies) == 0 {
		return 0, 0, 0
	}

	// Simple percentile calculation (not sorted, approximate)
	sorted := make([]int64, len(m.latencies))
	copy(sorted, m.latencies)
	
	// Bubble sort (good enough for small datasets)
	for i := 0; i < len(sorted); i++ {
		for j := i + 1; j < len(sorted); j++ {
			if sorted[i] > sorted[j] {
				sorted[i], sorted[j] = sorted[j], sorted[i]
			}
		}
	}

	p50 = sorted[len(sorted)*50/100]
	p95 = sorted[len(sorted)*95/100]
	p99 = sorted[len(sorted)*99/100]

	return
}

// Flush writes any buffered data and closes the file
func (m *MetricsTracker) Flush() {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.csvWriter.Flush()
	m.csvFile.Close()
}

// PrintStats prints current statistics to console
func (m *MetricsTracker) PrintStats() {
	stats := m.GetStats()
	separator := strings.Repeat("=", 60)
	
	fmt.Println("\n" + separator)
	fmt.Println("SIMULATOR METRICS")
	fmt.Println(separator)
	fmt.Printf("Total Published:     %d messages\n", stats["total_published"])
	fmt.Printf("Total Errors:        %d\n", stats["total_errors"])
	fmt.Printf("Throughput:          %.2f msg/sec\n", stats["messages_per_sec"])
	fmt.Printf("Avg Latency:         %d ms\n", stats["avg_latency_ms"])
	fmt.Printf("P50 Latency:         %d ms\n", stats["p50_latency_ms"])
	fmt.Printf("P95 Latency:         %d ms\n", stats["p95_latency_ms"])
	fmt.Printf("P99 Latency:         %d ms\n", stats["p99_latency_ms"])
	fmt.Printf("Elapsed Time:        %.2f sec\n", stats["elapsed_sec"])
	fmt.Println(separator)
}