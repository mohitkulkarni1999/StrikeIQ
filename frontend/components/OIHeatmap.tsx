import { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';

interface OIHeatmapProps {
  symbol: string;
}

interface OIData {
  strike: number;
  call_oi: number;
  put_oi: number;
  call_change: number;
  put_change: number;
  call_ltp: number;
  put_ltp: number;
}

export default function OIHeatmap({ symbol }: OIHeatmapProps) {
  const [oiData, setOiData] = useState<OIData[]>([]);
  const [loading, setLoading] = useState(true);
  const [spotPrice, setSpotPrice] = useState(19500);

  useEffect(() => {
    // Mock OI data - in real implementation, this would come from API
    const mockOIData: OIData[] = [
      { strike: 19000, call_oi: 125000, put_oi: 450000, call_change: -15000, put_change: 25000, call_ltp: 520, put_ltp: 15 },
      { strike: 19100, call_oi: 180000, put_oi: 380000, call_change: -20000, put_change: 18000, call_ltp: 450, put_ltp: 22 },
      { strike: 19200, call_oi: 250000, put_oi: 320000, call_change: -25000, put_change: 15000, call_ltp: 380, put_ltp: 35 },
      { strike: 19300, call_oi: 320000, put_oi: 280000, call_change: -30000, put_change: 12000, call_ltp: 320, put_ltp: 52 },
      { strike: 19400, call_oi: 450000, put_oi: 250000, call_change: -35000, put_change: 10000, call_ltp: 260, put_ltp: 75 },
      { strike: 19500, call_oi: 580000, put_oi: 520000, call_change: -40000, put_change: 8000, call_ltp: 210, put_ltp: 110 },
      { strike: 19600, call_oi: 520000, put_oi: 380000, call_change: 15000, put_change: -12000, call_ltp: 165, put_ltp: 155 },
      { strike: 19700, call_oi: 450000, put_oi: 320000, call_change: 20000, put_change: -15000, call_ltp: 125, put_ltp: 210 },
      { strike: 19800, call_oi: 380000, put_oi: 280000, call_change: 25000, put_change: -18000, call_ltp: 95, put_ltp: 275 },
      { strike: 19900, call_oi: 320000, put_oi: 250000, call_change: 18000, put_change: -12000, call_ltp: 70, put_ltp: 350 },
      { strike: 20000, call_oi: 280000, put_oi: 220000, call_change: 12000, put_change: -10000, call_ltp: 52, put_ltp: 425 },
    ];

    setTimeout(() => {
      setOiData(mockOIData);
      setLoading(false);
    }, 1000);
  }, [symbol]);

  const getOIIntensity = (oi: number) => {
    const maxOI = Math.max(...oiData.map(d => Math.max(d.call_oi, d.put_oi)));
    return (oi / maxOI) * 100;
  };

  const getChangeColor = (change: number) => {
    if (change > 0) return 'text-success-500';
    if (change < 0) return 'text-danger-500';
    return 'text-muted-foreground';
  };

  const getChangeBgColor = (change: number) => {
    if (change > 0) return 'bg-success-500/20';
    if (change < 0) return 'bg-danger-500/20';
    return 'bg-muted';
  };

  const getHeatmapColor = (oi: number, isCall: boolean) => {
    const intensity = getOIIntensity(oi);
    if (isCall) {
      return `rgba(239, 68, 68, ${intensity / 100})`; // Red for calls
    } else {
      return `rgba(34, 197, 94, ${intensity / 100})`; // Green for puts
    }
  };

  if (loading) {
    return (
      <div className="metric-card">
        <div className="flex items-center justify-center h-96">
          <div className="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="metric-card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold">OI Heatmap - {symbol}</h3>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-danger-500 rounded"></div>
            <span className="text-muted-foreground">Call OI</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <div className="w-3 h-3 bg-success-500 rounded"></div>
            <span className="text-muted-foreground">Put OI</span>
          </div>
        </div>
      </div>

      {/* Current Price Indicator */}
      <div className="mb-4 p-3 glass-morphism rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Current Price</span>
          <span className="text-lg font-bold">₹{spotPrice.toLocaleString('en-IN')}</span>
        </div>
      </div>

      {/* OI Heatmap Table */}
      <div className="overflow-x-auto overflow-y-auto max-h-96">
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-muted-foreground border-b border-white/10">
              <th className="pb-3">Strike</th>
              <th className="pb-3 text-center">Call OI</th>
              <th className="pb-3 text-center">Call Chg</th>
              <th className="pb-3 text-center">Call LTP</th>
              <th className="pb-3 text-center">Put LTP</th>
              <th className="pb-3 text-center">Put Chg</th>
              <th className="pb-3 text-center">Put OI</th>
            </tr>
          </thead>
          <tbody>
            {oiData.map((row, index) => (
              <tr 
                key={row.strike} 
                className={`border-b border-white/5 hover:bg-white/5 transition-colors ${
                  row.strike === spotPrice ? 'bg-primary-500/10' : ''
                }`}
              >
                <td className={`py-3 font-medium ${
                  row.strike === spotPrice ? 'text-primary-500' : ''
                }`}>
                  {row.strike.toLocaleString('en-IN')}
                </td>
                
                {/* Call OI with heatmap */}
                <td className="py-3 text-center">
                  <div 
                    className="px-2 py-1 rounded text-xs font-medium text-white oi-heatmap-cell"
                    style={{ backgroundColor: getHeatmapColor(row.call_oi, true) }}
                  >
                    {(row.call_oi / 1000).toFixed(0)}K
                  </div>
                </td>
                
                {/* Call Change */}
                <td className="py-3 text-center">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getChangeBgColor(row.call_change)} ${getChangeColor(row.call_change)}`}>
                    {row.call_change > 0 ? '+' : ''}{(row.call_change / 1000).toFixed(0)}K
                  </div>
                </td>
                
                {/* Call LTP */}
                <td className="py-3 text-center text-sm">
                  ₹{row.call_ltp}
                </td>
                
                {/* Put LTP */}
                <td className="py-3 text-center text-sm">
                  ₹{row.put_ltp}
                </td>
                
                {/* Put Change */}
                <td className="py-3 text-center">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getChangeBgColor(row.put_change)} ${getChangeColor(row.put_change)}`}>
                    {row.put_change > 0 ? '+' : ''}{(row.put_change / 1000).toFixed(0)}K
                  </div>
                </td>
                
                {/* Put OI with heatmap */}
                <td className="py-3 text-center">
                  <div 
                    className="px-2 py-1 rounded text-xs font-medium text-white oi-heatmap-cell"
                    style={{ backgroundColor: getHeatmapColor(row.put_oi, false) }}
                  >
                    {(row.put_oi / 1000).toFixed(0)}K
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* OI Analysis Summary */}
      <div className="mt-6 pt-6 border-t border-white/10">
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-lg font-bold text-danger-500">
              {(oiData.reduce((sum, row) => sum + row.call_oi, 0) / 1000000).toFixed(2)} Cr
            </div>
            <div className="text-xs text-muted-foreground">Total Call OI</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-success-500">
              {(oiData.reduce((sum, row) => sum + row.put_oi, 0) / 1000000).toFixed(2)} Cr
            </div>
            <div className="text-xs text-muted-foreground">Total Put OI</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-primary-500">
              {(oiData.reduce((sum, row) => sum + row.put_oi, 0) / 
                oiData.reduce((sum, row) => sum + row.call_oi, 0)).toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground">Put-Call Ratio</div>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-white/10">
        <div className="text-xs text-muted-foreground">
          <div className="font-medium mb-2">Interpretation:</div>
          <div>• Darker colors indicate higher Open Interest</div>
          <div>• Green changes show OI addition, Red shows OI reduction</div>
          <div>• High Call OI at strikes above spot = Resistance</div>
          <div>• High Put OI at strikes below spot = Support</div>
        </div>
      </div>
    </div>
  );
}
