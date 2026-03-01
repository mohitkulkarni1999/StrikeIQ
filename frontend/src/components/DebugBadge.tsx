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
                if (!sessionResponse.ok) {
                    console.warn(`HTTP Error in DebugBadge: ${sessionResponse.status}`);
                    return;
                }
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

        // Update every 10 seconds
        const interval = setInterval(fetchDebugInfo, 10000);

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
        <div className={`bg-white/3 border border-white/6 rounded-xl p-3 ${className}`}>
            {/* Panel Header */}
            <div className="text-xs font-semibold text-[#5cc8ff] mb-3 uppercase tracking-wider">
                Market Data Status
            </div>
            
            {/* Status Grid */}
            <div className="grid grid-cols-[140px_auto] gap-y-2">
                {/* Engine */}
                <div className="text-[11px] uppercase tracking-wider text-[#8a8a8a]">
                    Engine
                </div>
                <div className="text-[13px] font-semibold text-white">
                    {debugInfo.engineMode}
                </div>
                
                {/* Market */}
                <div className="text-[11px] uppercase tracking-wider text-[#8a8a8a]">
                    Market
                </div>
                <div className="text-[13px] font-semibold text-white">
                    {debugInfo.marketStatus}
                </div>
                
                {/* Source */}
                <div className="text-[11px] uppercase tracking-wider text-[#8a8a8a]">
                    Source
                </div>
                <div className="text-[13px] font-semibold text-white">
                    {debugInfo.dataSource}
                </div>
                
                {/* Spot */}
                <div className="text-[11px] uppercase tracking-wider text-[#8a8a8a]">
                    Spot
                </div>
                <div className="text-[13px] font-semibold text-white">
                    {debugInfo.spotSource}
                </div>
                
                {/* Mode */}
                <div className="text-[11px] uppercase tracking-wider text-[#8a8a8a]">
                    Mode
                </div>
                <div className="text-[13px] font-semibold text-white">
                    {debugInfo.mode}
                </div>
            </div>
        </div>
    );
};

export default DebugBadge;
