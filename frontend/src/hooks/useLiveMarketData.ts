import { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';

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
    isConnected: boolean;
    symbol: string;
    availableExpiries: string[];
    lastUpdate: string;
}

/**
 * WebSocket-only Market Data Hook
 * - Uses global WebSocket context for real-time data
 * - No REST polling - relies entirely on WebSocket
 * - Provides real-time streaming data
 */
export function useLiveMarketData(symbol: string, expiry: string | null): UseLiveMarketDataReturn {
    console.log("🔌 useLiveMarketData INIT", { symbol, expiry });

    const [data, setData] = useState<LiveMarketData | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<'loading' | 'snapshot' | 'live' | 'error'>('loading');

    // Use global WebSocket context
    const { isConnected, lastMessage, connect, error: wsError } = useWebSocket();

    // Handle WebSocket messages
    useEffect(() => {
        if (!lastMessage) return;

        console.log("📨 Processing WebSocket message:", lastMessage);

        try {
            // Handle different message types
            if (lastMessage.status === 'connected') {
                console.log("✅ Initial connection message received");
                setData(prev => ({
                    ...prev,
                    ...lastMessage,
                    available_expiries: lastMessage.available_expiries || []
                }));
                setMode('live');
                setLoading(false);
            } else if (lastMessage.status === 'live_update') {
                console.log("🔄 Live update received");

                // Transform backend payload to frontend expected shape
                const transformedData: LiveMarketData = {
                    ...lastMessage,
                    // Map intelligence directly
                    intelligence: lastMessage.intelligence || {},
                    // Map pin_probability directly  
                    pin_probability: lastMessage.pin_probability,
                    // Map optionChain from option_chain_snapshot
                    optionChain: lastMessage.option_chain_snapshot ? {
                        symbol: lastMessage.option_chain_snapshot.symbol,
                        spot: lastMessage.option_chain_snapshot.spot,
                        expiry: lastMessage.option_chain_snapshot.expiry,
                        calls: lastMessage.option_chain_snapshot.calls || [],
                        puts: lastMessage.option_chain_snapshot.puts || []
                    } : null,
                    // Extract confidence from intelligence
                    confidence: lastMessage.intelligence?.bias?.confidence || lastMessage.intelligence?.confidence,
                    // Map expiries for frontend
                    expiries: lastMessage.available_expiries || [],
                    // Ensure required fields
                    symbol: symbol,
                    spot: lastMessage.spot || 0,
                    timestamp: lastMessage.timestamp || new Date().toISOString()
                };

                setData(prev => ({
                    ...prev,
                    ...transformedData
                }));
                setMode('live');
                setLoading(false);
            } else if (lastMessage.status === 'auth_required') {
                setError('Authentication required');
                setMode('error');
            } else if (lastMessage.status === 'auth_error') {
                setError('Authentication service unavailable');
                setMode('error');
            }
        } catch (err) {
            console.error('❌ Error parsing WebSocket message:', err);
            setError('Failed to parse WebSocket message');
            setMode('error');
        }
    }, [lastMessage, symbol]);

    // Handle WebSocket errors
    useEffect(() => {
        if (wsError) {
            console.error('❌ WebSocket error from context:', wsError);
            setError(wsError);
            setMode('error');
        }
    }, [wsError]);

    // Update connection status
    useEffect(() => {
        if (isConnected) {
            console.log('✅ WebSocket connected, setting mode to live');
            setMode('live');
            setLoading(false);
            setError(null);
        } else {
            console.log('❌ WebSocket disconnected');
            setMode('loading');
            setLoading(true);
        }
    }, [isConnected]);

    // Initialize connection if not connected and we have symbol/expiry
    useEffect(() => {
        if (symbol && expiry && !isConnected && mode === 'loading') {
            console.log(`🚀 Initializing WebSocket connection for ${symbol} with expiry ${expiry}`);
            connect(symbol, expiry);
        }
    }, [symbol, expiry, isConnected, mode, connect]);

    return {
        data,
        loading,
        error,
        mode,
        isConnected,
        symbol,
        availableExpiries: data?.available_expiries || [],
        lastUpdate: new Date().toISOString(),
        status: null
    };
}
