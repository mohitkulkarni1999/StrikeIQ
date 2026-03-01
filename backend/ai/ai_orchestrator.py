"""
AI Orchestrator - Main pipeline for AI trade suggestions
Lightweight, optimized for Intel i5 CPU, 8GB RAM
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import time

# Import all AI engines
from .formula_engine import FormulaEngine, FormulaSignal
from .regime_engine import RegimeEngine
from .strategy_engine import StrategyEngine, StrategyChoice
from .strike_selection_engine import StrikeSelectionEngine
from .entry_exit_engine import EntryExitEngine
from .risk_engine import RiskEngine
from .explanation_engine import ExplanationEngine
from .learning_engine import LearningEngine

logger = logging.getLogger(__name__)

class TradeSuggestionWrapper:
    """Wrapper for learning engine interface"""
    def __init__(self, strategy, confidence, entry_price, target_price, stoploss_price, option_strike, option_type):
        self.strategy = strategy
        self.confidence = confidence
        self.entry_price = entry_price
        self.target_price = target_price
        self.stoploss_price = stoploss_price
        self.option_strike = option_strike
        self.option_type = option_type

@dataclass
class AITradeOutput:
    """Final AI trade output"""
    symbol: str
    trade: str  # strategy name
    option: str  # strike + type
    entry: float
    target: float
    stoploss: float
    confidence: float
    risk_reward: float
    regime: str
    explanation: List[str]
    risk_status: str  # APPROVED / REJECTED

class AIOrchestrator:
    """
    Main AI pipeline orchestrator
    Coordinates all AI engines to generate trade suggestions
    """
    
    def __init__(self):
        # Initialize all engines
        self.formula_engine = FormulaEngine()
        self.regime_engine = RegimeEngine()
        self.strategy_engine = StrategyEngine()
        self.strike_selection_engine = StrikeSelectionEngine()
        self.entry_exit_engine = EntryExitEngine()
        self.risk_engine = RiskEngine()
        self.explanation_engine = ExplanationEngine()
        self.learning_engine = LearningEngine()
        
        # Performance tracking
        self.pipeline_execution_times = []
        self.total_executions = 0
        
        logger.info("AI Orchestrator initialized with all engines")
    
    def run_ai_pipeline(self, live_metrics) -> Optional[Dict[str, Any]]:
        """
        Main AI pipeline function
        Takes LiveMetrics and returns trade suggestion
        """
        start_time = time.time()
        
        try:
            # Step 1: Formula Engine - Generate signals F01-F10
            formula_signals = self.formula_engine.analyze(live_metrics)
            
            # Step 2: Regime Engine - Detect market regime
            regime_detection = self.regime_engine.detect_regime(live_metrics)
            
            # Step 3: Strategy Engine - Choose strategy
            strategy_choice = self.strategy_engine.select_strategy(formula_signals)
            
            # Step 4: Strike Selection Engine - Choose best strike
            market_bias = self._determine_market_bias(formula_signals)
            strike_selection = self.strike_selection_engine.select_strike(
                live_metrics, market_bias, regime_detection.regime
            )
            
            # Step 5: Entry Exit Engine - Calculate entry, target, stoploss
            entry_exit_levels = self.entry_exit_engine.calculate_levels(
                strike_selection.best_strike, 
                strike_selection.option_type,
                live_metrics,
                market_bias,
                regime_detection.regime
            )
            
            # Step 6: Risk Engine - Validate trade
            risk_assessment = self._validate_risk(
                entry_exit_levels, strategy_choice, live_metrics
            )
            
            if not risk_assessment['approved']:
                return self._create_hold_result(live_metrics, "Risk validation failed", regime_detection.regime)
            
            # Step 7: Explanation Engine - Produce human readable reasoning
            explanation = self._generate_explanation(
                formula_signals, regime_detection, strategy_choice,
                strike_selection, entry_exit_levels, live_metrics
            )
            
            # Step 8: Learning Engine - Store prediction using existing tables
            # Create a trade suggestion object for learning engine
            trade_suggestion_obj = TradeSuggestionWrapper(
                strategy=strategy_choice.strategy,
                confidence=strategy_choice.confidence,
                entry_price=entry_exit_levels.entry_price,
                target_price=entry_exit_levels.target_price,
                stoploss_price=entry_exit_levels.stoploss_price,
                option_strike=strike_selection.best_strike,
                option_type=strike_selection.option_type
            )
            
            prediction_id = self.learning_engine.record_prediction(formula_signals, trade_suggestion_obj)
            
            # Calculate risk/reward ratio
            risk = abs(entry_exit_levels.entry_price - entry_exit_levels.stoploss_price)
            reward = abs(entry_exit_levels.target_price - entry_exit_levels.entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Create final output
            output = {
                "symbol": live_metrics.symbol,
                "strategy": strategy_choice.strategy,
                "option": f"{strike_selection.best_strike}{strike_selection.option_type}",
                "entry": entry_exit_levels.entry_price,
                "target": entry_exit_levels.target_price,
                "stoploss": entry_exit_levels.stoploss_price,
                "confidence": min(strategy_choice.confidence, entry_exit_levels.confidence),
                "risk_reward": risk_reward_ratio,
                "regime": regime_detection.regime,
                "explanation": explanation,
                "risk_status": "APPROVED"
            }
            
            # Track performance
            execution_time = time.time() - start_time
            self.pipeline_execution_times.append(execution_time)
            self.total_executions += 1
            
            logger.info(f"AI Pipeline completed in {execution_time:.3f}s for {live_metrics.symbol}")
            
            return output
            
        except Exception as e:
            logger.error(f"AI Pipeline error for {live_metrics.symbol}: {e}")
            return self._create_hold_result(live_metrics, f"Pipeline error: {str(e)}", "UNKNOWN")
    
    def _create_hold_result(self, live_metrics, reason: str, regime: str) -> Dict[str, Any]:
        """Create consistent HOLD result"""
        return {
            "symbol": live_metrics.symbol,
            "strategy": "HOLD",
            "option": "N/A",
            "entry": 0.0,
            "target": 0.0,
            "stoploss": 0.0,
            "confidence": 0.0,
            "risk_reward": 0.0,
            "regime": regime,
            "risk_status": "REJECTED",
            "explanation": [reason]
        }
    
    def _determine_market_bias(self, formula_signals) -> str:
        """Determine overall market bias from formula signals"""
        try:
            buy_weight = 0.0
            sell_weight = 0.0
            total_weight = 0.0
            
            # Weight important formulas more heavily
            weights = {
                "F01": 2.0,  # PCR - most important
                "F02": 1.5,  # OI imbalance
                "F03": 1.8,  # Gamma regime
                "F06": 1.3,  # Delta imbalance
                "F10": 1.4   # Flow imbalance
            }
            
            for formula_id, signal in formula_signals.items():
                weight = weights.get(formula_id, 1.0)
                total_weight += weight
                
                if signal.signal == "BUY":
                    buy_weight += weight * signal.confidence
                elif signal.signal == "SELL":
                    sell_weight += weight * signal.confidence
            
            if total_weight == 0:
                return "neutral"
            
            buy_ratio = buy_weight / total_weight
            sell_ratio = sell_weight / total_weight
            
            # Lower threshold for bias determination
            if buy_ratio > 0.25:
                return "bullish"
            elif sell_ratio > 0.25:
                return "bearish"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Market bias determination error: {e}")
            return "neutral"
    
    def _validate_risk(self, entry_exit_levels, strategy_choice, live_metrics) -> Dict[str, Any]:
        """Validate trade against risk rules"""
        try:
            # Basic risk validation
            risk_score = 0.0
            approved = True
            reasons = []
            
            # Check confidence threshold
            if strategy_choice.confidence < 0.6:
                approved = False
                risk_score += 0.3
                reasons.append("Low strategy confidence")
            
            # Check entry/exit confidence
            if entry_exit_levels.confidence < 0.5:
                approved = False
                risk_score += 0.2
                reasons.append("Low entry/exit confidence")
            
            # Check risk/reward ratio
            if entry_exit_levels.risk_reward_ratio < 2.0:
                approved = False
                risk_score += 0.4
                reasons.append("Risk/reward ratio below minimum")
            
            # Check volatility regime
            volatility_regime = getattr(live_metrics, 'volatility_regime', 'normal')
            if volatility_regime == "extreme":
                risk_score += 0.2
                reasons.append("Extreme volatility")
            
            # Check liquidity (proxy via total OI)
            total_oi = getattr(live_metrics, 'total_oi', 0)
            if total_oi < 100000:
                approved = False
                risk_score += 0.3
                reasons.append("Low liquidity")
            
            return {
                'approved': approved,
                'risk_score': min(risk_score, 1.0),
                'reasons': reasons
            }
            
        except Exception as e:
            logger.error(f"Risk validation error: {e}")
            return {
                'approved': False,
                'risk_score': 1.0,
                'reasons': ["Risk validation error"]
            }
    
    def _generate_explanation(self, formula_signals, regime_detection, strategy_choice,
                            strike_selection, entry_exit_levels, live_metrics) -> List[str]:
        """Generate human readable explanation"""
        try:
            explanation_parts = []
            
            # Regime explanation
            explanation_parts.append(f"Market Regime: {regime_detection.regime}")
            
            # Key formula signals
            strong_signals = []
            for formula_id, signal in formula_signals.items():
                if signal.confidence > 0.6 and signal.signal in ["BUY", "SELL"]:
                    formula_names = {
                        "F01": "PCR", "F02": "OI Imbalance", "F03": "Gamma",
                        "F04": "Volume", "F05": "Expected Move", "F06": "Delta",
                        "F07": "Volatility", "F08": "OI Velocity", "F09": "Gamma Flip",
                        "F10": "Flow"
                    }
                    name = formula_names.get(formula_id, formula_id)
                    strong_signals.append(f"{name}: {signal.reason}")
            
            if strong_signals:
                explanation_parts.extend(strong_signals[:3])  # Top 3 signals
            
            # Strategy reasoning
            explanation_parts.append(f"Strategy: {strategy_choice.strategy}")
            explanation_parts.append(f"Strategy Reasoning: {strategy_choice.reasoning}")
            
            # Strike selection reasoning
            explanation_parts.append(f"Strike Selection: {strike_selection.reasoning}")
            
            # Entry/exit reasoning
            explanation_parts.append(f"Entry/Exit: {entry_exit_levels.reasoning}")
            
            return explanation_parts
            
        except Exception as e:
            logger.error(f"Explanation generation error: {e}")
            return ["Error generating explanation"]
    
    def record_trade_outcome(self, prediction_id: str, outcome_data: Dict[str, Any]):
        """
        Record the outcome of a trade for learning
        """
        try:
            self.learning_engine.record_outcome(prediction_id, outcome_data)
            logger.info(f"Trade outcome recorded for prediction {prediction_id}")
        except Exception as e:
            logger.error(f"Trade outcome recording error: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get AI pipeline performance metrics
        """
        try:
            avg_execution_time = (
                sum(self.pipeline_execution_times) / len(self.pipeline_execution_times)
                if self.pipeline_execution_times else 0
            )
            
            return {
                'pipeline_performance': {
                    'total_executions': self.total_executions,
                    'avg_execution_time_ms': avg_execution_time * 1000,
                    'max_execution_time_ms': max(self.pipeline_execution_times) * 1000 if self.pipeline_execution_times else 0,
                    'min_execution_time_ms': min(self.pipeline_execution_times) * 1000 if self.pipeline_execution_times else 0
                },
                'learning_summary': self.learning_engine.get_learning_summary()
            }
            
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            return {'error': str(e)}

# Global AI Orchestrator instance
_ai_orchestrator = None

def get_ai_orchestrator() -> AIOrchestrator:
    """
    Get or create global AI Orchestrator instance
    """
    global _ai_orchestrator
    if _ai_orchestrator is None:
        _ai_orchestrator = AIOrchestrator()
    return _ai_orchestrator

def run_ai_pipeline(live_metrics) -> Optional[Dict[str, Any]]:
    """
    Convenience function to run AI pipeline
    """
    orchestrator = get_ai_orchestrator()
    return orchestrator.run_ai_pipeline(live_metrics)

def record_trade_outcome(prediction_id: str, outcome_data: Dict[str, Any]):
    """
    Convenience function to record trade outcome
    """
    orchestrator = get_ai_orchestrator()
    orchestrator.record_trade_outcome(prediction_id, outcome_data)

def get_ai_performance() -> Dict[str, Any]:
    """
    Convenience function to get AI performance metrics
    """
    orchestrator = get_ai_orchestrator()
    return orchestrator.get_performance_metrics()
