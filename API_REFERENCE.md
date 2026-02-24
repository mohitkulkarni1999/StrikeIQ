# 📡 StrikeIQ — Backend API Reference

> **Base URL:** `http://localhost:8000`  
> **Frontend Proxy:** Next.js rewrites `/api/*` → `http://localhost:8000/api/*`  
> **WebSocket Base:** `ws://localhost:8000`

---

## 📋 Table of Contents

- [System](#-system)
- [Authentication](#-authentication)
- [Market](#-market)
- [Options](#-options)
- [AI Intelligence](#-ai-intelligence)
- [Predictions](#-predictions)
- [WebSocket Init (REST)](#-websocket-init-rest)
- [WebSocket Live Feed](#-websocket-live-feed)
- [Frontend Usage Flow](#-recommended-frontend-usage-flow)

---

## 🟢 System

### `GET /api/v1/health`
Check if the backend server is alive and running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-02-25T00:00:00.000000",
  "version": "2.0.0",
  "service": "StrikeIQ API"
}
```

**When to use:** On app load to show a "backend connected" indicator.

---

### `GET /api/v1/debug/routes`
Returns a list of all registered routes in the FastAPI application.

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_routes": 25,
    "routes": [
      { "path": "/api/v1/health", "methods": ["GET"], "name": "health_check" }
    ]
  }
}
```

**When to use:** Debugging only — verify which endpoints are registered.

---

## 🔐 Authentication

### `GET /api/v1/auth/upstox`
Redirects the browser to the **Upstox OAuth login page**.

> ⚠️ Do **NOT** call this via `axios`. Open it directly in the browser:
> ```js
> window.location.href = '/api/v1/auth/upstox';
> ```

After login, Upstox redirects back to `/callback` which stores the token automatically.

---

### `GET /api/v1/auth/upstox/callback?code=...&state=...`
OAuth callback — **called automatically by Upstox** after login. Do not call this manually.

**What it does:**
1. Exchanges the authorization `code` for an access token
2. Stores the token securely on the backend
3. Redirects to `http://localhost:3000/auth/success?upstox=connected`

---

### `GET /api/v1/debug/auth-session`
Returns current Upstox token status. Useful for admin/debug panels.

**Response:**
```json
{
  "authenticated": true,
  "token_expiry": "2025-02-25T10:00:00+00:00",
  "seconds_remaining": 28800,
  "refresh_supported": false,
  "debug_info": {
    "has_credentials": true,
    "credentials_file": "upstox_credentials.json",
    "current_time": "2025-02-25T00:00:00+00:00"
  }
}
```

---

## 📈 Market

### `GET /api/v1/market/session`
Returns the **full market session status** — the most important endpoint for the frontend.

**Response:**
```json
{
  "status": "success",
  "data": {
    "market_status": "OPEN",
    "engine_mode": "LIVE",
    "last_check": "2025-02-25T00:00:00.000000",
    "is_polling": true
  },
  "timestamp": "2025-02-25T00:00:00.000000"
}
```

| Field | Values | Meaning |
|---|---|---|
| `market_status` | `OPEN` / `CLOSED` / `UNKNOWN` | Is market trading right now? |
| `engine_mode` | `LIVE` / `SNAPSHOT` / `OFFLINE` | Use WebSocket (LIVE) or REST snapshot (SNAPSHOT) |
| `is_polling` | `true` / `false` | Is backend actively checking market status? |

**When to use:** On app load and every ~60s to decide if you should connect WebSocket or show snapshot data.

---

### `POST /api/v1/market/session/refresh`
Forces an **immediate re-check** of market open/closed status from Upstox.

**Response:**
```json
{
  "status": "success",
  "data": {
    "market_status": "OPEN",
    "engine_mode": "LIVE",
    "message": "Market status refreshed to OPEN"
  }
}
```

**When to use:** Add a "Refresh" button on the dashboard status bar.

---

### `GET /api/v1/market/session/status`
**Lightweight** quick status check — only two fields.

**Response:**
```json
{
  "market_status": "OPEN",
  "engine_mode": "LIVE"
}
```

**When to use:** Polling every few seconds on the UI status bar (low overhead).

---

### `GET /api/v1/market/session/health`
Returns health diagnostics of the session manager.

**Response:**
```json
{
  "healthy": true,
  "issues": [],
  "status": { "market_status": "OPEN", "engine_mode": "LIVE", "is_polling": true },
  "timestamp": "2025-02-25T00:00:00.000000"
}
```

If stale (last check > 2 minutes ago), `healthy` will be `false` and `issues` will explain why.

**When to use:** Internal health monitoring panel.

---

### `GET /api/v1/market/ltp/:symbol`
Returns **Last Traded Price** for a symbol.

**Path params:** `:symbol` = `NIFTY` or `BANKNIFTY`

**Response:**
```json
{
  "status": "success",
  "data": {
    "symbol": "NIFTY",
    "spot_price": 22543.50,
    "market_status": "OPEN",
    "session_type": "LIVE",
    "timestamp": "2025-02-25T00:00:00"
  }
}
```

**When to use:** Showing the current index price in the header/dashboard.

---

### `GET /api/v1/market/status`
Returns simple market status text.

**Response:**
```json
{
  "status": "success",
  "data": {
    "market_status": "OPEN",
    "timestamp": "2025-02-25T00:00:00",
    "description": "Market is currently open"
  }
}
```

---

## ⛓️ Options

### `GET /api/v1/options/auth/status`
Checks if the Upstox access token is **valid** (cached for 1 minute).

**Response (Authenticated):**
```json
{
  "authenticated": true,
  "message": "Token is valid",
  "timestamp": "2025-02-25T00:00:00"
}
```

**Response (Not Authenticated):**
```json
{
  "session_type": "AUTH_REQUIRED",
  "mode": "AUTH",
  "message": "No access token available",
  "login_url": "http://localhost:8000/api/v1/auth/upstox",
  "timestamp": "2025-02-25T00:00:00"
}
```

> ✅ **Always call this first** before fetching option chain data. If not authenticated, redirect user to `login_url`.

---

### `GET /api/v1/options/contract/:symbol`
Returns all **available expiry dates** for a symbol.

**Path params:** `:symbol` = `NIFTY` or `BANKNIFTY`

**Response:**
```json
{
  "status": "success",
  "data": ["2025-02-27", "2025-03-06", "2025-03-13", "2025-03-27"]
}
```

**When to use:** Populating the **expiry date dropdown** on the option chain page.

---

### `GET /api/v1/options/chain/:symbol?expiry_date=YYYY-MM-DD`
Returns the **full option chain** (calls + puts for all strikes).

**Path params:** `:symbol` = `NIFTY` or `BANKNIFTY`  
**Required query param:** `expiry_date` in `YYYY-MM-DD` format

**Response:**
```json
{
  "status": "success",
  "source": "rest",
  "data": {
    "spot_price": 22543.50,
    "atm_strike": 22500,
    "expiry_date": "2025-02-27",
    "total_strikes": 40,
    "analytics_enabled": true,
    "calls": [
      {
        "strike_price": 22500,
        "ltp": 125.50,
        "oi": 1500000,
        "volume": 45000,
        "iv": 14.5,
        "delta": 0.52,
        "gamma": 0.002,
        "theta": -12.5,
        "vega": 18.3
      }
    ],
    "puts": [ ... ]
  }
}
```

**When to use:** This is the **main data source** for the Option Chain table. Use this for REST/snapshot mode.

---

### `GET /api/v1/options/oi-analysis/:symbol`
Returns **Open Interest analysis** — max pain, PCR, support/resistance levels.

**Path params:** `:symbol` = `NIFTY` or `BANKNIFTY`

**Response:**
```json
{
  "status": "success",
  "data": {
    "max_pain": 22400,
    "pcr": 0.85,
    "total_call_oi": 12500000,
    "total_put_oi": 10600000,
    "support_levels": [22300, 22200],
    "resistance_levels": [22600, 22700],
    "timestamp": "2025-02-25T00:00:00"
  },
  "total_strikes": 40
}
```

**When to use:** The **OI Analysis widget** on the dashboard.

---

### `GET /api/v1/options/greeks/:symbol?strike=22500&option_type=CE&expiry_date=YYYY-MM-DD`
Returns **Greeks** for a single specific option contract.

**Path params:** `:symbol` = `NIFTY` or `BANKNIFTY`  
**Required query params:** `strike` (number), `option_type` (`CE` or `PE`)  
**Optional query param:** `expiry_date`

**Response:**
```json
{
  "status": "success",
  "data": {
    "strike": 22500,
    "option_type": "CE",
    "greeks": {
      "delta": 0.52,
      "gamma": 0.002,
      "theta": -12.5,
      "vega": 18.3,
      "implied_volatility": 14.5
    },
    "ltp": 125.50,
    "oi": 1500000,
    "volume": 45000
  },
  "expiry_date": "2025-02-27"
}
```

**When to use:** Detailed single-contract analysis card when user clicks a row.

---

### `GET /api/v1/options/smart-money/:symbol`
Returns **Smart Money directional bias** signal from the v1 engine.

**Path params:** `:symbol` = `NIFTY` or `BANKNIFTY`

**Response:**
```json
{
  "status": "success",
  "data": {
    "signal": "BULLISH",
    "confidence": 0.72,
    "pcr": 0.85,
    "call_oi": 12500000,
    "put_oi": 10600000,
    "max_pain": 22400,
    "reasoning": "Strong put writing at 22400 suggests institutional support"
  },
  "timestamp": "2025-02-25T00:00:00"
}
```

---

### `GET /api/v1/options/smart-money-v2/:symbol`
Same as above but uses the **v2 engine** (statistically more stable).

> ✅ Prefer `smart-money-v2` over `smart-money` for production use.

---

### `GET /api/v1/options/smart-money/performance/:symbol?days=30`
Returns **historical accuracy metrics** for the Smart Money engine.

**Query param:** `days` (1–365, default `30`)

**Response:**
```json
{
  "status": "success",
  "data": {
    "total_predictions": 120,
    "correct_predictions": 87,
    "accuracy": 0.725,
    "bullish_accuracy": 0.76,
    "bearish_accuracy": 0.69,
    "period_days": 30
  }
}
```

**When to use:** Performance Tracking chart/stats section.

---

### `POST /api/v1/options/smart-money/update-results/:symbol?lookback_minutes=30`
Triggers the backend to **compare past predictions** against actual market moves.

**Query param:** `lookback_minutes` (5–120, default `30`)

**When to use:** Call this periodically (e.g. every 30 min during market hours) to keep accuracy metrics fresh.

---

## 🤖 AI Intelligence

### `POST /api/v1/intelligence/interpret`
Sends a market intelligence data object to the **AI interpreter service** and gets a human-readable narrative back.

**Request body:** Any market intelligence object (from the option chain or smart money data)
```json
{
  "signal": "BULLISH",
  "pcr": 0.85,
  "max_pain": 22400,
  "spot_price": 22543
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "narrative": "Market is showing bullish bias with strong put writing at 22400...",
    "key_observations": ["PCR below 1 indicates call dominance", "Max pain at 22400"],
    "risk_level": "MODERATE"
  },
  "timestamp": "2025-02-25T00:00:00"
}
```

**When to use:** Generate AI commentary beneath the dashboard widgets.

---

## 📊 Predictions

### `GET /api/v1/predictions/:symbol`
Returns **AI-generated predictions** for a symbol.

**Path params:** `:symbol` = `NIFTY` or `BANKNIFTY`

**Response:**
```json
{
  "status": "success",
  "data": {
    "bullish_probability": 0.65,
    "volatility_probability": 0.35,
    "confidence_score": 0.72,
    "regime": "BULLISH",
    "expected_move": 150.5,
    "time_horizon": "30min",
    "model_version": "v1.0"
  },
  "symbol": "NIFTY"
}
```

> ⚠️ **Note:** Currently returns placeholder/hardcoded data. AI model integration is pending.

---

## 🔌 WebSocket Init (REST)

These are regular HTTP endpoints that manage the WebSocket session state.

### `GET /api/ws/init`
**Initializes the backend WebSocket feed.** Must be called **once** after OAuth login succeeds.

**Response:**
```json
{ "status": "connected" }
```

> ✅ After this returns `"connected"`, you can open the live WebSocket connection below.

---

### `GET /api/ws/status`
Checks if the WebSocket session is active for the current client.

**Response (active):** `{ "status": "connected" }`  
**Response (inactive):** `401 Unauthorized` — `{ "msg": "not ready" }`

---

## ⚡ WebSocket Live Feed

```
ws://localhost:8000/ws/live-options/:symbol?expiry=YYYY-MM-DD
```

### Parameters
| Param | Required | Description |
|---|---|---|
| `:symbol` | ✅ | `NIFTY` or `BANKNIFTY` |
| `expiry` | ✅ | Expiry date in `YYYY-MM-DD` format |

### Prerequisites
1. Call `GET /api/ws/init` and get `{ "status": "connected" }`
2. Backend must have a valid Upstox token
3. Market must be `OPEN` (otherwise server closes with code `1011`)

### Message Format (received from server every ~1 second)

**On connect:**
```json
{
  "status": "connected",
  "symbol": "NIFTY",
  "message": "WebSocket connection successful",
  "timestamp": "2025-02-25T00:00:00+00:00"
}
```

**Live data stream:**
```json
{
  "status": "market_data",
  "data": {
    "spot_price": 22543.50,
    "atm_strike": 22500,
    "calls": [ ... ],
    "puts": [ ... ]
  },
  "market_status": "OPEN",
  "timestamp": "2025-02-25T00:00:00+00:00"
}
```

**On error:**
```json
{
  "status": "error",
  "message": "Authentication required",
  "timestamp": "2025-02-25T00:00:00+00:00"
}
```

### Close Codes
| Code | Reason |
|---|---|
| `1000` | Normal / manual disconnect |
| `1011` | Backend WS feed not running (market closed or not initialized) |

---

## 🔄 Recommended Frontend Usage Flow

```
App Load
  │
  ├─► GET /api/v1/health           → Backend alive?
  │
  ├─► GET /api/v1/options/auth/status → Authenticated?
  │       │
  │       ├── NO  → Redirect to /api/v1/auth/upstox (OAuth login)
  │       │               │
  │       │               └─► After login → GET /api/ws/init
  │       │
  │       └── YES ──────────────────────────────────────────┐
  │                                                          │
  ├─► GET /api/v1/market/session    → market_status?         │
  │       │                                                  │
  │       ├── OPEN  → Connect WebSocket                      │
  │       │            ws://localhost:8000/ws/live-options/NIFTY?expiry=...
  │       │            (streams data every 1s)               │
  │       │                                                  │
  │       └── CLOSED → GET /api/v1/options/chain/NIFTY?expiry_date=...
  │                    (one-time REST snapshot)              │
  │                                                          │
  ├─► GET /api/v1/options/contract/NIFTY  → Expiry dates ◄──┘
  ├─► GET /api/v1/options/oi-analysis/NIFTY
  ├─► GET /api/v1/options/smart-money-v2/NIFTY
  └─► POST /api/v1/intelligence/interpret  → AI narrative
```

---

## 🛠️ Quick Reference

| Category | Endpoint | Method |
|---|---|---|
| Health | `/api/v1/health` | GET |
| Auth Login | `/api/v1/auth/upstox` | GET (browser redirect) |
| Auth Status | `/api/v1/options/auth/status` | GET |
| Market Session | `/api/v1/market/session` | GET |
| Market Status | `/api/v1/market/session/status` | GET |
| LTP | `/api/v1/market/ltp/:symbol` | GET |
| Expiry Dates | `/api/v1/options/contract/:symbol` | GET |
| Option Chain | `/api/v1/options/chain/:symbol?expiry_date=` | GET |
| OI Analysis | `/api/v1/options/oi-analysis/:symbol` | GET |
| Greeks | `/api/v1/options/greeks/:symbol?strike=&option_type=` | GET |
| Smart Money v2 | `/api/v1/options/smart-money-v2/:symbol` | GET |
| Performance | `/api/v1/options/smart-money/performance/:symbol` | GET |
| AI Interpret | `/api/v1/intelligence/interpret` | POST |
| WS Init | `/api/ws/init` | GET |
| WS Live Feed | `ws://localhost:8000/ws/live-options/:symbol?expiry=` | WebSocket |
