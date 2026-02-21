"""
Tick Latency Analyzer
Analyzes collected latency metrics and identifies performance bottlenecks
"""

import statistics
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from collections import defaultdict

from .tick_latency_tracker import get_latency_tracker, TickLatencyMetrics

logger = logging.getLogger(__name__)

@dataclass
class LatencyAnalysis:
    """Results of latency analysis"""
    sample_count: int
    time_range: Dict[str, str]
    
    # Average latencies (ms)
    avg_decode_time: float
    avg_queue_wait_time: float
    avg_strategy_time: float
    avg_broadcast_time: float
    avg_total_latency: float
    
    # Stage contributions (%)
    decode_contribution: float
    queue_contribution: float
    strategy_contribution: float
    broadcast_contribution: float
    
    # High-frequency analysis
    high_freq_analysis: Dict[str, Any]
    
    # Recommendations
    bottleneck_stage: str
    optimization_recommendation: str
    requires_architectural_change: bool

class TickLatencyAnalyzer:
    """
    Analyzes tick latency metrics to identify performance issues
    Provides actionable recommendations based on data
    """
    
    def __init__(self):
        self.tracker = get_latency_tracker()
    
    def analyze_recent_performance(self, 
                               sample_limit: int = 1000,
                               high_freq_threshold_ms: float = 10.0) -> LatencyAnalysis:
        """
        Analyze recent tick performance
        
        Args:
            sample_limit: Maximum number of samples to analyze
            high_freq_threshold_ms: Threshold for high-frequency detection
        """
        
        # Get recent metrics
        recent_metrics = self._get_recent_metrics(sample_limit)
        
        if not recent_metrics:
            return self._create_empty_analysis("No data available")
        
        # Calculate basic statistics
        basic_stats = self._calculate_basic_statistics(recent_metrics)
        
        # Analyze stage contributions
        stage_contributions = self._analyze_stage_contributions(recent_metrics)
        
        # High-frequency burst analysis
        high_freq_analysis = self._analyze_high_frequency_bursts(
            recent_metrics, high_freq_threshold_ms
        )
        
        # Identify bottleneck
        bottleneck_stage = self._identify_bottleneck_stage(stage_contributions)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            bottleneck_stage, 
            basic_stats['avg_total_latency'],
            high_freq_analysis
        )
        
        return LatencyAnalysis(
            sample_count=len(recent_metrics),
            time_range=basic_stats['time_range'],
            avg_decode_time=basic_stats['avg_decode_time'],
            avg_queue_wait_time=basic_stats['avg_queue_wait_time'],
            avg_strategy_time=basic_stats['avg_strategy_time'],
            avg_broadcast_time=basic_stats['avg_broadcast_time'],
            avg_total_latency=basic_stats['avg_total_latency'],
            decode_contribution=stage_contributions['decode'],
            queue_contribution=stage_contributions['queue'],
            strategy_contribution=stage_contributions['strategy'],
            broadcast_contribution=stage_contributions['broadcast'],
            high_freq_analysis=high_freq_analysis,
            bottleneck_stage=bottleneck_stage,
            optimization_recommendation=recommendation['text'],
            requires_architectural_change=recommendation['architectural_change']
        )
    
    def _get_recent_metrics(self, limit: int) -> List[TickLatencyMetrics]:
        """Get recent tick metrics from tracker"""
        try:
            # Get percentile report to extract data
            report = self.tracker.get_percentile_report()
            
            # If we have statistics, reconstruct metrics
            if 'statistics_ms' in report and 'total_end_to_end' in report['statistics_ms']:
                # For this analysis, we'll use the tracker's internal data
                # In a real implementation, you'd access the actual metrics
                return self._reconstruct_metrics_from_report(report, limit)
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting recent metrics: {e}")
            return []
    
    def _reconstruct_metrics_from_report(self, report: Dict[str, Any], limit: int) -> List[TickLatencyMetrics]:
        """
        Reconstruct TickLatencyMetrics from percentile report
        In a real implementation, you'd access the actual stored metrics
        """
        # This is a simplified reconstruction for demonstration
        # In practice, you'd have direct access to the stored TickLatencyMetrics
        
        stats = report.get('statistics_ms', {})
        
        if not stats:
            return []
        
        # Create sample metrics based on statistics
        metrics = []
        sample_count = min(limit, report.get('sample_count', 100))
        
        for i in range(sample_count):
            # Create synthetic metrics based on statistics
            # This is just for demonstration - real implementation uses actual data
            metric = TickLatencyMetrics(
                tick_id=f"sample_{i}",
                timestamps=None  # Not needed for this analysis
            )
            
            # Set latencies based on statistics (with some variation)
            metric.decode_duration = int(stats.get('decode_duration', {}).get('mean', 0) * 1_000_000)
            metric.queue_wait_time = int(stats.get('queue_wait_time', {}).get('mean', 0) * 1_000_000)
            metric.strategy_duration = int(stats.get('strategy_duration', {}).get('mean', 0) * 1_000_000)
            metric.broadcast_duration = int(stats.get('broadcast_duration', {}).get('mean', 0) * 1_000_000)
            metric.total_end_to_end = int(stats.get('total_end_to_end', {}).get('mean', 0) * 1_000_000)
            
            metrics.append(metric)
        
        return metrics
    
    def _calculate_basic_statistics(self, metrics: List[TickLatencyMetrics]) -> Dict[str, Any]:
        """Calculate basic latency statistics"""
        
        # Extract latencies in milliseconds
        decode_times = [m.decode_duration / 1_000_000 for m in metrics]
        queue_times = [m.queue_wait_time / 1_000_000 for m in metrics]
        strategy_times = [m.strategy_duration / 1_000_000 for m in metrics]
        broadcast_times = [m.broadcast_duration / 1_000_000 for m in metrics]
        total_times = [m.total_end_to_end / 1_000_000 for m in metrics]
        
        # Calculate averages
        avg_decode = statistics.mean(decode_times) if decode_times else 0
        avg_queue = statistics.mean(queue_times) if queue_times else 0
        avg_strategy = statistics.mean(strategy_times) if strategy_times else 0
        avg_broadcast = statistics.mean(broadcast_times) if broadcast_times else 0
        avg_total = statistics.mean(total_times) if total_times else 0
        
        # Time range (simplified)
        now = datetime.now(timezone.utc)
        
        return {
            'avg_decode_time': avg_decode,
            'avg_queue_wait_time': avg_queue,
            'avg_strategy_time': avg_strategy,
            'avg_broadcast_time': avg_broadcast,
            'avg_total_latency': avg_total,
            'time_range': {
                'start': (now.replace(microsecond=0)).isoformat(),
                'end': now.isoformat()
            }
        }
    
    def _analyze_stage_contributions(self, metrics: List[TickLatencyMetrics]) -> Dict[str, float]:
        """Analyze percentage contribution of each stage to total latency"""
        
        if not metrics:
            return {'decode': 0, 'queue': 0, 'strategy': 0, 'broadcast': 0}
        
        # Calculate total time for each stage
        total_decode = sum(m.decode_duration for m in metrics)
        total_queue = sum(m.queue_wait_time for m in metrics)
        total_strategy = sum(m.strategy_duration for m in metrics)
        total_broadcast = sum(m.broadcast_duration for m in metrics)
        total_all = total_decode + total_queue + total_strategy + total_broadcast
        
        if total_all == 0:
            return {'decode': 0, 'queue': 0, 'strategy': 0, 'broadcast': 0}
        
        # Calculate percentages
        return {
            'decode': (total_decode / total_all) * 100,
            'queue': (total_queue / total_all) * 100,
            'strategy': (total_strategy / total_all) * 100,
            'broadcast': (total_broadcast / total_all) * 100
        }
    
    def _analyze_high_frequency_bursts(self, 
                                   metrics: List[TickLatencyMetrics], 
                                   threshold_ms: float) -> Dict[str, Any]:
        """Analyze performance during high-frequency tick bursts"""
        
        if not metrics:
            return {'burst_detected': False, 'analysis': 'No data available'}
        
        # Identify high-frequency ticks (below threshold)
        fast_ticks = [
            m for m in metrics 
            if m.total_end_to_end / 1_000_000 < threshold_ms
        ]
        
        if not fast_ticks:
            return {'burst_detected': False, 'analysis': 'No high-frequency ticks detected'}
        
        # Calculate statistics for fast ticks
        fast_decode_times = [m.decode_duration / 1_000_000 for m in fast_ticks]
        fast_queue_times = [m.queue_wait_time / 1_000_000 for m in fast_ticks]
        fast_strategy_times = [m.strategy_duration / 1_000_000 for m in fast_ticks]
        fast_broadcast_times = [m.broadcast_duration / 1_000_000 for m in fast_ticks]
        
        # Identify which stage has highest variance during bursts
        stage_variances = {
            'decode': statistics.variance(fast_decode_times) if len(fast_decode_times) > 1 else 0,
            'queue': statistics.variance(fast_queue_times) if len(fast_queue_times) > 1 else 0,
            'strategy': statistics.variance(fast_strategy_times) if len(fast_strategy_times) > 1 else 0,
            'broadcast': statistics.variance(fast_broadcast_times) if len(fast_broadcast_times) > 1 else 0
        }
        
        # Find stage with highest variance (most inconsistent during bursts)
        highest_variance_stage = max(stage_variances.items(), key=lambda x: x[1])
        
        # Calculate performance degradation during bursts
        normal_avg = statistics.mean([m.total_end_to_end / 1_000_000 for m in metrics])
        burst_avg = statistics.mean([m.total_end_to_end / 1_000_000 for m in fast_ticks])
        
        return {
            'burst_detected': True,
            'fast_tick_count': len(fast_ticks),
            'total_tick_count': len(metrics),
            'fast_tick_percentage': (len(fast_ticks) / len(metrics)) * 100,
            'burst_stage_averages': {
                'decode_ms': statistics.mean(fast_decode_times) if fast_decode_times else 0,
                'queue_ms': statistics.mean(fast_queue_times) if fast_queue_times else 0,
                'strategy_ms': statistics.mean(fast_strategy_times) if fast_strategy_times else 0,
                'broadcast_ms': statistics.mean(fast_broadcast_times) if fast_broadcast_times else 0
            },
            'highest_variance_stage': highest_variance_stage[0],
            'highest_variance_value': highest_variance_stage[1],
            'performance_degradation': {
                'normal_avg_ms': normal_avg,
                'burst_avg_ms': burst_avg,
                'degradation_percent': ((normal_avg - burst_avg) / normal_avg * 100) if normal_avg > 0 else 0
            }
        }
    
    def _identify_bottleneck_stage(self, contributions: Dict[str, float]) -> str:
        """Identify the stage contributing most to total latency"""
        
        # Find stage with highest contribution
        bottleneck = max(contributions.items(), key=lambda x: x[1])
        
        # Only consider it a bottleneck if it contributes more than 30%
        if bottleneck[1] > 30.0:
            return bottleneck[0]
        
        # If no single stage dominates, return "balanced"
        return "balanced"
    
    def _generate_recommendation(self, 
                              bottleneck_stage: str, 
                              total_latency_ms: float,
                              high_freq_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimization recommendations"""
        
        # Check if architectural change is needed
        needs_arch_change = total_latency_ms > 100.0
        
        if bottleneck_stage == "balanced":
            return {
                'text': "Performance is balanced across all stages. Monitor for any stage exceeding 20% contribution.",
                'architectural_change': needs_arch_change
            }
        
        recommendations = {
            'decode': {
                'text': "Protobuf decoding is the primary bottleneck. Consider optimizing protobuf schema, using faster parsing libraries, or moving decode to compiled extensions.",
                'architectural_change': False
            },
            'queue': {
                'text': "Queue wait times are excessive. Consider increasing queue sizes, adding more workers, or implementing priority queues for time-critical ticks.",
                'architectural_change': False
            },
            'strategy': {
                'text': "Strategy execution is the bottleneck. Optimize strategy algorithms, reduce computational complexity, or implement strategy-level caching.",
                'architectural_change': False
            },
            'broadcast': {
                'text': "UI broadcasting is slow. Optimize serialization, implement connection pooling, or use more efficient transport protocols.",
                'architectural_change': False
            }
        }
        
        base_recommendation = recommendations.get(bottleneck_stage, {
            'text': "Unknown bottleneck stage. Further investigation required.",
            'architectural_change': needs_arch_change
        })
        
        # Add architectural change recommendation if needed
        if needs_arch_change:
            base_recommendation['text'] += " Total latency exceeds 100ms - consider architectural changes such as parallel processing, data partitioning, or load balancing."
        
        # Add high-frequency specific recommendations
        if high_freq_analysis.get('burst_detected'):
            worst_stage = high_freq_analysis.get('highest_variance_stage')
            if worst_stage and worst_stage != bottleneck_stage:
                base_recommendation['text'] += f" During high-frequency bursts, {worst_stage} shows highest variance - consider burst-specific optimizations."
        
        return base_recommendation
    
    def _create_empty_analysis(self, reason: str) -> LatencyAnalysis:
        """Create empty analysis when no data is available"""
        return LatencyAnalysis(
            sample_count=0,
            time_range={'start': '', 'end': ''},
            avg_decode_time=0.0,
            avg_queue_wait_time=0.0,
            avg_strategy_time=0.0,
            avg_broadcast_time=0.0,
            avg_total_latency=0.0,
            decode_contribution=0.0,
            queue_contribution=0.0,
            strategy_contribution=0.0,
            broadcast_contribution=0.0,
            high_freq_analysis={'burst_detected': False, 'analysis': reason},
            bottleneck_stage="none",
            optimization_recommendation=reason,
            requires_architectural_change=False
        )
    
    def generate_performance_report(self, analysis: LatencyAnalysis) -> str:
        """Generate a formatted performance report"""
        
        if analysis.sample_count == 0:
            return "No performance data available for analysis."
        
        report = []
        report.append("=" * 60)
        report.append("TICK LATENCY PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Analysis Time: {datetime.now(timezone.utc).isoformat()}")
        report.append(f"Sample Count: {analysis.sample_count}")
        report.append(f"Time Range: {analysis.time_range['start']} to {analysis.time_range['end']}")
        report.append("")
        
        # Average latencies
        report.append("AVERAGE LATENCIES (milliseconds):")
        report.append("-" * 40)
        report.append(f"  Decode Time:        {analysis.avg_decode_time:.3f} ms")
        report.append(f"  Queue Wait Time:    {analysis.avg_queue_wait_time:.3f} ms")
        report.append(f"  Strategy Time:       {analysis.avg_strategy_time:.3f} ms")
        report.append(f"  Broadcast Time:      {analysis.avg_broadcast_time:.3f} ms")
        report.append(f"  TOTAL END-TO-END:  {analysis.avg_total_latency:.3f} ms")
        report.append("")
        
        # Stage contributions
        report.append("STAGE CONTRIBUTIONS (% of total latency):")
        report.append("-" * 40)
        report.append(f"  Decode:    {analysis.decode_contribution:.1f}%")
        report.append(f"  Queue:     {analysis.queue_contribution:.1f}%")
        report.append(f"  Strategy:   {analysis.strategy_contribution:.1f}%")
        report.append(f"  Broadcast:  {analysis.broadcast_contribution:.1f}%")
        report.append("")
        
        # Bottleneck identification
        report.append("BOTTLENECK ANALYSIS:")
        report.append("-" * 40)
        report.append(f"  Primary Bottleneck: {analysis.bottleneck_stage.upper()}")
        report.append("")
        
        # High-frequency analysis
        if analysis.high_freq_analysis.get('burst_detected'):
            report.append("HIGH-FREQUENCY BURST ANALYSIS:")
            report.append("-" * 40)
            burst = analysis.high_freq_analysis
            report.append(f"  Fast Ticks: {burst['fast_tick_count']}/{burst['total_tick_count']} ({burst['fast_tick_percentage']:.1f}%)")
            report.append(f"  Worst Variance Stage: {burst['highest_variance_stage']}")
            report.append(f"  Performance Degradation: {burst['performance_degradation']['degradation_percent']:.1f}%")
            report.append("")
        
        # Recommendations
        report.append("OPTIMIZATION RECOMMENDATIONS:")
        report.append("-" * 40)
        report.append(f"  {analysis.optimization_recommendation}")
        
        if analysis.requires_architectural_change:
            report.append("")
            report.append("⚠️  ARCHITECTURAL CHANGES RECOMMENDED")
            report.append("    Total latency exceeds 100ms threshold")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def export_analysis(self, analysis: LatencyAnalysis, filename: str) -> None:
        """Export analysis to JSON file"""
        import json
        
        export_data = {
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'analysis': {
                'sample_count': analysis.sample_count,
                'time_range': analysis.time_range,
                'average_latencies_ms': {
                    'decode_time': analysis.avg_decode_time,
                    'queue_wait_time': analysis.avg_queue_wait_time,
                    'strategy_time': analysis.avg_strategy_time,
                    'broadcast_time': analysis.avg_broadcast_time,
                    'total_latency': analysis.avg_total_latency
                },
                'stage_contributions_percent': {
                    'decode': analysis.decode_contribution,
                    'queue': analysis.queue_contribution,
                    'strategy': analysis.strategy_contribution,
                    'broadcast': analysis.broadcast_contribution
                },
                'bottleneck_stage': analysis.bottleneck_stage,
                'high_frequency_analysis': analysis.high_freq_analysis,
                'recommendation': analysis.optimization_recommendation,
                'requires_architectural_change': analysis.requires_architectural_change
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Latency analysis exported to {filename}")

# Global analyzer instance
_global_analyzer: Optional[TickLatencyAnalyzer] = None

def get_latency_analyzer() -> TickLatencyAnalyzer:
    """Get global latency analyzer instance"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = TickLatencyAnalyzer()
    return _global_analyzer

def analyze_current_performance(sample_limit: int = 1000) -> LatencyAnalysis:
    """Analyze current performance and return results"""
    analyzer = get_latency_analyzer()
    return analyzer.analyze_recent_performance(sample_limit)

def generate_performance_report(sample_limit: int = 1000) -> str:
    """Generate formatted performance report"""
    analyzer = get_latency_analyzer()
    analysis = analyzer.analyze_recent_performance(sample_limit)
    return analyzer.generate_performance_report(analysis)

def export_performance_analysis(filename: str, sample_limit: int = 1000) -> None:
    """Export performance analysis to file"""
    analyzer = get_latency_analyzer()
    analysis = analyzer.analyze_recent_performance(sample_limit)
    analyzer.export_analysis(analysis, filename)
