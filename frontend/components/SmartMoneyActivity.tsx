import { RealTimeSignals } from '../types/market';
import { TrendingUp, TrendingDown, AlertTriangle, Activity, Eye } from 'lucide-react';

interface SmartMoneyActivityProps {
  signals: RealTimeSignals;
}

export default function SmartMoneyActivity({ signals }: SmartMoneyActivityProps) {
  if (!signals) {
    return (
      <div className="glass-morphism rounded-xl p-6 border border-dashed border-white/20">
        <div className="text-center">
          <Eye className="w-12 h-12 text-muted-foreground/50 mx-auto mb-4" />
          <h4 className="text-lg font-semibold text-white mb-2">Smart Money Monitoring</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Smart money signals will appear when sufficient institutional activity is detected in the options chain.
          </p>
          <div className="mt-4 pt-4 border-t border-white/10">
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
              <Activity className="w-3 h-3" />
              <span>Waiting for significant block trades</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { smart_money_signal } = signals;
  const signal = smart_money_signal.signal;
  const action = smart_money_signal.action;
  const activities = smart_money_signal.activities || [];

  const getSignalColor = (signal: string) => {
    if (signal.includes('BULLISH')) return 'text-success-500';
    if (signal.includes('BEARISH')) return 'text-danger-500';
    return 'text-warning-500';
  };

  const getSignalBgColor = (signal: string) => {
    if (signal.includes('BULLISH')) return 'bg-success-500/20 border-success-500/30';
    if (signal.includes('BEARISH')) return 'bg-danger-500/20 border-danger-500/30';
    return 'bg-warning-500/20 border-warning-500/30';
  };

  const getActivityIcon = (activity: string) => {
    if (activity.includes('BULLISH')) return <TrendingUp className="w-4 h-4" />;
    if (activity.includes('BEARISH')) return <TrendingDown className="w-4 h-4" />;
    if (activity.includes('TRAP')) return <AlertTriangle className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  const getActivityColor = (activity: string) => {
    if (activity.includes('BULLISH')) return 'text-success-500 bg-success-500/20';
    if (activity.includes('BEARISH')) return 'text-danger-500 bg-danger-500/20';
    if (activity.includes('TRAP')) return 'text-warning-500 bg-warning-500/20';
    return 'text-muted-foreground bg-muted';
  };

  return (
    <div className="metric-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold">Smart Money Activity</h3>
        <div className={`px-3 py-1 rounded-full border ${getSignalBgColor(signal)}`}>
          <span className={`text-sm font-medium ${getSignalColor(signal)}`}>
            {signal.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Main Signal Display */}
      <div className={`glass-morphism rounded-lg p-4 mb-6 border ${getSignalBgColor(signal)}`}>
        <div className="flex items-center justify-between">
          <div>
            <div className={`text-lg font-semibold ${getSignalColor(signal)}`}>
              {signal.replace('_', ' ')}
            </div>
            <div className="text-sm text-muted-foreground">
              Recommended Action: <span className="font-medium">{action}</span>
            </div>
          </div>
          <div className={`p-3 rounded-lg ${getSignalBgColor(signal)}`}>
            <div className={getSignalColor(signal)}>
              {getActivityIcon(signal)}
            </div>
          </div>
        </div>
      </div>

      {/* Activity Breakdown */}
      {activities.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-muted-foreground">Detected Activities</h4>
          <div className="space-y-2">
            {activities.map((activity, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-2 rounded-lg glass-morphism"
              >
                <div className={`p-1.5 rounded ${getActivityColor(activity)}`}>
                  {getActivityIcon(activity)}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium">
                    {activity.replace('_', ' ')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Smart Money Indicators */}
      <div className="mt-6 pt-6 border-t border-white/10">
        <h4 className="text-sm font-medium text-muted-foreground mb-3">Activity Indicators</h4>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 glass-morphism rounded-lg">
            <div className="text-2xl font-bold text-success-500">
              {activities.filter(a => a.includes('BULLISH')).length}
            </div>
            <div className="text-xs text-muted-foreground">Bullish Signals</div>
          </div>
          <div className="text-center p-3 glass-morphism rounded-lg">
            <div className="text-2xl font-bold text-danger-500">
              {activities.filter(a => a.includes('BEARISH')).length}
            </div>
            <div className="text-xs text-muted-foreground">Bearish Signals</div>
          </div>
        </div>
      </div>

      {/* Interpretation */}
      <div className="mt-4 p-3 glass-morphism rounded-lg">
        <div className="text-xs text-muted-foreground">
          <div className="font-medium mb-1">Smart Money Interpretation:</div>
          {signal.includes('BULLISH') && (
            <div>Institutional activity suggests bullish bias with potential upside momentum.</div>
          )}
          {signal.includes('BEARISH') && (
            <div>Institutional activity suggests bearish bias with potential downside pressure.</div>
          )}
          {signal.includes('MIXED') && (
            <div>Conflicting institutional signals detected - wait for clearer confirmation.</div>
          )}
          {signal.includes('NO_ACTIVITY') && (
            <div>Minimal institutional activity detected - market may be in consolidation phase.</div>
          )}
        </div>
      </div>
    </div>
  );
}
