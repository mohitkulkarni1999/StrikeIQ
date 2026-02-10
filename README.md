# StrikeIQ - Options Market Intelligence SaaS

AI-powered options market intelligence platform for Indian markets (NIFTY & BANKNIFTY).

## Features

### Market Bias Engine
- Price vs VWAP analysis
- 5-minute OI change calculations
- Put-Call Ratio (PCR) computation
- Price-OI divergence detection
- Bullish/Bearish/Neutral bias with confidence percentage

### Expected Move Engine
- Expected move calculation using ATM Call + ATM Put premiums
- Current price vs expected range display
- Breakout condition flagging

### Smart Money Activity Detector
- Aggressive call writing detection
- Aggressive put writing detection
- Long/short buildup identification
- Liquidity trap zone detection

### Dashboard UI
- Dark theme interface
- Real-time bias meter
- OI heatmap visualization
- Expected move range display
- Trap risk indicator

## Architecture

- **Backend**: Python with FastAPI
- **Data Processing**: Pandas, NumPy
- **Database**: PostgreSQL
- **Frontend**: Next.js with TailwindCSS
- **Real-time**: WebSocket connections

## Project Structure

```
StrikeIQ/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── data/           # Data layer
│   │   ├── engines/        # Analysis engines
│   │   ├── models/         # Database models
│   │   └── services/       # Business logic
│   ├── requirements.txt
│   └── main.py
├── frontend/               # Next.js frontend
│   ├── components/
│   ├── pages/
│   ├── styles/
│   ├── package.json
│   └── next.config.js
├── docker-compose.yml
└── README.md
```

## Quick Start

1. Clone the repository
2. Set up environment variables
3. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

See `.env.example` for required environment variables.
