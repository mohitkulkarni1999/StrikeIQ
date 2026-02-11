import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from datetime import timedelta
from ..models.market_data import MarketSnapshot, OptionChainSnapshot
from .feature_engine import FeatureEngine

class DatasetBuilder:
    def __init__(self, db: Session):
        self.db = db
        self.feature_engine = FeatureEngine(db)

    def build_training_dataset(self, symbol: str, lookback_days: int = 30):
        """
        Builds a historical dataset for training.
        Fetches snapshots, joins with options, and generates labels.
        """
        # Fetch snapshots
        snapshots = self.db.query(MarketSnapshot)\
            .filter(MarketSnapshot.symbol == symbol)\
            .order_by(MarketSnapshot.timestamp.asc()).all()
            
        if not snapshots:
            return pd.DataFrame()
            
        data = []
        for i, snap in enumerate(snapshots):
            # Calculate features for this snapshot
            # Note: In a production loop, we'd optimize the rolling window
            row = self.feature_engine.prepare_ml_row(symbol) # This is inefficient in a loop, but illustrative
            
            # Find Label: Future price in 30 minutes
            # Search for a snapshot ~30 mins ahead
            target_time = snap.timestamp + timedelta(minutes=30)
            future_snap = self.db.query(MarketSnapshot)\
                .filter(MarketSnapshot.symbol == symbol)\
                .filter(MarketSnapshot.timestamp >= target_time)\
                .order_by(MarketSnapshot.timestamp.asc()).first()
                
            if future_snap:
                move = (future_snap.spot_price - snap.spot_price) / snap.spot_price
                row['label_move_30m'] = move
                # Directional label: 1 if Bullish (>0.1% move), 0 otherwise
                row['label_bullish'] = 1 if move > 0.001 else 0
                data.append(row)
                
        return pd.DataFrame(data)

    def export_to_csv(self, symbol: str, filepath: str):
        df = self.build_training_dataset(symbol)
        if not df.empty:
            df.to_csv(filepath, index=False)
            return True
        return False
