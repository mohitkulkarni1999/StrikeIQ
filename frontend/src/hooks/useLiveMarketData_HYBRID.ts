/**
 * Hybrid WebSocket + REST Market Data Hook
 * - Uses WebSocket for real-time options chain data
 * - Falls back to REST API when WebSocket fails
 * - Provides best of both worlds: real-time streaming + reliability
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import api from '../lib/api';

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

// Main hook interface
interface UseLiveMarketDataReturn {
    data: any;
    loading: boolean;
    error: string | null;
    mode: 'loading' | 'snapshot' | 'live' | 'error';
    isConnected: boolean;
    symbol: string | null;
    availableExpiries: string[];
    lastUpdate: string | null;
}

export function useLiveMarketData(symbol: string, expiry: string | null): UseLiveMarketDataReturn {
    console.log("🔥 useLiveMarketData INIT (HYBRID)", { symbol, expiry });
    
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [mode, setMode] = useState<'loading' | 'snapshot' | 'live' | 'error'>('loading');
    const [isConnected, setIsConnected] = useState<boolean>(false);
    
    // Refs for WebSocket lifecycle
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectRef = useRef<number>(0);
    const mountedRef = useRef<boolean>(true);
    const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
    
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
            console.log("🧹 Cleaned up market data connections");
        };
    }, []);
    
    // WebSocket connection function
    const connectWebSocket = useCallback((symbol: string, expiry: string | null) => {
        if (!symbol) return;
        
        const url = expiry
            ? `ws://localhost:8000/ws/live-options/${symbol}?expiry_date=${encodeURIComponent(expiry)}`
            : `ws://localhost:8000/ws/live-options/${symbol}`;
        
        console.log("🔗 CONNECTING TO WebSocket:", url);
        
        const ws = new WebSocket(url);
        wsRef.current = ws;
        
        ws.onopen = () => {
            if (!mountedRef.current) return;
            
            reconnectRef.current = 0;
            setError(null);
            setLoading(false);
            setMode('live');
            setIsConnected(true);
            console.log("✅ WebSocket Connected for real-time data");
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
            
            console.log(`🔄 Reconnecting WebSocket in ${delay}ms (attempt ${reconnectRef.current})`);
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
            
            // Close to trigger reconnect logic
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
        
        // Connect immediately
        connectWebSocket(symbol, expiry);
    }, [symbol, expiry, connectWebSocket]);
    
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
            
            console.log("📡 FETCHING REST API:", apiUrl);
            
            const response = await fetch(apiUrl);
            const result = await response.json();
            
            if (result.status === 'success') {
                setData(result.data);
                setMode('live');
                console.log("✅ REST API data fetched successfully");
            } else {
                throw new Error(result.error || 'Failed to fetch market data');
            }
        } catch (err) {
            console.error('❌ REST API fetch error:', err);
            setError(err instanceof Error ? err.message : 'Failed to fetch market data');
            setMode('error');
        } finally {
            setLoading(false);
        }
    }, [symbol, expiry]);
    
    // Start WebSocket and set up REST fallback
    useEffect(() => {
        mountedRef.current = true;
        
        // Try WebSocket first for real-time data
        connectWebSocket(symbol, expiry);
        
        // Set up REST polling as fallback (every 30 seconds)
        pollIntervalRef.current = setInterval(() => {
            if (mountedRef.current && !isConnected) {
                console.log("🔄 WebSocket not connected, polling REST API as fallback");
                pollMarketData();
            }
        }, 30000); // 30 seconds
        
        return () => {
            mountedRef.current = false;
            
            if (wsRef.current) {
                wsRef.current.close();
                wsRef.current = null;
            }
            
            if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
            }
            
            console.log("🧹 Cleaned up market data connections");
        };
    }, [symbol, expiry, connectWebSocket, pollMarketData]);
    
    return {
        data,
        loading,
        error,
        mode,
        isConnected,
        symbol,
        availableExpiries: data?.available_expiries || [],
        lastUpdate: data?.timestamp || null
    };
}
