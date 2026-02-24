import { useState, useEffect } from 'react';
import { useLiveOptionsWS } from '@/core/ws/useLiveOptionsWS';

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
 * - Uses locked core WebSocket module for real-time data
 * - No REST polling - relies entirely on WebSocket
 * - Provides real-time streaming data
 */
export function useLiveMarketData(symbol: string, expiry: string | null): UseLiveMarketDataReturn {
    console.log("🔌 useLiveMarketData INIT", { symbol, expiry });

    const [data, setData] = useState<LiveMarketData | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<'loading' | 'snapshot' | 'live' | 'error'>('loading');

    // Use locked WebSocket core module
    const { isConnected, ws } = useLiveOptionsWS({
        symbol,
        expiry: expiry || '',
        onMessage: (message) => {
            if (message.status === 'connected') {
                console.log("✅ Initial connection message received");
                setData(prev => ({
                    ...prev,
                    ...message,
                    available_expiries: message.available_expiries || []
                }));
                setMode('live');
                setLoading(false);
            } else if (message.status === 'live_update') {
                console.log("🔄 Live update received");

                // Transform backend payload to frontend expected shape
                const transformedData: LiveMarketData = {
                    ...message,
                    // Map intelligence directly
                    intelligence: message.intelligence || {},
                    // Map pin_probability directly  
                    pin_probability: message.pin_probability,
                    // Map optionChain from option_chain_snapshot
                    optionChain: message.option_chain_snapshot ? {
                        symbol: message.option_chain_snapshot.symbol,
                        spot: message.option_chain_snapshot.spot,
                        expiry: message.option_chain_snapshot.expiry,
                        calls: message.option_chain_snapshot.calls || [],
                        puts: message.option_chain_snapshot.puts || []
                    } : null,
                    // Extract confidence from intelligence
                    confidence: message.intelligence?.bias?.confidence || message.intelligence?.confidence,
                    // Map expiries for frontend
                    expiries: message.available_expiries || [],
                    // Ensure required fields
                    symbol: symbol,
                    spot: message.spot || 0,
                    timestamp: message.timestamp || new Date().toISOString()
                };

                setData(prev => ({
                    ...prev,
                    ...transformedData
                }));
                setMode('live');
                setLoading(false);
            } else if (message.status === 'auth_required') {
                setError('Authentication required');
                setMode('error');
            } else if (message.status === 'auth_error') {
                setError('Authentication service unavailable');
                setMode('error');
            }
        },
        onError: (error) => {
            console.error('❌ WebSocket error from core module:', error);
            setError(error);
            setMode('error');
        }
    });

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
