# SmartMoneyEngine v1 - Implementation Documentation

## Overview

SmartMoneyEngine v1 is a production-ready system for generating directional bias signals for NIFTY and BANKNIFTY using real option chain snapshot data. The engine analyzes multiple market microstructure features to determine smart money flow and provides confidence-scored trading signals.

## Architecture

### Core Components

1. **SmartMoneyEngine** (`app/services/market_data/smart_money_engine.py`)
   - Main engine class with all feature calculations
   - Rule-based bias generation
   - Confidence scoring algorithm
   - 30-second caching mechanism

2. **API Endpoint** (`app/api/v1/options.py`)
   - RESTful endpoint: `GET /api/v1/options/smart-money/{symbol}`
   - Input validation and error handling
   - Dependency injection for engine

3. **Database Schema** (`app/models/market_data.py`)
   - Enhanced `OptionChainSnapshot` model with required fields
   - Performance indexes for fast queries

## Feature Calculations

### Primary Features

1. **Put-Call Ratio (PCR)**
   - `PCR = total_put_oi / total_call_oi`
   - Used for sentiment analysis

2. **PCR Shift**
   - Current PCR vs 15-minute average
   - Indicates changing sentiment momentum

3. **ATM Straddle**
   - Price of at-the-money call + put
   - Measures market expectations of volatility

4. **Straddle Change %**
   - Percentage change over last 5 minutes
   - Indicates volatility expectations

5. **OI Acceleration**
   - Change in OI delta between snapshots
   - `acceleration = current_oi_delta - previous_oi_delta`

6. **IV Regime**
   - Classification: LOW/NORMAL/HIGH
   - Based on percentile of last 30 snapshots

### SQL Queries Used

```sql
-- Get latest N timestamps for symbol
SELECT DISTINCT timestamp 
FROM option_chain_snapshots 
WHERE symbol = 'NIFTY' 
ORDER BY timestamp DESC 
LIMIT 30;

-- Get all snapshots for timestamps
SELECT * FROM option_chain_snapshots 
WHERE symbol = 'NIFTY' 
AND timestamp IN (timestamps) 
ORDER BY timestamp DESC;
```

## Bias Logic

### Bullish Conditions
- Put OI increasing significantly (OI acceleration > 1000)
- PCR increasing (PCR shift > 0.1)
- ATM straddle expanding upward (> 2%)
- High PCR (> 1.2)

### Bearish Conditions
- Call OI increasing significantly (OI acceleration < -1000)
- PCR decreasing (PCR shift < -0.1)
- ATM straddle expanding downward (< -2%)
- Low PCR (< 0.8)

### Confidence Scoring

Base confidence from signal strength:
```
base_confidence = (signal_strength / total_signals) * 50
```

Boost factors:
- PCR shift contribution: `min(abs(pcr_shift) * 20, 20)`
- Straddle change: `min(abs(straddle_change) * 5, 15)`
- OI acceleration: `min(abs(oi_acceleration) / 100, 15)`

Final confidence: `min(base_confidence + boosts, 100)`

## Performance Optimizations

### Database Indexes
- `idx_option_chain_symbol`: Symbol queries
- `idx_option_chain_symbol_timestamp`: Composite index for common queries
- `ix_option_chain_snapshots_strike`: Strike queries
- `ix_option_chain_snapshots_timestamp`: Timestamp queries

### Query Optimization
- Batch fetching of snapshots
- In-memory filtering for duplicates
- Efficient timestamp-based queries
- 30-second result caching

### Caching Strategy
- Cache key: `smart_money_{symbol}`
- TTL: 30 seconds
- Automatic cache invalidation

## API Response Format

```json
{
  "status": "success",
  "data": {
    "symbol": "NIFTY",
    "timestamp": "2026-02-11T17:22:15.605881+00:00",
    "bias": "BEARISH",
    "confidence": 52.1,
    "metrics": {
      "pcr": 0.268,
      "pcr_shift": -0.004,
      "atm_straddle": 80.0,
      "straddle_change_percent": 0.0,
      "oi_acceleration": 200,
      "iv_regime": "LOW"
    },
    "reasoning": [
      "Low PCR indicating bearish sentiment"
    ]
  },
  "timestamp": "2026-02-11T22:52:15.606812"
}
```

## Validation Results

✅ **All Tests Passed**
- Bias changes when OI shifts
- Confidence changes dynamically  
- PCR updates correctly
- Works during live market simulation
- No crashes on low snapshot count
- Works after restart
- Handles expiry day scenarios

## Production Deployment

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- Standard FastAPI environment variables

### Dependencies
- SQLAlchemy 2.0+
- FastAPI
- NumPy for statistical calculations
- PostgreSQL database

### Monitoring
- Engine logs all signal generations
- API logs all requests and errors
- Performance metrics in logs

### Scaling Considerations
- Database connection pooling
- Horizontal scaling via multiple API instances
- Redis caching for production deployments
- Database read replicas for query performance

## Usage Examples

### API Calls
```bash
# Get NIFTY signal
curl "http://localhost:8000/api/v1/options/smart-money/NIFTY"

# Get BANKNIFTY signal  
curl "http://localhost:8000/api/v1/options/smart-money/BANKNIFTY"
```

### Python Integration
```python
from app.services.market_data.smart_money_engine import SmartMoneyEngine

engine = SmartMoneyEngine()
signal = await engine.generate_smart_money_signal("NIFTY", db_session)
print(f"Bias: {signal['bias']}, Confidence: {signal['confidence']}")
```

## Future Enhancements

### v2 Roadmap
- Machine learning integration for bias prediction
- Multi-timeframe analysis
- Volume-weighted OI calculations
- Greeks-based signal refinement
- Real-time streaming updates
- Historical backtesting framework

### Advanced Features
- Sentiment analysis integration
- Options flow analysis
- Institutional activity detection
- Volatility surface modeling
- Risk-adjusted signal generation

---

**Status**: ✅ Production Ready  
**Version**: v1.0  
**Last Updated**: 2026-02-11  
**Author**: Senior Quant Engineer & Fintech Backend Architect
