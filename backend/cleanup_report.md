# STRIKEIQ CODEBASE CLEANUP REPORT

## BACKEND CLEANUP ANALYSIS

### PROTOBUF FILES TO REMOVE

**Duplicate/Unwanted Files:**
- `app/services/MarketDataFeedV3.proto` (duplicate - keep only in proto/)
- `app/services/MarketDataFeedV3_pb2.py` (duplicate - keep only in proto/)
- `app/websocket/protobuf/feed_response_pb2.py` (legacy file)

**Files to Keep:**
- `app/proto/MarketDataFeedV3.proto` ✅
- `app/proto/MarketDataFeedV3_pb2.py` ✅

**Import Usage Verification:**
- `app/services/upstox_protobuf_parser_v3.py` imports from `app.proto.MarketDataFeedV3_pb2` ✅
- `app/services/websocket_market_feed.py` imports from `app.proto.MarketDataFeedV3_pb2` ✅

### PRODUCTION FILES (KEEP - USED)

**Files in Use:**
- `app/core/production_architecture.py` - Referenced in production_main.py
- `app/core/production_redis_client.py` - Production Redis client
- `app/core/production_market_state_manager.py` - Production state manager
- `app/core/production_ws_manager.py` - Production WebSocket manager
- `app/api/v1/ws/market_ws_production.py` - Production WebSocket endpoint
- `production_main.py` - Production entry point

**Status:** These files are imported and used in production deployment. **DO NOT DELETE.**

### CACHE CLEANUP REQUIRED

**Files to Remove:**
- All `__pycache__` directories
- All `*.pyc` files

### FRONTEND CLEANUP ANALYSIS

### DUPLICATE COMPONENT FILES

**Duplicate Intelligence Components:**
- `AlertPanel.tsx` vs `AlertPanelFinal.tsx`
- `ConvictionPanel.tsx` vs `ConvictionPanelFinal.tsx`
- `ExpiryPanel.tsx` vs `ExpiryPanelFinal.tsx`
- `GammaPressurePanel.tsx` vs `GammaPressurePanelFinal.tsx`
- `InteractionPanel.tsx` vs `InteractionPanelFinal.tsx`
- `RegimeDynamicsPanel.tsx` vs `RegimeDynamicsPanelFinal.tsx`
- `StructuralBanner.tsx` vs `StructuralBannerFinal.tsx`
- `IntelligenceDashboard.tsx` vs `IntelligenceDashboardFinal.tsx`

**Recommendation:** Keep the "Final" versions (newer implementations) and remove the originals.

### CLEANUP ACTIONS REQUIRED

## BACKEND CLEANUP

### 1. Remove Duplicate Protobuf Files
```bash
rm app/services/MarketDataFeedV3.proto
rm app/services/MarketDataFeedV3_pb2.py
rm -rf app/websocket/protobuf/
```

### 2. Clean Python Cache
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## FRONTEND CLEANUP

### 1. Remove Duplicate Components
```bash
rm src/components/intelligence/AlertPanel.tsx
rm src/components/intelligence/ConvictionPanel.tsx
rm src/components/intelligence/ExpiryPanel.tsx
rm src/components/intelligence/GammaPressurePanel.tsx
rm src/components/intelligence/InteractionPanel.tsx
rm src/components/intelligence/RegimeDynamicsPanel.tsx
rm src/components/intelligence/StructuralBanner.tsx
rm src/pages/IntelligenceDashboard.tsx
```

## VALIDATION CHECKLIST

After cleanup, verify:

### Backend
- [ ] FastAPI server starts: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`
- [ ] No import errors in protobuf parser
- [ ] WebSocket connection works
- [ ] Message router parses index ticks without warnings

### Frontend
- [ ] Next.js development server starts: `npm run dev`
- [ ] Intelligence dashboard loads
- [ ] All components render correctly
- [ ] No import errors

## RISK ASSESSMENT

**LOW RISK:**
- Protobuf duplicate removal (verified imports)
- Cache cleanup
- Duplicate component removal (keeping Final versions)

**NO RISK:**
- Production files (all in use)
- Core service files (all referenced)

## SUMMARY

**Files to Delete: 11**
- 3 backend protobuf files
- 8 frontend duplicate components

**Files to Keep:**
- All production files (in use)
- All core service files
- Final versions of components
- Main protobuf files in proto/ directory

**Estimated Cleanup Impact:** Minimal - removing duplicates and unused files only.
