"use client";

/**
 * DataModeContext
 * ───────────────
 * Provides a global "dataMode" toggle:
 *   'online'  → use live WebSocket data (default when market is LIVE)
 *   'offline' → force snapshot/REST data even if market is LIVE
 *
 * The Navbar renders the toggle only when the market is active (mode === 'live').
 * The Dashboard reads this context and overrides its display accordingly.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

export type DataMode = 'online' | 'offline';

interface DataModeContextValue {
    dataMode: DataMode;
    setDataMode: (mode: DataMode) => void;
    toggleDataMode: () => void;
    isOnline: boolean;
    isOffline: boolean;
}

const DataModeContext = createContext<DataModeContextValue>({
    dataMode: 'online',
    setDataMode: () => { },
    toggleDataMode: () => { },
    isOnline: true,
    isOffline: false,
});

export function DataModeProvider({ children }: { children: React.ReactNode }) {
    const [dataMode, setDataModeState] = useState<DataMode>('online');

    const setDataMode = useCallback((mode: DataMode) => {
        console.log(`📡 DataMode changed → ${mode.toUpperCase()}`);
        setDataModeState(mode);
    }, []);

    const toggleDataMode = useCallback(() => {
        setDataModeState(prev => {
            const next = prev === 'online' ? 'offline' : 'online';
            console.log(`📡 DataMode toggled → ${next.toUpperCase()}`);
            return next;
        });
    }, []);

    return (
        <DataModeContext.Provider
            value={{
                dataMode,
                setDataMode,
                toggleDataMode,
                isOnline: dataMode === 'online',
                isOffline: dataMode === 'offline',
            }}
        >
            {children}
        </DataModeContext.Provider>
    );
}

export function useDataMode() {
    return useContext(DataModeContext);
}
