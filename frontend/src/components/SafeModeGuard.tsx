import React from 'react';

interface SafeModeGuardProps {
    engineMode: string;
    dataSource: string;
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

/**
 * SafeModeGuard - Implements comprehensive mode-based guards
 * Prevents components from running in inappropriate modes
 */
const SafeModeGuard: React.FC<SafeModeGuardProps> = ({ 
    engineMode, 
    dataSource, 
    children, 
    fallback = null 
}) => {
    
    // ENGINE MODE UI VALIDATION GUARD
    if (engineMode !== "LIVE") {
        // Disable live animations and WS-dependent components
        console.log(`🛡️ SafeModeGuard: Disabling live features - Engine mode: ${engineMode}`);
        
        if (fallback) {
            return <>{fallback}</>;
        }
        
        // Return children with disabled state if no fallback provided
        return (
            <div className="opacity-50 pointer-events-none">
                {children}
            </div>
        );
    }
    
    // STALE WS DATA PREVENTION GUARD
    if (engineMode === "SNAPSHOT" && dataSource === "rest_snapshot") {
        console.log("🛡️ SafeModeGuard: Using snapshot mode - preventing stale WS data");
        
        // Children can render but should use REST data only
        return <>{children}</>;
    }
    
    // LIVE MODE - Full functionality
    console.log("✅ SafeModeGuard: Live mode enabled - full functionality");
    return <>{children}</>;
};

/**
 * Hook to check if component should be enabled based on mode
 */
export const useModeGuard = (engineMode: string, requiredMode: 'LIVE' | 'SNAPSHOT' | 'HALTED' | 'ANY') => {
    if (requiredMode === 'ANY') return true;
    return engineMode === requiredMode;
};

/**
 * Hook to get effective spot price based on mode
 */
export const useEffectiveSpot = (data: any, engineMode: string) => {
    if (!data) return 0;
    
    // STALE WS DATA PREVENTION
    const effectiveSpot = engineMode === "LIVE"
        ? data.ws_tick_price || data.spot
        : data.rest_spot_price || data.spot;
    
    console.log(`🎯 Effective spot: ${effectiveSpot} (Mode: ${engineMode}, Source: ${engineMode === 'LIVE' ? 'WS' : 'REST'})`);
    
    return effectiveSpot;
};

/**
 * Hook to check if analytics should use snapshot mode
 */
export const useSnapshotAnalytics = (engineMode: string, dataSource: string) => {
    const isSnapshotMode = engineMode === "SNAPSHOT" || engineMode === "HALTED";
    const isRestSource = dataSource === "rest_snapshot";
    
    return {
        shouldUseSnapshot: isSnapshotMode && isRestSource,
        showSnapshotLabel: isSnapshotMode,
        disableLiveCalculations: isSnapshotMode,
        useRestPremiums: isSnapshotMode,
        useRestOI: isSnapshotMode
    };
};

/**
 * Hook to prevent timeout in snapshot mode
 */
export const useTimeoutProtection = (engineMode: string) => {
    const shouldPreventTimeouts = engineMode !== "LIVE";
    
    return {
        shouldPreventRetries: shouldPreventTimeouts,
        shouldPreventWSWait: shouldPreventTimeouts,
        shouldPreventPremiumWait: shouldPreventTimeouts,
        abortWSDependentCalls: shouldPreventTimeouts
    };
};

export default SafeModeGuard;
