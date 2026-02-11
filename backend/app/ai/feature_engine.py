import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.market_data import MarketSnapshot, OptionChainSnapshot

class FeatureEngine:
    def __init__(self, db: Session):
        self.db = db

    def calculate_directional_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate momentum, VWAP deviation, and Gap % 
        Assumes df is sorted by timestamp
        """
        if df.empty:
            return df
            
        # 1. Multi-timeframe momentum (Returns)
        df['returns_5m'] = df['spot_price'].pct_change(periods=1)
        df['returns_15m'] = df['spot_price'].pct_change(periods=3)
        df['returns_30m'] = df['spot_price'].pct_change(periods=6)
        
        # 2. VWAP Deviation (assuming we have VWAP from API or calculating simplified)
        if 'vwap' in df.columns and not df['vwap'].isnull().all():
            df['vwap_deviation'] = (df['spot_price'] - df['vwap']) / df['vwap']
        else:
            # Fallback: simple moving average as proxy
            df['sma_20'] = df['spot_price'].rolling(window=20).mean()
            df['vwap_deviation'] = (df['spot_price'] - df['sma_20']) / df['sma_20']
            
        return df

    def calculate_option_features(self, market_snapshot: MarketSnapshot, chain: List[OptionChainSnapshot]) -> Dict[str, Any]:
        """
        Calculate PCR, Writing Pressure, and ATM Straddle Move
        """
        if not chain:
            return {}
            
        df = pd.DataFrame([{
            'strike': c.strike,
            'type': c.option_type,
            'oi': c.oi,
            'ltp': c.ltp,
            'iv': c.iv,
            'volume': c.volume
        } for c in chain])
        
        # 1. Put-Call Ratio (OI based)
        call_oi = df[df['type'] == 'CE']['oi'].sum()
        put_oi = df[df['type'] == 'PE']['oi'].sum()
        pcr = put_oi / call_oi if call_oi > 0 else 1.0
        
        # 2. Writing Pressure (Volume vs OI)
        # Higher OI + Volume expansion on one side indicates writing/buying pressure
        # Simplified: weighted average IV
        avg_iv = df['iv'].mean()
        
        # 3. ATM Detection
        spot = market_snapshot.spot_price
        df['dist'] = abs(df['strike'] - spot)
        atm_strike = df.loc[df['dist'].idxmin()]['strike']
        
        # ATM Straddle Expected Move (%)
        # Simple Approximation: 0.8 * ATM_IV * sqrt(days_to_expiry/365)
        # For intraday, we use IV directly as a feature
        atm_iv = df[df['strike'] == atm_strike]['iv'].mean()
        
        return {
            'pcr': pcr,
            'avg_iv': avg_iv,
            'atm_iv': atm_iv,
            'call_oi': call_oi,
            'put_oi': put_oi,
            'strike_count': len(df['strike'].unique())
        }

    def prepare_ml_row(self, symbol: str, lookback_minutes: int = 60) -> Optional[Dict[str, Any]]:
        """
        Main entry point to get a single ML-ready feature vector for current state
        """
        # Fetch last N snapshots
        snapshots = self.db.query(MarketSnapshot)\
            .filter(MarketSnapshot.symbol == symbol)\
            .order_by(MarketSnapshot.timestamp.desc())\
            .limit(20).all()
            
        if not snapshots:
            return None
            
        # Sort ascending for calculations
        snapshots.reverse()
        df = pd.DataFrame([s.__dict__ for s in snapshots])
        df = self.calculate_directional_features(df)
        
        # Get latest snapshot and its option chain
        latest_snapshot = snapshots[-1]
        chain = self.db.query(OptionChainSnapshot)\
            .filter(OptionChainSnapshot.market_snapshot_id == latest_snapshot.id).all()
            
        option_features = self.calculate_option_features(latest_snapshot, chain)
        
        # Combine
        latest_row = df.iloc[-1].to_dict()
        latest_row.update(option_features)
        
        # Clean up SQLAlchemy state
        if '_sa_instance_state' in latest_row:
            del latest_row['_sa_instance_state']
            
        return latest_row
