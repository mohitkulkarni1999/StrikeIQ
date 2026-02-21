#!/usr/bin/env python3
"""
Analyze Collected Tick Metrics
Standalone script to analyze tick latency metrics and generate performance report
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.websocket.benchmarking import (
    get_latency_tracker,
    get_latency_analyzer,
    get_performance_dashboard,
    initialize_latency_tracking,
    analyze_current_performance,
    generate_performance_report,
    export_performance_data
)

async def main():
    """Main analysis function"""
    
    print("🔍 Tick Latency Metrics Analysis")
    print("=" * 50)
    
    try:
        # Initialize benchmarking system (if not already running)
        try:
            initialize_latency_tracking(sampling_rate=10, latency_threshold_ms=50.0)
            print("✅ Latency tracking initialized")
        except Exception as e:
            print(f"⚠️  Latency tracking already running or failed: {e}")
        
        # Get current performance metrics
        print("\n📊 Analyzing current performance...")
        analysis = analyze_current_performance(sample_limit=1000)
        
        if analysis.sample_count == 0:
            print("❌ No performance data available for analysis.")
            print("   Ensure the system has been processing ticks.")
            return
        
        # Display key metrics
        print(f"\n📈 ANALYSIS RESULTS (based on {analysis.sample_count} samples):")
        print("-" * 50)
        
        print(f"🔧 Average Decode Time:     {analysis.avg_decode_time:.3f} ms")
        print(f"⏳ Average Queue Wait Time: {analysis.avg_queue_wait_time:.3f} ms")
        print(f"🧠 Average Strategy Time:    {analysis.avg_strategy_time:.3f} ms")
        print(f"📡 Average Broadcast Time:   {analysis.avg_broadcast_time:.3f} ms")
        print(f"🎯 Total End-to-End Latency: {analysis.avg_total_latency:.3f} ms")
        
        # Stage contributions
        print(f"\n📊 Stage Contributions (% of total latency):")
        print(f"   Decode:    {analysis.decode_contribution:.1f}%")
        print(f"   Queue:     {analysis.queue_contribution:.1f}%")
        print(f"   Strategy:   {analysis.strategy_contribution:.1f}%")
        print(f"   Broadcast:  {analysis.broadcast_contribution:.1f}%")
        
        # High-frequency analysis
        if analysis.high_freq_analysis.get('burst_detected'):
            burst = analysis.high_freq_analysis
            print(f"\n🚀 High-Frequency Burst Analysis:")
            print(f"   Fast ticks: {burst['fast_tick_percentage']:.1f}% of total")
            print(f"   Worst variance stage: {burst['highest_variance_stage']}")
            print(f"   Performance degradation: {burst['performance_degradation']['degradation_percent']:.1f}%")
        
        # Bottleneck identification
        print(f"\n⚠️  Bottleneck Analysis:")
        bottleneck = analysis.bottleneck_stage
        
        if bottleneck == "balanced":
            print("   ✅ Performance is balanced across all stages")
        else:
            print(f"   🚨 Primary Bottleneck: {bottleneck.upper()}")
            print(f"   📊 Contribution: {getattr(analysis, f'{bottleneck}_contribution', 0):.1f}%")
        
        # Decode vs Strategy comparison
        tracker = get_latency_tracker()
        comparison = tracker.get_decode_vs_strategy_comparison()
        
        if 'error' not in comparison:
            print(f"\n⚖️  Decode vs Strategy Comparison:")
            print(f"   Decode avg:   {comparison['decode_performance']['mean_ms']:.3f} ms")
            print(f"   Strategy avg:  {comparison['strategy_performance']['mean_ms']:.3f} ms")
            print(f"   Faster stage:  {comparison['comparison']['faster_stage']}")
            print(f"   Performance gap: {comparison['comparison']['performance_gap_ms']:.3f} ms")
        
        # Recommendations
        print(f"\n💡 Optimization Recommendations:")
        print(f"   {analysis.optimization_recommendation}")
        
        if analysis.requires_architectural_change:
            print(f"\n🏗️  ARCHITECTURAL CHANGES REQUIRED")
            print(f"     Total latency ({analysis.avg_total_latency:.1f}ms) exceeds 100ms threshold")
        
        # Highlight highest latency stage during bursts
        if analysis.high_freq_analysis.get('burst_detected'):
            worst_stage = analysis.high_freq_analysis.get('highest_variance_stage')
            if worst_stage and worst_stage != bottleneck:
                print(f"\n🎯 High-Frequency Bottleneck: {worst_stage.upper()}")
                print(f"   Shows highest variance during tick bursts")
                print(f"   Consider burst-specific optimizations for this stage")
        
        # Generate detailed report
        print(f"\n📄 Generating detailed report...")
        detailed_report = generate_performance_report(sample_limit=1000)
        
        # Save to file
        report_filename = f"latency_analysis_report_{int(asyncio.get_event_loop().time())}.txt"
        with open(report_filename, 'w') as f:
            f.write(detailed_report)
        
        print(f"✅ Detailed report saved to: {report_filename}")
        
        # Export JSON data
        json_filename = f"latency_analysis_data_{int(asyncio.get_event_loop().time())}.json"
        await export_performance_data(json_filename)
        print(f"✅ JSON data exported to: {json_filename}")
        
        # Performance assessment
        print(f"\n🎯 Performance Assessment:")
        if analysis.avg_total_latency <= 10:
            print("   🟢 EXCELLENT: Sub-10ms average latency")
        elif analysis.avg_total_latency <= 25:
            print("   🟡 GOOD: Sub-25ms average latency")
        elif analysis.avg_total_latency <= 50:
            print("   🟠 ACCEPTABLE: Sub-50ms average latency")
        elif analysis.avg_total_latency <= 100:
            print("   🔴 POOR: Exceeds 50ms, requires optimization")
        else:
            print("   🔴 CRITICAL: Exceeds 100ms, architectural changes needed")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
