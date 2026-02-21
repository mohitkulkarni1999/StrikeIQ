import React, { useState, useEffect } from 'react';
import { Activity, Wifi, Database, Clock, AlertTriangle } from 'lucide-react';

interface DebugBadgeProps {
    className?: string;
}

interface DebugInfo {
    engineMode: string;
    marketStatus: string;
    dataSource: string;
    spotSource: string;
    mode: string;
}

const DebugBadge: React.FC<DebugBadgeProps> = ({ className = "" }) => {
    const [debugInfo, setDebugInfo] = useState<DebugInfo>({
        engineMode: 'UNKNOWN',
        marketStatus: 'UNKNOWN',
        dataSource: 'UNKNOWN',
        spotSource: 'UNKNOWN',
        mode: 'UNKNOWN'
    });

    useEffect(() => {
        const fetchDebugInfo = async () => {
            try {
                // Get market session info
                const sessionResponse = await fetch('/api/v1/market/session');
                const sessionResult = await sessionResponse.json();
                
                if (sessionResult.status === 'success') {
                    const sessionData = sessionResult.data;
                    
                    setDebugInfo({
                        engineMode: sessionData.engine_mode || 'UNKNOWN',
                        marketStatus: sessionData.market_status || 'UNKNOWN',
                        dataSource: sessionData.data_source || 'UNKNOWN',
                        spotSource: sessionData.engine_mode === 'LIVE' ? 'WS' : 'REST',
                        mode: sessionData.engine_mode === 'LIVE' ? 'LIVE' : 
                             sessionData.engine_mode === 'HALTED' ? 'HALTED' : 'SNAPSHOT'
                    });
                }
            } catch (err) {
                console.error('Debug info fetch error:', err);
            }
        };

        fetchDebugInfo();
        
        // Update every 5 seconds
        const interval = setInterval(fetchDebugInfo, 5000);
        
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (mode: string) => {
        switch (mode) {
            case 'LIVE':
                return 'text-green-400 bg-green-500/20 border-green-500/40';
            case 'SNAPSHOT':
                return 'text-blue-400 bg-blue-500/20 border-blue-500/40';
            case 'HALTED':
                return 'text-red-500 bg-red-500/20 border-red-500/40';
            case 'OFFLINE':
                return 'text-gray-400 bg-gray-500/20 border-gray-500/40';
            default:
                return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/40';
        }
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'engine':
                return <Activity className="w-3 h-3" />;
            case 'market':
                return <Clock className="w-3 h-3" />;
            case 'data':
                return <Database className="w-3 h-3" />;
            case 'spot':
                return <Wifi className="w-3 h-3" />;
            default:
                return <AlertTriangle className="w-3 h-3" />;
        }
    };

    return (
        <div className={`flex flex-col gap-1 p-2 bg-card border border-border rounded text-xs font-mono ${className}`}>
            {/* Engine Mode */}
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                    {getIcon('engine')}
                    <span className="text-text-secondary">Engine:</span>
                </div>
                <span className={`px-2 py-0.5 rounded border ${getStatusColor(debugInfo.engineMode)}`}>
                    {debugInfo.engineMode}
                </span>
            </div>

            {/* Market Status */}
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                    {getIcon('market')}
                    <span className="text-text-secondary">Market:</span>
                </div>
                <span className={`px-2 py-0.5 rounded border ${getStatusColor(debugInfo.marketStatus)}`}>
                    {debugInfo.marketStatus}
                </span>
            </div>

            {/* Data Source */}
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                    {getIcon('data')}
                    <span className="text-text-secondary">Source:</span>
                </div>
                <span className={`px-2 py-0.5 rounded border ${getStatusColor(debugInfo.dataSource)}`}>
                    {debugInfo.dataSource}
                </span>
            </div>

            {/* Spot Source */}
            <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                    {getIcon('spot')}
                    <span className="text-text-secondary">Spot:</span>
                </div>
                <span className={`px-2 py-0.5 rounded border ${getStatusColor(debugInfo.spotSource)}`}>
                    {debugInfo.spotSource}
                </span>
            </div>

            {/* Combined Mode Display */}
            <div className="flex items-center gap-2 pt-1 border-t border-border">
                <span className="text-text-secondary">Mode:</span>
                <span className={`px-2 py-0.5 rounded font-bold ${getStatusColor(debugInfo.mode)}`}>
                    {debugInfo.mode}
                </span>
            </div>
        </div>
    );
};

export default DebugBadge;
