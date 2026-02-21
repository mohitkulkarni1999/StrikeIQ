import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../lib/api';

// Import WebSocket type safety helpers
import { isWebSocket } from './websocketTypeFix';

// Types for WebSocket messages
interface WebSocketMessage {
    status: 'success' | 'live_update' | 'error' | 'auth_required' | 'connected' | 'heartbeat';
    mode?: 'snapshot' | 'live';
    symbol?: string;
    data?: any;
    error?: string;
    timestamp: string;
    // Metadata for stability
    source?: string;
    // Option chain intelligence payload
    option_chain_intelligence?: any;
}

interface WebSocketPayload {
    status: string
    mode: string
    symbol: string
    timestamp: string
    spot: number
    option_chain_snapshot: {
        symbol: string
        spot: number
        expiry: string
        calls: any[]
        puts: any[]
    }
    analytics: any
    intelligence: any
    option_chain_intelligence: any
    pin_probability: any
    expected_move_data: any
    alerts: any[]
}

export interface LiveMarketData {
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
    // FIX 6: market_bias declared — used for VWAP in MarketMetrics
    market_bias?: {
        vwap?: number;
        current_price?: number;
        pcr?: number;
        bias_strength?: number;
    };
    // Normalized option chain data
    optionChain?: {
        symbol: string;
        spot: number;
        expiry: string;
        calls: any[];
        puts: any[];
    } | null;
}

interface MarketStatus {
    market_status?: string;
    websocket_status?: string;
    server_time?: string;
    symbol_supported?: string[];
}

interface UseLiveMarketDataReturn {
    data: LiveMarketData | null;
    status: MarketStatus | null;
    loading: boolean;
    error: string | null;
    mode: 'loading' | 'snapshot' | 'live' | 'error';
}

/**
 * Production-Grade Live Market Data Hook
 * - Prevents multiple WebSocket connections via useRef
 * - Merges state to prevent UI flicker
 * - Handles Market Status polling (Phase 1)
 * - Single source of truth for Symbol/Expiry
 */
export function useLiveMarketData(symbol: string, expiry: string | null): UseLiveMarketDataReturn {
    console.log("🔥 useLiveMarketData INIT", { symbol, expiry });
    
    const [data, setData] = useState<LiveMarketData | null>(null);
    const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<'loading' | 'snapshot' | 'live' | 'error'>('loading');

    // refs for stable WebSocket lifecycle
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectRef = useRef<number>(0);
    const mountedRef = useRef<boolean>(true);

    // Mount/unmount handling
    useEffect(() => {
        mountedRef.current = true;
        return () => {
            mountedRef.current = false;
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
        };
    }, []);

    // Connect function with proper lifecycle management
    const connectWebSocket = useCallback((symbol: string, expiry: string | null) => {
        if (!symbol) return;

        const url = expiry
            ? `ws://localhost:8000/ws/live-options/${symbol}?expiry_date=${encodeURIComponent(expiry)}`
            : `ws://localhost:8000/ws/live-options/${symbol}`;

        console.log("CONNECTING TO:", url);

        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
            if (!mountedRef.current) return;
            
            reconnectRef.current = 0;
            setError(null);
            setLoading(false);
            setMode('live');
            console.log("✅ WS Connected");
        };

        ws.onmessage = (event) => {
            if (!mountedRef.current) return;
            
            try {
                console.log("📡 RAW WS MESSAGE:", event.data);
                const messageData = JSON.parse(event.data);
                
                // Handle different message types
                if (messageData.status === 'connected') {
                    console.log("📦 Initial connection message received");
                    setData(prev => ({
                        ...prev,
                        ...messageData,
                        available_expiries: messageData.available_expiries || []
                    }));
                } else if (messageData.status === 'live_update') {
                    console.log("📦 Live update received");
                    
                    // Transform backend payload to frontend expected shape
                    const transformedData = {
                        ...messageData,
                        // Map intelligence directly
                        intelligence: messageData.intelligence || {},
                        // Map pin_probability directly  
                        pin_probability: messageData.pin_probability,
                        // Map optionChain from option_chain_snapshot
                        optionChain: messageData.option_chain_snapshot ? {
                            symbol: messageData.option_chain_snapshot.symbol,
                            spot: messageData.option_chain_snapshot.spot,
                            expiry: messageData.option_chain_snapshot.expiry,
                            calls: messageData.option_chain_snapshot.calls || [],
                            puts: messageData.option_chain_snapshot.puts || []
                        } : null,
                        // Extract confidence from intelligence
                        confidence: messageData.intelligence?.bias?.confidence || messageData.intelligence?.confidence,
                        // Map expiries for frontend
                        expiries: messageData.available_expiries || []
                    };
                    
                    setData(prev => ({
                        ...prev,
                        ...transformedData
                    }));
                } else if (messageData.status === 'auth_required') {
                    setError('Authentication required');
                    setMode('error');
                } else if (messageData.status === 'auth_error') {
                    setError('Authentication service unavailable');
                    setMode('error');
                }
            } catch (err) {
                console.error('❌ Error parsing WebSocket message:', err);
            }
        };

        ws.onclose = (event) => {
            if (!mountedRef.current) return;
            
            console.log(`🔌 WebSocket closed: ${event.code} ${event.reason}`);
            
            // Don't reconnect for manual closes or auth errors
            if (event.code === 1000 || mode === 'error') {
                console.log('🔌 Manual close or error, not reconnecting');
                return;
            }

            // Exponential backoff with max cap
            const delay = Math.min(10000, 1000 * 2 ** reconnectRef.current);
            reconnectRef.current += 1;

            console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectRef.current})`);

            setTimeout(() => {
                if (mountedRef.current && wsRef.current?.readyState !== WebSocket.OPEN) {
                    connectWebSocket(symbol, expiry);
                }
            }, delay);
        };

        ws.onerror = (error) => {
            if (!mountedRef.current) return;
            
            console.error('❌ WebSocket Error:', error);
            setError('Connection error');
            
            // ✅ FIXED: Safe type narrowing for WebSocket readyState check
            // Use type guard to safely check if event.target is a WebSocket
            if (isWebSocket(error.target)) {
                if (error.target.readyState === WebSocket.CLOSED) {
                    console.log('🔐 WebSocket connection was rejected - likely auth error');
                    // Dispatch auth expired event to trigger auth flow
                    window.dispatchEvent(new CustomEvent('auth-expired'));
                }
            }
            
            // Close to trigger reconnect logic
            if (wsRef.current) {
                wsRef.current.close();
            }
        };

    }, [symbol, expiry, mode]);

    // Force hard reconnect when symbol or expiry changes
    useEffect(() => {
        if (!symbol || !expiry) return;

        console.log("🔁 HARD RECONNECT for expiry:", expiry);

        if (wsRef.current) {
            wsRef.current.onclose = null;
            wsRef.current.onerror = null;
            wsRef.current.onmessage = null;
            wsRef.current.close();
            wsRef.current = null;
        }

        connectWebSocket(symbol, expiry);

    }, [symbol, expiry]);

    return {
        data,
        status: marketStatus,
        loading,
        error,
        mode
    };
}
