import { MarketData } from '../types/dashboard';

// Core intelligence interfaces
export interface BiasIntelligence {
  score: number;
  label: string;
  strength: number;
  direction: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  signal: 'strong' | 'moderate' | 'weak';
}

export interface VolatilityRegime {
  current: 'low' | 'normal' | 'elevated' | 'extreme';
  percentile: number;
  trend: 'rising' | 'falling' | 'stable';
  risk: 'low' | 'medium' | 'high' | 'extreme';
  environment: 'accumulation' | 'distribution' | 'compression' | 'expansion';
}

export interface LiquidityIntelligence {
  total_oi: number;
  oi_change_24h: number;
  concentration: number;
  depth_score: number;
  flow_direction: 'inflow' | 'outflow' | 'balanced';
}

export interface ProbabilityIntelligence {
  expected_move: number;
  upper_1sd: number;
  lower_1sd: number;
  upper_2sd: number;
  lower_2sd: number;
  breach_probability: number;
  range_hold_probability: number;
  volatility_state: 'underpriced' | 'fair' | 'overpriced';
}

export interface MarketIntelligence {
  bias: BiasIntelligence;
  volatility: VolatilityRegime;
  liquidity: LiquidityIntelligence;
  probability?: ProbabilityIntelligence;
  timestamp: string;
  confidence: number;
}

// Intelligence Aggregator - Centralized business logic
export class IntelligenceEngine {
  static computeBias(rawAnalytics: any): BiasIntelligence {
    const score = rawAnalytics?.bias_score ?? 0;
    const label = rawAnalytics?.bias_label ?? "NEUTRAL";

    const direction = label.includes("BULL") ? 'bullish' :
      label.includes("BEAR") ? 'bearish' : 'neutral';

    const strength = score / 100;
    const confidence = Math.min(score + 10, 100) / 100;

    let signal: 'strong' | 'moderate' | 'weak';
    if (score >= 70) signal = 'strong';
    else if (score >= 55) signal = 'moderate';
    else signal = 'weak';

    return {
      score,
      label,
      strength,
      direction,
      confidence,
      signal
    };
  }

  static computeVolatilityRegime(marketData: MarketData, historicalIV?: number[]): VolatilityRegime {
    // Placeholder: In real implementation, this would use IV data
    const percentile = Math.random() * 100; // Mock IV percentile
    const trend = Math.random() > 0.5 ? 'rising' : 'falling'; // Mock trend

    let current: 'low' | 'normal' | 'elevated' | 'extreme';
    let risk: 'low' | 'medium' | 'high' | 'extreme';

    if (percentile < 25) {
      current = 'low';
      risk = 'low';
    } else if (percentile < 50) {
      current = 'normal';
      risk = 'medium';
    } else if (percentile < 75) {
      current = 'elevated';
      risk = 'high';
    } else {
      current = 'extreme';
      risk = 'extreme';
    }

    // Determine market environment
    let environment: 'accumulation' | 'distribution' | 'compression' | 'expansion';
    if (current === 'low' && trend === 'rising') {
      environment = 'accumulation';
    } else if (current === 'extreme' && trend === 'rising') {
      environment = 'expansion';
    } else if (current === 'elevated' && trend === 'falling') {
      environment = 'distribution';
    } else {
      environment = 'compression';
    }

    return {
      current,
      percentile,
      trend,
      risk,
      environment
    };
  }

  static computeLiquidity(rawAnalytics: any): LiquidityIntelligence {
    const total_oi = (rawAnalytics?.total_call_oi ?? 0) + (rawAnalytics?.total_put_oi ?? 0);
    const concentration = Math.abs(rawAnalytics?.oi_dominance ?? 0);

    // Mock flow direction based on OI changes
    const flow_direction = concentration > 0.1 ? 'inflow' : 'balanced';

    return {
      total_oi,
      oi_change_24h: 0, // Would need historical data
      concentration,
      depth_score: Math.min(total_oi / 1000000, 100),
      flow_direction
    };
  }

  static aggregateIntelligence(
    rawAnalytics: any,
    marketData: MarketData
  ): MarketIntelligence {
    const bias = this.computeBias(rawAnalytics);
    const volatility = this.computeVolatilityRegime(marketData);
    const liquidity = this.computeLiquidity(rawAnalytics);

    // Overall confidence based on data quality and consistency
    const confidence = (bias.confidence + (volatility.percentile / 100)) / 2;

    return {
      bias,
      volatility,
      liquidity,
      timestamp: new Date().toISOString(),
      confidence
    };
  }
}

// Hook for components to consume intelligence
export function useMarketIntelligence(
  rawAnalytics: any,
  marketData: MarketData | null
): MarketIntelligence | null {
  if (!rawAnalytics || !marketData) return null;

  return IntelligenceEngine.aggregateIntelligence(rawAnalytics, marketData);
}
