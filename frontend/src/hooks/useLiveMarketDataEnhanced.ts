import { useState, useEffect, useRef, useCallback } from 'react';

// Enhanced interfaces for backend response
interface MarketSessionData {
    market_status: 'OPEN' | 'CLOSED' | 'PRE_OPEN' | 'OPENING_END' | 'CLOSING' | 'CLOSING_END' | 'HALTED' | 'UNKNOWN';
    engine_mode: 'LIVE' | 'SNAPSHOT' | 'HALTED' | 'OFFLINE';
    data_source: 'websocket_stream' | 'rest_snapshot';
    last_check?: string;
    is_polling?: boolean;
}

interface LiveMarketData {
    symbol: string;
    spot: number;
    change?: number;
    change_percent?: number;
    analytics: any;
    intelligence: any;
    timestamp: string;
    // Additional engine-specific fields
    structural_regime?: string;
    regime_confidence?: number;
    regime_stability?: number;
    acceleration_index?: number;
    regime_dynamics?: any;
    pin_probability?: number;
    flow_gamma_interaction?: any;
    expiry_magnet_analysis?: any;
    expected_move_data?: any;
    smart_money_activity?: any;
    option_chain_intelligence?: any;
    gamma_pressure_map?: any;
    alerts?: any[];
    available_expiries?: string[];
    // Market session fields
    market_status?: string;
    engine_mode?: string;
    data_source?: string;
    // Normalized option chain data
    optionChain?: {
        symbol: string;
        spot: number;
        expiry: string;
        calls: any[];
        puts: any[];
    } | null;
}

interface UseLiveMarketDataReturn {
    data: LiveMarketData | null;
    status: MarketSessionData | null;
    loading: boolean;
    error: string | null;
    mode: 'loading' | 'snapshot' | 'live' | 'halted' | 'error';
    isConnected: boolean;
    symbol: string;
    availableExpiries: string[];
    lastUpdate: string;
}

/**
 * Enhanced Market Data Hook with NSE Trading Phase Support
 * - Properly handles market session states
 * - Prevents stale WS data usage
 * - Implements snapshot mode safety
 */
