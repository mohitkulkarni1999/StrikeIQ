import React, { useEffect, useState } from 'react';
import { AlertTriangle, Info, AlertCircle, X } from 'lucide-react';

interface Alert {
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string;
  metadata?: any;
}

interface AlertPanelProps {
  alerts: Alert[];
  maxVisible?: number;
}

const AlertPanel: React.FC<AlertPanelProps> = ({ alerts, maxVisible = 5 }) => {
  const [visibleAlerts, setVisibleAlerts] = useState<Alert[]>([]);
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());

  useEffect(() => {
    // Filter and sort alerts
    const filtered = alerts
      .filter(alert => !dismissedAlerts.has(`${alert.alert_type}-${alert.timestamp}`))
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, maxVisible);
    
    setVisibleAlerts(filtered);
  }, [alerts, dismissedAlerts, maxVisible]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/20 border-red-500/40 text-red-400';
      case 'high':
        return 'bg-orange-500/20 border-orange-500/40 text-orange-400';
      case 'medium':
        return 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400';
      case 'low':
        return 'bg-blue-500/20 border-blue-500/40 text-blue-400';
      default:
        return 'bg-gray-500/20 border-gray-500/40 text-gray-400';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
      case 'high':
        return <AlertTriangle className="w-4 h-4" />;
      case 'medium':
        return <AlertCircle className="w-4 h-4" />;
      case 'low':
        return <Info className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const colors = {
      critical: 'bg-red-500 text-white',
      high: 'bg-orange-500 text-white',
      medium: 'bg-yellow-500 text-black',
      low: 'bg-blue-500 text-white'
    };
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[severity as keyof typeof colors] || colors.low}`}>
        {severity.toUpperCase()}
      </span>
    );
  };

  const dismissAlert = (alert: Alert) => {
    const key = `${alert.alert_type}-${alert.timestamp}`;
    setDismissedAlerts(prev => new Set([...prev, key]));
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    return date.toLocaleTimeString();
  };

  if (visibleAlerts.length === 0) {
    return (
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
              <Info className="w-6 h-6 text-green-400" />
            </div>
            <div className="text-gray-400 font-medium">No Active Alerts</div>
            <div className="text-sm text-gray-500 mt-1">Market conditions are normal</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-white">Structural Alerts</h3>
        <div className="text-sm text-gray-400">
          {visibleAlerts.length} Active
        </div>
      </div>

      <div className="space-y-3">
        {visibleAlerts.map((alert, index) => (
          <div
            key={`${alert.alert_type}-${alert.timestamp}`}
            className={`
              relative p-4 rounded-lg border transition-all duration-300
              ${getSeverityColor(alert.severity)}
              ${index === 0 ? 'animate-pulse' : ''} // Pulse newest alert
            `}
          >
            {/* Dismiss button */}
            <button
              onClick={() => dismissAlert(alert)}
              className="absolute top-2 right-2 p-1 hover:bg-white/10 rounded transition-colors"
            >
              <X className="w-3 h-3 text-gray-400" />
            </button>

            <div className="flex items-start space-x-3">
              {/* Alert Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {getSeverityIcon(alert.severity)}
              </div>

              {/* Alert Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  {getSeverityBadge(alert.severity)}
                  <div className="text-xs text-gray-400 uppercase tracking-wide">
                    {alert.alert_type.replace('_', ' ')}
                  </div>
                </div>
                
                <div className="text-sm text-white font-medium mb-2">
                  {alert.message}
                </div>
                
                <div className="text-xs text-gray-400">
                  {formatTimestamp(alert.timestamp)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Alert count indicator */}
      {alerts.length > maxVisible && (
        <div className="mt-4 text-center">
          <div className="text-sm text-gray-400">
            +{alerts.length - maxVisible} more alerts
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertPanel;
