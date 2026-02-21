"""
Performance Dashboard
Real-time performance monitoring and analysis dashboard
"""

import asyncio
import json
import time
from typing import Dict, Any, List
from datetime import datetime, timezone

from .latency_analyzer import get_latency_analyzer, analyze_current_performance
from .tick_latency_tracker import get_latency_tracker

class PerformanceDashboard:
    """
    Real-time performance monitoring dashboard
    Provides live analysis of tick processing performance
    """
    
    def __init__(self):
        self.analyzer = get_latency_analyzer()
        self.tracker = get_latency_tracker()
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        
        # Get recent analysis
        analysis = self.analyzer.analyze_recent_performance(sample_limit=500)
        
        # Get tracker statistics
        tracker_stats = self.tracker.get_statistics()
        
        # Get decode vs strategy comparison
        comparison = self.tracker.get_decode_vs_strategy_comparison()
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'current_analysis': {
                'sample_count': analysis.sample_count,
                'avg_decode_time_ms': analysis.avg_decode_time,
                'avg_queue_wait_time_ms': analysis.avg_queue_wait_time,
                'avg_strategy_time_ms': analysis.avg_strategy_time,
                'avg_broadcast_time_ms': analysis.avg_broadcast_time,
                'avg_total_latency_ms': analysis.avg_total_latency,
                'bottleneck_stage': analysis.bottleneck_stage,
                'requires_architectural_change': analysis.requires_architectural_change
            },
            'stage_contributions': {
                'decode_percent': analysis.decode_contribution,
                'queue_percent': analysis.queue_contribution,
                'strategy_percent': analysis.strategy_contribution,
                'broadcast_percent': analysis.broadcast_contribution
            },
            'high_frequency_analysis': analysis.high_freq_analysis,
            'decode_vs_strategy_comparison': comparison,
            'tracker_statistics': tracker_stats
        }
    
    async def generate_summary_report(self) -> str:
        """Generate summary performance report"""
        
        metrics = await self.get_current_metrics()
        analysis = metrics['current_analysis']
        
        if analysis['sample_count'] == 0:
            return "No performance data available for analysis."
        
        # Build report
        report_lines = []
        report_lines.append("📊 TICK LATENCY PERFORMANCE SUMMARY")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {metrics['timestamp']}")
        report_lines.append(f"Samples: {analysis['sample_count']}")
        report_lines.append("")
        
        # Key metrics
        report_lines.append("🔍 KEY METRICS:")
        report_lines.append(f"  Average Decode Time:     {analysis['avg_decode_time_ms']:.2f} ms")
        report_lines.append(f"  Average Queue Wait:     {analysis['avg_queue_wait_time_ms']:.2f} ms")
        report_lines.append(f"  Average Strategy Time:   {analysis['avg_strategy_time_ms']:.2f} ms")
        report_lines.append(f"  Average Broadcast Time:  {analysis['avg_broadcast_time_ms']:.2f} ms")
        report_lines.append(f"  Total End-to-End:       {analysis['avg_total_latency_ms']:.2f} ms")
        report_lines.append("")
        
        # Stage contributions
        report_lines.append("📈 STAGE CONTRIBUTIONS:")
        contributions = metrics['stage_contributions']
        report_lines.append(f"  Decode:    {contributions['decode_percent']:.1f}%")
        report_lines.append(f"  Queue:     {contributions['queue_percent']:.1f}%")
        report_lines.append(f"  Strategy:   {contributions['strategy_percent']:.1f}%")
        report_lines.append(f"  Broadcast:  {contributions['broadcast_percent']:.1f}%")
        report_lines.append("")
        
        # Bottleneck analysis
        report_lines.append("⚠️  BOTTLENECK ANALYSIS:")
        bottleneck = analysis['bottleneck_stage']
        if bottleneck == "balanced":
            report_lines.append("  ✅ Performance is balanced across stages")
        else:
            report_lines.append(f"  🚨 Primary Bottleneck: {bottleneck.upper()}")
        report_lines.append("")
        
        # High-frequency analysis
        hf_analysis = metrics['high_frequency_analysis']
        if hf_analysis.get('burst_detected'):
            report_lines.append("🚀 HIGH-FREQUENCY BURST ANALYSIS:")
            report_lines.append(f"  Fast ticks: {hf_analysis['fast_tick_percentage']:.1f}% of total")
            report_lines.append(f"  Worst variance stage: {hf_analysis['highest_variance_stage']}")
            report_lines.append("")
        
        # Decode vs Strategy comparison
        comparison = metrics['decode_vs_strategy_comparison']
        if 'error' not in comparison:
            report_lines.append("⚖️  DECODE vs STRATEGY COMPARISON:")
            report_lines.append(f"  Decode avg:   {comparison['decode_performance']['mean_ms']:.2f} ms")
            report_lines.append(f"  Strategy avg:  {comparison['strategy_performance']['mean_ms']:.2f} ms")
            report_lines.append(f"  Faster stage:  {comparison['comparison']['faster_stage']}")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("💡 OPTIMIZATION RECOMMENDATIONS:")
        
        # Get recommendation from analysis
        from .latency_analyzer import LatencyAnalyzer
        temp_analyzer = LatencyAnalyzer()
        recommendation = temp_analyzer._generate_recommendation(
            bottleneck, 
            analysis['avg_total_latency_ms'], 
            hf_analysis
        )
        
        report_lines.append(f"  {recommendation['text']}")
        
        if analysis['requires_architectural_change']:
            report_lines.append("")
            report_lines.append("🏗️  ARCHITECTURAL CHANGES REQUIRED")
            report_lines.append("     Total latency exceeds 100ms threshold")
        
        report_lines.append("")
        report_lines.append("=" * 50)
        
        return "\n".join(report_lines)
    
    async def get_bottleneck_analysis(self) -> Dict[str, Any]:
        """Get detailed bottleneck analysis"""
        
        metrics = await self.get_current_metrics()
        analysis = metrics['current_analysis']
        
        if analysis['sample_count'] == 0:
            return {'error': 'No data available'}
        
        bottleneck = analysis['bottleneck_stage']
        contributions = metrics['stage_contributions']
        
        # Determine severity
        total_latency = analysis['avg_total_latency_ms']
        severity = 'low'
        if total_latency > 100:
            severity = 'critical'
        elif total_latency > 50:
            severity = 'high'
        elif total_latency > 25:
            severity = 'medium'
        
        return {
            'bottleneck_stage': bottleneck,
            'bottleneck_contribution': contributions.get(f"{bottleneck}_percent", 0),
            'total_latency_ms': total_latency,
            'severity': severity,
            'requires_optimization': bottleneck != 'balanced',
            'requires_architectural_change': analysis['requires_architectural_change'],
            'recommendation': self._get_stage_specific_recommendation(bottleneck, total_latency)
        }
    
    def _get_stage_specific_recommendation(self, stage: str, total_latency: float) -> str:
        """Get stage-specific optimization recommendation"""
        
        recommendations = {
            'decode': {
                'low': "Protobuf decoding is performing well. Continue monitoring.",
                'medium': "Consider optimizing protobuf schema or using faster parsing libraries.",
                'high': "Protobuf decoding is significantly slow. Implement compiled extensions or alternative parsing.",
                'critical': "Critical decode performance. Consider schema redesign or precompiled parsing."
            },
            'queue': {
                'low': "Queue performance is acceptable.",
                'medium': "Consider increasing worker count or queue sizes.",
                'high': "Queue wait times are excessive. Add more workers or implement priority queues.",
                'critical': "Critical queue bottleneck. Implement load balancing and increase processing capacity."
            },
            'strategy': {
                'low': "Strategy execution is efficient.",
                'medium': "Consider optimizing strategy algorithms or caching results.",
                'high': "Strategy execution is slow. Optimize computational complexity.",
                'critical': "Critical strategy performance. Implement algorithmic improvements or parallel processing."
            },
            'broadcast': {
                'low': "Broadcast performance is good.",
                'medium': "Consider optimizing serialization or connection pooling.",
                'high': "Broadcast is slow. Implement more efficient transport protocols.",
                'critical': "Critical broadcast performance. Consider architectural changes to data distribution."
            },
            'balanced': {
                'low': "System is well-balanced and performing optimally.",
                'medium': "Performance is balanced but could benefit from general optimizations.",
                'high': "Balanced performance but overall latency is high. Consider system-wide optimizations.",
                'critical': "System-wide performance issues. Consider architectural changes."
            }
        }
        
        # Determine severity level
        if total_latency > 100:
            severity = 'critical'
        elif total_latency > 50:
            severity = 'high'
        elif total_latency > 25:
            severity = 'medium'
        else:
            severity = 'low'
        
        return recommendations.get(stage, recommendations['balanced']).get(severity, 'No recommendation available.')
    
    async def export_performance_data(self, filename: str) -> None:
        """Export comprehensive performance data to file"""
        
        metrics = await self.get_current_metrics()
        
        export_data = {
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'performance_metrics': metrics,
            'analysis_summary': await self.get_bottleneck_analysis(),
            'recommendations': {
                'immediate_optimization': metrics['current_analysis']['optimization_recommendation'],
                'architectural_change_required': metrics['current_analysis']['requires_architectural_change'],
                'stage_specific': self._get_stage_specific_recommendation(
                    metrics['current_analysis']['bottleneck_stage'],
                    metrics['current_analysis']['avg_total_latency_ms']
                )
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

# Global dashboard instance
_global_dashboard: Optional[PerformanceDashboard] = None

def get_performance_dashboard() -> PerformanceDashboard:
    """Get global performance dashboard instance"""
    global _global_dashboard
    if _global_dashboard is None:
        _global_dashboard = PerformanceDashboard()
    return _global_dashboard

async def get_current_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics"""
    dashboard = get_performance_dashboard()
    return await dashboard.get_current_metrics()

async def generate_performance_summary() -> str:
    """Generate performance summary report"""
    dashboard = get_performance_dashboard()
    return await dashboard.generate_summary_report()

async def get_bottleneck_analysis() -> Dict[str, Any]:
    """Get bottleneck analysis"""
    dashboard = get_performance_dashboard()
    return await dashboard.get_bottleneck_analysis()

async def export_performance_data(filename: str) -> None:
    """Export performance data"""
    dashboard = get_performance_dashboard()
    await dashboard.export_performance_data(filename)
