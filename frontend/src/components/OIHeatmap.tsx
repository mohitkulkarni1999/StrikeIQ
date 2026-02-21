import { useState, useEffect, useRef } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import api from '../lib/api';

interface OIData {
  strike: number;
  oi: number;
  change: number;
  ltp: number;
  volume: number;
  iv: number;
  put_oi: number;
  put_change: number;
  put_ltp: number;
  put_volume: number;
  put_iv: number;
}

interface OIHeatmapProps {
  symbol: string;
  liveData?: any; // Live option chain data from useLiveMarketData
}

export default function OIHeatmap({ symbol, liveData }: OIHeatmapProps) {
  const [oiData, setOiData] = useState<OIData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [spotPrice, setSpotPrice] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const tableRef = useRef<HTMLDivElement>(null);
  const atmRowRef = useRef<HTMLTableRowElement>(null);
  const hasScrolledRef = useRef<boolean>(false);

  // DEBUG: Log props and structure
  console.log("OIHeatmap props:", { symbol, liveData });
  console.log("LIVE DATA STRUCTURE:", liveData ? Object.keys(liveData) : 'null');
  console.log("OPTION_CHAIN_SNAPSHOT:", liveData?.option_chain_snapshot);

  // Reset scroll flag when symbol changes
  useEffect(() => {
    hasScrolledRef.current = false;
  }, [symbol]);

  // Process live data from WebSocket (includes chain snapshot)
  useEffect(() => {
    if (liveData && liveData.calls && liveData.puts && Array.isArray(liveData.calls)) {
      console.log("PROCESSING CALLS ARRAY, length:", liveData.calls.length);
      console.log("FIRST CALL ROW:", liveData.calls[0]);
      console.log("FIRST PUT ROW:", liveData.puts[0]);
      
      // Use spot price from live data
      setSpotPrice(liveData.spot);

      // Transform calls/puts data for heatmap
      const transformedData = liveData.calls.map((call: any, index: number) => {
        const put = liveData.puts[index] || {};
        return {
          strike: call.strike,
          oi: call.oi || 0,
          change: 0, // Not available in snapshot
          ltp: call.ltp || 0,
          volume: 0, // Not available in snapshot
          iv: call.iv || 0,
          put_oi: put.oi || 0,
          put_change: 0,
          put_ltp: put.ltp || 0,
          put_volume: 0,
          put_iv: put.iv || 0,
        };
      });

      console.log("TRANSFORMED DATA:", transformedData[0]);
      setOiData(transformedData);
      setLoading(false);
      setError(null);
    } else {
      console.log("NO VALID CALLS/PUTS DATA");
      console.log("liveData exists:", !!liveData);
      console.log("calls exists:", !!liveData?.calls);
      console.log("puts exists:", !!liveData?.puts);
      console.log("calls is array:", Array.isArray(liveData?.calls));
    }
  }, [liveData]);

  if (loading && oiData.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    );
  }

  if (error && oiData.length === 0) {
    return (
      <div className="metric-card">
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <h3 className="text-xl font-semibold text-danger-500">Error</h3>
            <p className="text-muted-foreground">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 min-h-[600px]">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <h3 className="text-xl font-bold text-white">OI Heatmap</h3>
          {loading && (
            <div className="w-4 h-4 border-2 border-[#4F8CFF] border-t-transparent rounded-full animate-spin"></div>
          )}
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-xs font-bold uppercase">
            <div className="w-3 h-3 bg-[#FF4D4F]/40 border border-[#FF4D4F]/60 rounded"></div>
            <span className="text-gray-400">Calls</span>
          </div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase">
            <div className="w-3 h-3 bg-[#00FF9F]/40 border border-[#00FF9F]/60 rounded"></div>
            <span className="text-gray-400">Puts</span>
          </div>
        </div>
      </div>

      {/* Current Price Indicator */}
      {spotPrice && (
        <div className="mb-4 p-4 bg-black/20 rounded-xl border-l-4 border-l-[#00FF9F] border border-gray-800">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Current Spot Price</span>
            <div className="text-right">
              <span className="text-xl font-black text-[#00FF9F]">
                ₹{spotPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* OI Heatmap Table */}
      <div className="relative border border-white/10 rounded-lg overflow-hidden">
        {/* Fixed Header */}
        <div className="sticky top-0 z-20 bg-[#111827] border-b border-white/10">
          <table className="w-full table-fixed">
            <thead>
              <tr className="text-left text-xs text-muted-foreground uppercase tracking-wider font-bold">
                <th className="py-4 px-2 text-center w-[100px]">Call OI</th>
                <th className="py-4 px-2 text-center w-[80px]">Call Chg</th>
                <th className="py-4 px-2 text-center w-[100px]">Call LTP</th>
                <th className="py-4 px-2 text-center w-[90px] bg-white/5">Strike</th>
                <th className="py-4 px-2 text-center w-[100px]">Put LTP</th>
                <th className="py-4 px-2 text-center w-[80px]">Put Chg</th>
                <th className="py-4 px-2 text-center w-[100px]">Put OI</th>
              </tr>
            </thead>
          </table>
        </div>

        {/* Scrollable Body */}
        <div className="overflow-x-auto overflow-y-auto max-h-[500px] scrollbar-thin scrollbar-thumb-white/10" ref={tableRef}>
          <table className="w-full table-fixed">
            <tbody className="divide-y divide-white/5">
              {oiData.map((row) => {
                // Use backend ATM calculation instead of frontend derivation
                const isATM = liveData?.current_atm_strike && Math.abs(row.strike - liveData.current_atm_strike) <= 1;

                return (
                  <tr
                    key={row.strike}
                    ref={isATM ? atmRowRef : null}
                    className={`hover:bg-white/5 ${isATM ? 'bg-green-500/10' : ''}`}
                  >
                    {/* Call OI with heatmap */}
                    <td className="py-3 text-center w-[100px]">
                      <div
                        className="px-2 py-1 rounded text-xs font-bold text-white mx-1 overflow-hidden text-ellipsis whitespace-nowrap"
                        style={{ backgroundColor: 'rgba(239, 68, 68, 0.4)' }}
                      >
                        {row.oi.toLocaleString('en-IN')}
                      </div>
                    </td>

                    {/* Call Change */}
                    <td className="py-3 text-center w-[80px]">
                      <div className={`text-xs font-bold tabular-nums ${row.change > 0 ? 'text-success-500' : row.change < 0 ? 'text-danger-500' : 'text-gray-300'}`}>
                        {row.change > 0 ? '+' : ''}{row.change?.toLocaleString('en-IN')}
                      </div>
                    </td>

                    {/* Call LTP */}
                    <td className="py-3 text-center w-[100px] font-mono text-xs tabular-nums">
                      {row.ltp?.toLocaleString('en-IN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </td>

                    {/* Strike */}
                    <td className="py-3 px-2 text-center font-bold w-[90px] bg-white/5 relative">
                      <span className={isATM ? 'text-green-400' : 'text-gray-300'}>
                        {row.strike.toLocaleString('en-IN')}
                      </span>
                      {isATM && <div className="absolute left-0 top-0 bottom-0 w-1 bg-green-500"></div>}
                    </td>

                    {/* Put LTP */}
                    <td className="py-3 text-center w-[100px] font-mono text-xs tabular-nums">
                      {row.put_ltp?.toLocaleString('en-IN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                      })}
                    </td>

                    {/* Put Change */}
                    <td className="py-3 text-center w-[80px]">
                      <div className={`text-xs font-bold tabular-nums ${row.put_change > 0 ? 'text-success-500' : row.put_change < 0 ? 'text-danger-500' : 'text-gray-300'}`}>
                        {row.put_change > 0 ? '+' : ''}{row.put_change?.toLocaleString('en-IN')}
                      </div>
                    </td>

                    {/* Put OI with heatmap */}
                    <td className="py-3 text-center w-[100px]">
                      <div
                        className="px-2 py-1 rounded text-xs font-bold text-white mx-1 overflow-hidden text-ellipsis whitespace-nowrap"
                        style={{ backgroundColor: 'rgba(34, 197, 94, 0.4)' }}
                      >
                        {row.put_oi.toLocaleString('en-IN')}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-white/10">
        <div className="font-medium mb-2">Interpretation:</div>
        <div className="text-sm text-muted-foreground space-y-1">
          <div>• 📍 Green highlight indicates ATM (At-The-Money) strike</div>
          <div>• Darker colors indicate higher Open Interest</div>
          <div>• Color coded changes show OI addition (+) or reduction (-)</div>
        </div>
      </div>
    </div>
  );
}