export function useLiveMarketData(symbol: string, expiry: string | null): UseLiveMarketDataReturn {
    console.log("🚀 Enhanced useLiveMarketData INIT", { symbol, expiry });
    
    const [data, setData] = useState<LiveMarketData | null>(null);
    const [marketStatus, setMarketStatus] = useState<MarketSessionData | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<'loading' | 'snapshot' | 'live' | 'halted' | 'error'>('loading');
    const [isConnected, setIsConnected] = useState<boolean>(false);
    
    // Refs for lifecycle management
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectRef = useRef<number>(0);
    const mountedRef = useRef<boolean>(true);
    const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const marketStatusIntervalRef = useRef<NodeJS.Timeout | null>(null);
    
    // Mount/unmount handling
    useEffect(() => {
        mountedRef.current = true;
        return () => {
            mountedRef.current = false;
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
            if (marketStatusIntervalRef.current) {
                clearInterval(marketStatusIntervalRef.current);
            }
            console.log("🧹 Enhanced market data connections cleaned up");
        };
    }, []);
    
    // Fetch market session status
    const fetchMarketStatus = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/market/session');
            const result = await response.json();
            
            if (result.status === 'success') {
                const sessionData = result.data;
                setMarketStatus(sessionData);
                
                // Update mode based on engine_mode
                switch (sessionData.engine_mode) {
                    case 'LIVE':
                        setMode('live');
                        console.log("🟢 FRONTEND MODE ACTIVATED: LIVE MODE");
                        break;
                    case 'SNAPSHOT':
                        setMode('snapshot');
                        console.log("🔵 FRONTEND MODE ACTIVATED: SNAPSHOT MODE");
                        break;
                    case 'HALTED':
                        setMode('halted');
                        console.log("🔴 FRONTEND MODE ACTIVATED: HALTED MODE");
                        break;
                    case 'OFFLINE':
                        setMode('error');
                        console.log("⚫ FRONTEND MODE ACTIVATED: OFFLINE MODE");
                        break;
                    default:
                        setMode('error');
                        console.log("❌ FRONTEND MODE ACTIVATED: UNKNOWN MODE");
                }
                
                return sessionData;
            }
        } catch (err) {
            console.error('❌ Market status fetch error:', err);
            setMode('error');
        }
    }, []);
    
    // WebSocket connection function (only in LIVE mode)
    const connectWebSocket = useCallback((symbol: string, expiry: string | null) => {
        if (!symbol || mode !== 'live') {
            console.log(`🚫 WebSocket connection skipped - mode: ${mode}`);
            return;
        }
        
        const url = expiry
            ? `ws://localhost:8000/ws/live-options/${symbol}?expiry_date=${encodeURIComponent(expiry)}`
            : `ws://localhost:8000/ws/live-options/${symbol}`;
        
        console.log("🔌 CONNECTING TO WebSocket:", url);
        
        const ws = new WebSocket(url);
        wsRef.current = ws;
        
        ws.onopen = () => {
            if (!mountedRef.current) return;
            
            reconnectRef.current = 0;
            setError(null);
            setLoading(false);
            setIsConnected(true);
            console.log("✅ WebSocket Connected for real-time data");
        };
        
        ws.onmessage = (event) => {
            if (!mountedRef.current) return;
            
            try {
                console.log("📨 RAW WS MESSAGE:", event.data);
                const messageData = JSON.parse(event.data);
                
                // Only process WS data in LIVE mode
                if (mode === 'live') {
                    // Transform backend payload to frontend expected shape
                    const transformedData = {
                        ...messageData,
                        market_status: marketStatus?.market_status,
                        engine_mode: marketStatus?.engine_mode,
                        data_source: marketStatus?.data_source,
                        // Map intelligence directly
                        intelligence: messageData.intelligence || {},
                        // Map optionChain from option_chain_snapshot
                        optionChain: messageData.option_chain_snapshot ? {
                            symbol: messageData.option_chain_snapshot.symbol,
                            spot: messageData.option_chain_snapshot.spot,
                            expiry: messageData.option_chain_snapshot.expiry,
                            calls: messageData.option_chain_snapshot.calls || [],
                            puts: messageData.option_chain_snapshot.puts || []
                        } : null,
                        // Map expiries for frontend
                        available_expiries: messageData.available_expiries || []
                    };
                    
                    setData(prev => ({ ...prev, ...transformedData }));
                }
            } catch (err) {
                console.error('❌ Error parsing WebSocket message:', err);
            }
        };
        
        ws.onclose = (event) => {
            if (!mountedRef.current) return;
            
            console.log(`🔌 WebSocket closed: ${event.code} ${event.reason}`);
            setIsConnected(false);
            
            // Don't reconnect for manual closes or non-live modes
            if (event.code === 1000 || mode !== 'live') {
                console.log('🚫 Manual close or non-live mode, not reconnecting');
                return;
            }
            
            // Exponential backoff with max cap (only in LIVE mode)
            if (mode === 'live') {
                const delay = Math.min(10000, 1000 * 2 ** reconnectRef.current);
                reconnectRef.current += 1;
                
                console.log(`🔄 Reconnecting WebSocket in ${delay}ms (attempt ${reconnectRef.current})`);
                setTimeout(() => {
                    if (mountedRef.current && mode === 'live') {
                        connectWebSocket(symbol, expiry);
                    }
                }, delay);
            }
        };
        
        ws.onerror = (error) => {
            if (!mountedRef.current) return;
            
            console.error('❌ WebSocket Error:', error);
            setError('Connection error');
            setIsConnected(false);
            
            // Close to trigger reconnect logic (only in LIVE mode)
            if (wsRef.current && mode === 'live') {
                wsRef.current.close();
            }
        };
        
    }, [mode, marketStatus]);
    
    // REST API polling fallback
    const pollMarketData = useCallback(async () => {
        if (!symbol || !mountedRef.current) return;
        
        try {
            setLoading(true);
            setError(null);
            
            // Build API URL with optional expiry
            const apiUrl = expiry 
                ? `/api/v1/market-data/${symbol}?expiry=${encodeURIComponent(expiry)}`
                : `/api/v1/market-data/${symbol}`;
            
            console.log("📡 FETCHING:", apiUrl);
            
            const response = await fetch(apiUrl);
            const result = await response.json();
            
            if (result.status === 'success') {
                const enhancedData = {
                    ...result.data,
                    market_status: marketStatus?.market_status,
                    engine_mode: marketStatus?.engine_mode,
                    data_source: marketStatus?.data_source
                };
                
                setData(enhancedData);
                
                // Set mode based on engine_mode from backend
                if (marketStatus) {
                    // Mode is already set by fetchMarketStatus
                    console.log(`✅ Market data fetched successfully - Mode: ${mode}`);
                } else {
                    // Fallback if market status not yet fetched
                    setMode('snapshot');
                }
            } else {
                throw new Error(result.error || 'Failed to fetch market data');
            }
        } catch (err) {
            console.error('❌ Market data fetch error:', err);
            setError(err instanceof Error ? err.message : 'Failed to fetch market data');
            setMode('error');
        } finally {
            setLoading(false);
        }
    }, [symbol, expiry, mode, marketStatus]);
    
    // Start market status monitoring on mount
    useEffect(() => {
        fetchMarketStatus();
        
        // Poll market status every 30 seconds
        marketStatusIntervalRef.current = setInterval(fetchMarketStatus, 30000);
        
        return () => {
            if (marketStatusIntervalRef.current) {
                clearInterval(marketStatusIntervalRef.current);
            }
        };
    }, [fetchMarketStatus]);
    
    // Start data fetching based on mode
    useEffect(() => {
        if (!marketStatus) return;
        
        if (mode === 'live') {
            // Start WebSocket connection
            connectWebSocket(symbol, expiry);
        } else {
            // Use REST polling for snapshot/halted modes
            console.log(`📸 Using REST snapshot mode - Engine: ${marketStatus.engine_mode}`);
            pollMarketData();
            
            // Set up polling interval (every 15 seconds for snapshot modes)
            pollIntervalRef.current = setInterval(() => {
                if (mountedRef.current && mode !== 'live') {
                    pollMarketData();
                }
            }, 15000);
        }
        
        return () => {
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
        };
    }, [symbol, expiry, mode, marketStatus, connectWebSocket, pollMarketData]);

    // Effective spot price based on mode
    const effectiveSpot = data && mode === 'live' 
        ? data.spot 
        : data?.spot;

    return {
        data,
        status: marketStatus,
        loading,
        error,
        mode,
        isConnected: mode === 'live' ? isConnected : true, // Always "connected" for snapshot modes
        symbol,
        availableExpiries: data?.available_expiries || [],
        lastUpdate: new Date().toISOString(),
        effectiveSpot
    };
}
