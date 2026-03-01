/**
 * API Latency Benchmark
 * Tests API fetch latency for key endpoints
 * Runs 1000 requests per endpoint
 */

class APILatencyBenchmark {
    constructor() {
        this.endpoints = [
            { path: '/metrics', method: 'GET', name: 'Market Metrics' },
            { path: '/signals', method: 'GET', name: 'Trading Signals' },
            { path: '/market-state', method: 'GET', name: 'Market State' },
            { path: '/api/v1/market/metrics', method: 'GET', name: 'API v1 Metrics' },
            { path: '/api/v1/signals/recent', method: 'GET', name: 'Recent Signals' },
            { path: '/health', method: 'GET', name: 'Health Check' }
        ];
        this.baseUrl = 'http://localhost:8000'; // Adjust as needed
        this.results = new Map();
        this.totalRequests = 0;
        this.successfulRequests = 0;
        this.failedRequests = 0;
    }

    // Make HTTP request with timing
    async makeRequest(endpoint, timeout = 10000) {
        const startTime = performance.now();
        let response;
        let error = null;
        
        try {
            const url = `${this.baseUrl}${endpoint.path}`;
            const options = {
                method: endpoint.method,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                signal: AbortSignal.timeout(timeout)
            };
            
            response = await fetch(url, options);
            
            const endTime = performance.now();
            const latency = endTime - startTime;
            
            // Consume response body
            const responseText = await response.text();
            
            return {
                success: response.ok,
                status: response.status,
                statusText: response.statusText,
                latency: latency,
                responseSize: responseText.length,
                headers: Object.fromEntries(response.headers.entries()),
                endpoint: endpoint.name
            };
            
        } catch (err) {
            const endTime = performance.now();
            const latency = endTime - startTime;
            
            return {
                success: false,
                status: 0,
                statusText: err.name,
                latency: latency,
                error: err.message,
                endpoint: endpoint.name
            };
        }
    }

    // Warm up connection
    async warmUpConnection() {
        console.log("Warming up connection...");
        
        try {
            await this.makeRequest(this.endpoints[0], 5000);
            console.log("✅ Connection warm-up complete");
        } catch (error) {
            console.log("⚠️  Connection warm-up failed:", error.message);
        }
    }

    // Run benchmark for single endpoint
    async runEndpointBenchmark(endpoint, requestCount = 1000) {
        console.log(`\n🔍 Benchmarking ${endpoint.name} (${requestCount} requests)`);
        
        const latencies = [];
        const results = {
            endpoint: endpoint.name,
            path: endpoint.path,
            method: endpoint.method,
            requestCount: requestCount,
            latencies: [],
            successCount: 0,
            errorCount: 0,
            statusCodes: new Map(),
            errors: []
        };
        
        // Run requests in batches to avoid overwhelming the server
        const batchSize = 50;
        const batches = Math.ceil(requestCount / batchSize);
        
        for (let batch = 0; batch < batches; batch++) {
            const batchPromises = [];
            
            // Create batch of concurrent requests
            for (let i = 0; i < batchSize && (batch * batchSize + i) < requestCount; i++) {
                const requestPromise = this.makeRequest(endpoint);
                batchPromises.push(requestPromise);
            }
            
            // Wait for batch to complete
            try {
                const batchResults = await Promise.allSettled(batchPromises);
                
                // Process batch results
                batchResults.forEach((result, index) => {
                    if (result.status === 'fulfilled') {
                        const response = result.value;
                        results.latencies.push(response.latency);
                        
                        if (response.success) {
                            results.successCount++;
                            
                            // Track status codes
                            const statusCode = response.status;
                            results.statusCodes.set(statusCode, (results.statusCodes.get(statusCode) || 0) + 1);
                        } else {
                            results.errorCount++;
                            
                            if (response.error) {
                                results.errors.push({
                                    error: response.error,
                                    status: response.status,
                                    latency: response.latency
                                });
                            }
                        }
                    } else {
                        results.errorCount++;
                        results.errors.push({
                            error: result.reason.message,
                            reason: result.reason
                        });
                    }
                });
                
            } catch (error) {
                console.error(`Batch ${batch} error:`, error);
                results.errorCount += batchSize;
            }
            
            // Progress indicator
            const completed = Math.min((batch + 1) * batchSize, requestCount);
            console.log(`  Progress: ${completed}/${requestCount} requests`);
            
            // Small delay between batches to be respectful to the server
            if (batch < batches - 1) {
                await new Promise(resolve => setTimeout(resolve, 10));
            }
        }
        
        return results;
    }

