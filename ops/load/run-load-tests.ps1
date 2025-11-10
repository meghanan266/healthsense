# HealthSense Load Testing Script
# Tests different device scales and captures metrics

$ErrorActionPreference = "Stop"

Write-Host "🚀 HealthSense Load Testing Suite" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Create results directory
$resultsDir = "../../docs/load-test-results"
New-Item -ItemType Directory -Path $resultsDir -Force | Out-Null

# Test configurations
$tests = @(
    @{ devices = 10; duration = "2m"; name = "baseline-10" },
    @{ devices = 50; duration = "2m"; name = "medium-50" },
    @{ devices = 100; duration = "2m"; name = "high-100" },
    @{ devices = 500; duration = "2m"; name = "stress-500" },
    @{ devices = 1000; duration = "2m"; name = "extreme-1000" }
)

foreach ($test in $tests) {
    Write-Host "`n📊 Running test: $($test.name)" -ForegroundColor Yellow
    Write-Host "   Devices: $($test.devices)" -ForegroundColor Gray
    Write-Host "   Duration: $($test.duration)" -ForegroundColor Gray
    
    $outputFile = "$resultsDir/$($test.name)-metrics.csv"
    
    # Run simulator
    $process = Start-Process -FilePath "go" `
        -ArgumentList "run", "../../backend/cmd/simulator/main.go", `
                      "-devices", $test.devices, `
                      "-duration", $test.duration, `
                      "-interval", "2s", `
                      "-metrics", $outputFile `
        -NoNewWindow -PassThru -Wait
    
    Write-Host "✅ Test completed: $($test.name)" -ForegroundColor Green
    
    # Wait 10 seconds between tests
    Write-Host "⏳ Cooling down for 10 seconds..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
}

Write-Host "`n🎉 All load tests completed!" -ForegroundColor Green
Write-Host "Results saved to: $resultsDir" -ForegroundColor Cyan