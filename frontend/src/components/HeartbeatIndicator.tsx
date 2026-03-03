import React from 'react';
import { useWebSocketHeartbeat } from '@/utils/websocketHeartbeat';

/**
 * React component for heartbeat indicator
 */
export function HeartbeatIndicator() {
  const { isConnected, lastHeartbeat } = useWebSocketHeartbeat();

  if (!isConnected) {
    return (
      <div className="flex items-center gap-2 text-gray-500">
        <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
        <span className="text-xs">OFFLINE</span>
      </div>
    );
  }

  const isBeating = lastHeartbeat && (Date.now() - lastHeartbeat) < 5000; // Beating if heartbeat within 5 seconds
  const lastSeen = lastHeartbeat ? Math.floor((Date.now() - lastHeartbeat) / 1000) : 0;

  return (
    <div className="flex items-center gap-2">
      <div 
        className={`w-2 h-2 rounded-full transition-all duration-200 ${
          isBeating 
            ? 'bg-green-500 scale-125 shadow-lg shadow-green-500/50' 
            : 'bg-green-400 scale-100'
        }`}
      />
      <span className="text-xs text-green-500">
        LIVE {lastSeen > 0 ? `(${lastSeen}s ago)` : ''}
      </span>
    </div>
  );
}

export default HeartbeatIndicator;