    // Calculate statistics for endpoint results
    calculateEndpointStats(results) {
        if (results.latencies.length === 0) {
            return {
                avgLatency: 0,
                minLatency: 0,
                maxLatency: 0,
                p50Latency: 0,
                p95Latency: 0,
                p99Latency: 0,
                stdDeviation: 0,
                successRate: 0,
                requestsPerSecond: 0
            };
        }
        
        const latencies = results.latencies.sort((a, b) => a - b);
        const count = latencies.length;
        
        // Basic statistics
        const avgLatency = latencies.reduce((sum, lat) => sum + lat, 0) / count;
        const minLatency = latencies[0];
        const maxLatency = latencies[count - 1];
        
        // Percentiles
        const p50Latency = latencies[Math.floor(count * 0.5)];
        const p95Latency = latencies[Math.floor(count * 0.95)];
        const p99Latency = latencies[Math.floor(count * 0.99)];
        
        // Standard deviation
        const variance = latencies.reduce((sum, lat) => sum + Math.pow(lat - avgLatency, 2), 0) / count;
        const stdDeviation = Math.sqrt(variance);
        
        // Success rate and throughput
        const successRate = (results.successCount / results.requestCount) * 100;
        const totalTime = Math.max(...latencies); // Approximate total time
        const requestsPerSecond = results.requestCount / (totalTime / 1000);
        
        return {
            avgLatency,
            minLatency,
            maxLatency,
            p50Latency,
            p95Latency,
            p99Latency,
            stdDeviation,
            successRate,
            requestsPerSecond
        };
    }

    // Run complete API benchmark
    async runAPIBenchmark(requestsPerEndpoint = 1000) {
        console.log(`🚀 Starting API Latency Benchmark (${requestsPerEndpoint} requests per endpoint)`);
        console.log("=" * 80);
        console.log(`Testing ${this.endpoints.length} endpoints against ${this.baseUrl}`);
        console.log("=" * 80);
        
        // Check if server is available
        console.log("Checking server availability...");
        try {
            const healthCheck = await this.makeRequest(this.endpoints.find(e => e.path === '/health') || this.endpoints[0], 5000);
            if (!healthCheck.success) {
                console.log("⚠️  Server health check failed, but continuing with benchmark...");
            } else {
                console.log("✅ Server is available");
            }
        } catch (error) {
            console.log("❌ Server is not available. Please start the server before running benchmarks.");
            return null;
        }
        
        // Warm up connection
        await this.warmUpConnection();
        
        // Run benchmarks for each endpoint
        const allResults = [];
        
        for (const endpoint of this.endpoints) {
            try {
                const results = await this.runEndpointBenchmark(endpoint, requestsPerEndpoint);
                const stats = this.calculateEndpointStats(results);
                
                allResults.push({
                    ...results,
                    ...stats
                });
                
                // Print immediate results
                console.log(`✅ ${endpoint.name}:`);
                console.log(`   Average: ${stats.avgLatency.toFixed(3)} ms`);
                console.log(`   Max: ${stats.maxLatency.toFixed(3)} ms`);
                console.log(`   P95: ${stats.p95Latency.toFixed(3)} ms`);
                console.log(`   Success Rate: ${stats.successRate.toFixed(1)}%`);
                console.log(`   Requests/sec: ${stats.requestsPerSecond.toFixed(1)}`);
                
                if (results.errors.length > 0) {
                    console.log(`   Errors: ${results.errors.length}`);
                }
                
            } catch (error) {
                console.error(`❌ Failed to benchmark ${endpoint.name}:`, error.message);
                
                allResults.push({
                    endpoint: endpoint.name,
                    path: endpoint.path,
                    method: endpoint.method,
                    requestCount: requestsPerEndpoint,
                    successCount: 0,
                    errorCount: requestsPerEndpoint,
                    avgLatency: 0,
                    maxLatency: 0,
                    minLatency: 0,
                    p50Latency: 0,
                    p95Latency: 0,
                    p99Latency: 0,
                    successRate: 0,
                    requestsPerSecond: 0,
                    errors: [{ error: error.message }]
                });
            }
        }
        
        return allResults;
    }

