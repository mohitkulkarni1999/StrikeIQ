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

  // Add custom animation styles
  React.useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes critical-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
      }
      .critical-alert {
        animation: critical-pulse 1.5s ease-in-out infinite;
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

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
        return 'bg-red-500/10 border-red-500/30 text-red-400 border-l-4 border-l-red-500';
      case 'high':
        return 'bg-orange-500/10 border-orange-500/30 text-orange-400 border-l-4 border-l-orange-500';
      case 'medium':
        return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400 border-l-4 border-l-yellow-500';
      case 'low':
        return 'bg-blue-500/10 border-blue-500/30 text-blue-400 border-l-4 border-l-blue-500';
      default:
        return 'bg-gray-500/10 border-gray-500/30 text-gray-400 border-l-4 border-l-gray-500';
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
      critical: 'bg-red-500/20 text-red-300 border border-red-500/30',
      high: 'bg-orange-500/20 text-orange-300 border border-orange-500/30',
      medium: 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30',
      low: 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
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
      <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-xl p-3 shadow-lg">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
          <div className="text-sm text-gray-400">No Active Alerts</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-2xl p-6 shadow-lg">
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
              ${alert.severity === 'critical' ? 'critical-alert' : ''} // Custom pulse for critical alerts
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
