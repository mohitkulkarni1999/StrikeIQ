import { useState, useEffect, useRef } from 'react';
import { useLiveOptionsWS } from '@/core/ws/useLiveOptionsWS';
import { useWSStore } from '@/core/ws/wsStore';
import { clearWSInitialized } from '@/core/ws/wsInitController';

export interface LiveMarketData {
    symbol: string;
    spot: number;
    change?: number;
    change_percent?: number;
    analytics: any;
    intelligence: any;
    timestamp: string;
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
    market_bias?: {
        vwap?: number;
        current_price?: number;
        pcr?: number;
        bias_strength?: number;
    };
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
    isConnected: boolean;
    symbol: string;
    availableExpiries: string[];
    lastUpdate: string;
}

// ── Shared event name — Navbar fires this, useLiveMarketData listens ──────────
export const WS_BACKEND_ONLINE_EVENT = 'strikeiq:backend-online';

export function useLiveMarketData(symbol: string, expiry: string | null): UseLiveMarketDataReturn {

    const [data, setData] = useState<LiveMarketData | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<'loading' | 'snapshot' | 'live' | 'error'>('loading');

    // Always-current reference to reconnect — updated every render via useEffect below
    const reconnectRef = useRef<(() => void) | null>(null);

    const { reconnect } = useLiveOptionsWS({
        symbol,
        expiry: expiry || '',

        onMessage: (message) => {
            if (message.status === 'connected') {
                setData(prev => ({ ...prev, ...message, available_expiries: message.available_expiries || [] }));
                setMode(prev => prev === 'loading' ? 'snapshot' : prev);
                setLoading(false);
                setError(null);

            } else if (message.status === 'live_update') {
                const transformed: LiveMarketData = {
                    ...message,
                    intelligence: message.intelligence || {},
                    pin_probability: message.pin_probability,
                    optionChain: message.option_chain_snapshot ? {
                        symbol: message.option_chain_snapshot.symbol,
                        spot: message.option_chain_snapshot.spot,
                        expiry: message.option_chain_snapshot.expiry,
                        calls: message.option_chain_snapshot.calls || [],
                        puts: message.option_chain_snapshot.puts || [],
                    } : null,
                    confidence: message.intelligence?.bias?.confidence,
                    expiries: message.available_expiries || [],
                    symbol,
                    spot: message.spot || 0,
                    timestamp: message.timestamp || new Date().toISOString(),
                };
                setData(prev => ({ ...prev, ...transformed }));
                setMode(message.spot && message.spot > 0 ? 'live' : 'snapshot');
                setLoading(false);
                setError(null);

            } else if (message.status === 'market_data' && message.data) {
                // Handle the new market_data format from backend
                const transformed: LiveMarketData = {
                    ...message.data,
                    symbol: message.data.symbol || symbol,
                    spot: message.data.spot || 0,
                    timestamp: message.data.timestamp || new Date().toISOString(),
                    intelligence: message.data.intelligence || {},
                    optionChain: message.data.option_chain || null,
                    availableExpiries: message.data.available_expiries || [],
                };
                setData(prev => ({ ...prev, ...transformed }));
                setMode('live');
                setLoading(false);
                setError(null);

            } else if (message.status === 'auth_required') {
                setError('Authentication required'); setMode('error');
            } else if (message.status === 'auth_error') {
                setError('Authentication service unavailable'); setMode('error');
            }
        },

        onError: (err) => {
            console.warn('⚠️ WS error:', err);
            setError(err);
            setMode('error');
        },

        onDisconnect: () => {
            setMode(prev => prev === 'live' ? 'loading' : prev);
        },
    });

    // Keep reconnectRef always pointing to the latest reconnect
    useEffect(() => {
        reconnectRef.current = reconnect;
    }, [reconnect]);

    // ── Listen for the backend-online event fired by Navbar ──────────────────
    // This is the only reconnect trigger — no stale closures because we always
    // read reconnectRef.current which is updated every render.
    useEffect(() => {
        const handleBackendOnline = () => {
            console.log('🔄 [useLiveMarketData] backend-online event received → reconnecting');

            // Full reset of wsStore guards so connect() isn't blocked
            const store = useWSStore.getState();
            store.setConnected(false);
            store.setInitializing(false);
            store.setError(null);
            store.resetReconnectAttempts();
            store.setWS(null);

            // Clear the init flag so /api/ws/init is called again
            clearWSInitialized();

            // Reset UI
            setMode('loading');
            setLoading(true);
            setError(null);

            // Call reconnect via ref — always fresh, never stale
            reconnectRef.current?.();
        };

        window.addEventListener(WS_BACKEND_ONLINE_EVENT, handleBackendOnline);
        return () => window.removeEventListener(WS_BACKEND_ONLINE_EVENT, handleBackendOnline);
    }, []); // empty deps — safe because we use reconnectRef.current

    // ── Sync isConnected from wsStore ─────────────────────────────────────────
    const isConnected = useWSStore(state => state.isConnected);

    useEffect(() => {
        if (isConnected) {
            setLoading(false);
            setError(null);
        } else {
            setMode(prev => prev === 'live' ? 'loading' : prev);
        }
    }, [isConnected]);

    return {
        data, loading, error, mode, isConnected,
        symbol,
        availableExpiries: data?.available_expiries || [],
        lastUpdate: new Date().toISOString(),
        status: null,
    };
}