    // Print comprehensive results
    printResults(allResults) {
        if (!allResults || allResults.length === 0) {
            console.log("❌ No results to display");
            return;
        }
        
        console.log("\n" + "=" * 100);
        console.log("📊 API LATENCY PERFORMANCE RESULTS");
        console.log("=" * 100);
        
        // Summary table
        console.log(f"{'Endpoint':<25} | {'Method':<6} | {'Avg ms':<8} | {'Max ms':<8} | {'P95 ms':<8} | {'Success %':<10} | {'Req/sec':<10}");
        console.log("-" * 100);
        
        let totalRequests = 0;
        let totalSuccessful = 0;
        let totalLatency = 0;
        
        allResults.forEach(results => {
            console.log(`${results.endpoint:<25} | ${results.method:<6} | ${results.avgLatency:<8.3f} | ${results.maxLatency:<8.3f} | ${results.p95Latency:<8.3f} | ${results.successRate:<10.1f} | ${results.requestsPerSecond:<10.1f}`);
            
            totalRequests += results.requestCount;
            totalSuccessful += results.successCount;
            totalLatency += results.avgLatency * results.requestCount;
        });
        
        // Overall statistics
        const overallSuccessRate = (totalSuccessful / totalRequests) * 100;
        const overallAvgLatency = totalLatency / totalRequests;
        
        console.log("\n" + "=" * 100);
        console.log("📈 OVERALL STATISTICS");
        console.log("=" * 100);
        console.log(`Total Requests: ${totalRequests}`);
        console.log(`Successful Requests: ${totalSuccessful}`);
        console.log(`Failed Requests: ${totalRequests - totalSuccessful}`);
        console.log(`Overall Success Rate: ${overallSuccessRate.toFixed(1)}%`);
        console.log(`Overall Average Latency: ${overallAvgLatency.toFixed(3)} ms`);
        
        // Best and worst performers
        const successfulResults = allResults.filter(r => r.successCount > 0);
        if (successfulResults.length > 0) {
            const fastest = successfulResults.reduce((min, curr) => curr.avgLatency < min.avgLatency ? curr : min);
            const slowest = successfulResults.reduce((max, curr) => curr.avgLatency > max.avgLatency ? curr : max);
            const highestThroughput = successfulResults.reduce((max, curr) => curr.requestsPerSecond > max.requestsPerSecond ? curr : max);
            
            console.log(`\n🏆 Fastest Endpoint: ${fastest.endpoint} (${fastest.avgLatency.toFixed(3)} ms)`);
            console.log(`⚠️  Slowest Endpoint: ${slowest.endpoint} (${slowest.avgLatency.toFixed(3)} ms)`);
            console.log(`🚀 Highest Throughput: ${highestThroughput.endpoint} (${highestThroughput.requestsPerSecond.toFixed(1)} req/sec)`);
        }
        
        // Error analysis
        const errorResults = allResults.filter(r => r.errors.length > 0);
        if (errorResults.length > 0) {
            console.log("\n⚠️  ERROR ANALYSIS:");
            console.log("-" * 50);
            
            errorResults.forEach(results => {
                console.log(`${results.endpoint}:`);
                console.log(`  Errors: ${results.errors.length}/${results.requestCount}`);
                
                // Show unique error types
                const errorTypes = new Map();
                results.errors.forEach(error => {
                    const type = error.error || 'Unknown';
                    errorTypes.set(type, (errorTypes.get(type) || 0) + 1);
                });
                
                errorTypes.forEach((count, type) => {
                    console.log(`    ${type}: ${count}`);
                });
            });
        }
        
        // Success criteria check
        console.log("\n🎯 SUCCESS CRITERIA CHECK:");
        console.log("-" * 50);
        
        const allUnder50ms = successfulResults.every(r => r.avgLatency < 50.0);
        const allHighSuccess = successfulResults.every(r => r.successRate > 95.0);
        const goodOverallSuccess = overallSuccessRate > 95.0;
        
        console.log(`All endpoints < 50ms: ${allUnder50ms ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`All endpoints > 95% success: ${allHighSuccess ? '✅ PASS' : '❌ FAIL'}`);
        console.log(`Overall success > 95%: ${goodOverallSuccess ? '✅ PASS' : '❌ FAIL'}`);
        
        if (allUnder50ms && allHighSuccess && goodOverallSuccess) {
            console.log("\n🎉 API LATENCY PERFORMANCE: EXCELLENT");
        } else {
            console.log("\n⚠️  API LATENCY PERFORMANCE: NEEDS OPTIMIZATION");
        }
        
        return allResults;
    }
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APILatencyBenchmark;
}

// Auto-run if executed directly
if (typeof window !== 'undefined') {
    // Browser environment
    window.APILatencyBenchmark = APILatencyBenchmark;
    
    // Auto-run benchmark
    const benchmark = new APILatencyBenchmark();
    benchmark.runAPIBenchmark(1000)
        .then(results => benchmark.printResults(results))
        .catch(error => console.error('Benchmark error:', error));
} else if (typeof global !== 'undefined') {
    // Node.js environment
    global.APILatencyBenchmark = APILatencyBenchmark;
}
