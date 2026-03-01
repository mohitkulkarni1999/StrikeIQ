import { useState, useEffect, useRef, useCallback } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Calendar } from 'lucide-react';
import api from '../lib/api';
import { useWSStore } from '../core/ws/wsStore';
import { useDashboardData } from '../hooks/useDashboardData';

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
}

const OIHeatmap: React.FC<OIHeatmapProps> = ({ symbol }) => {
  
  // Use global store data
  const { calls, puts, connected } = useDashboardData();

  const [oiData, setOiData] = useState<OIData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [spotPrice, setSpotPrice] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Read from Zustand store for fallback
  const { liveData: wsLiveData, optionChainSnapshot, spot } = useWSStore();
  
  // Use structured data from global store, fallback to legacy data
  const actualLiveData = calls.length > 0 || puts.length > 0 
    ? { calls, puts, spot }
    : wsLiveData || optionChainSnapshot;

  // 🔥 PCR FALLBACK CALCULATION (FRONTEND-ONLY FIX)
  const calculatePCR = useCallback((data: any) => {
    if (!data || !data.calls || !data.puts) return 0;
    
    const totalCallOI = data.calls.reduce((sum: number, call: any) => 
      sum + (call.open_interest || call.oi || 0), 0);
    const totalPutOI = data.puts.reduce((sum: number, put: any) => 
      sum + (put.open_interest || put.oi || 0), 0);
    
    return totalCallOI > 0 ? totalPutOI / totalCallOI : 0;
  }, [actualLiveData]);

  // Use backend PCR if valid, otherwise fallback to calculated PCR
  const pcr = actualLiveData?.pcr && actualLiveData.pcr > 0
    ? actualLiveData.pcr
    : calculatePCR(actualLiveData);

  // 🔥 PCR DEBUG LOGGING
  console.log("🔥 PCR ANALYSIS:", {
    backendPCR: actualLiveData?.pcr,
    calculatedPCR: calculatePCR(actualLiveData),
    effectivePCR: pcr,
    hasValidCalls: !!(actualLiveData?.calls?.length),
    hasValidPuts: !!(actualLiveData?.puts?.length),
    totalCallOI: actualLiveData?.calls?.reduce((s: number, c: any) => s + (c.open_interest || c.oi || 0), 0),
    totalPutOI: actualLiveData?.puts?.reduce((s: number, p: any) => s + (p.open_interest || p.oi || 0), 0)
  });

  const tableRef = useRef<HTMLDivElement>(null);
  const atmRowRef = useRef<HTMLTableRowElement>(null);
  const hasScrolledRef = useRef<boolean>(false);

  // DEBUG: Log props and structure
  console.log("OIHeatmap props:", { symbol });
  console.log("WS LIVE DATA FROM STORE:", wsLiveData);
  console.log("OPTION_CHAIN_SNAPSHOT FROM STORE:", optionChainSnapshot);
  console.log("ACTUAL LIVE DATA:", actualLiveData);
  console.log("LIVE DATA STRUCTURE:", actualLiveData ? Object.keys(actualLiveData) : 'null');

  // Reset scroll flag when symbol changes
  useEffect(() => {
    hasScrolledRef.current = false;
  }, [symbol]);

  // Process live data from WebSocket (includes chain snapshot)
  useEffect(() => {
    if (actualLiveData && "calls" in actualLiveData && "puts" in actualLiveData && Array.isArray(actualLiveData.calls)) {
      // Add console.log for WS payload verification
      console.log("🔥 WS PAYLOAD VERIFICATION:", actualLiveData);
      console.log("CALLS ARRAY:", actualLiveData.calls);
      console.log("PUTS ARRAY:", actualLiveData.puts);
      console.log("SPOT PRICE:", actualLiveData.spot_price);
      console.log("ATM STRIKE:", actualLiveData.atm_strike);
      console.log("TIMESTAMP:", actualLiveData._ts);
      
      // Use spot price from live data (new field name)
      setSpotPrice(actualLiveData.spot_price);

      // Build unified strike map by merging calls and puts
      const strikeMap: { [key: number]: { call_oi: number; put_oi: number; call_ltp: number; put_ltp: number; call_volume: number; put_volume: number } } = {};
      
      // Process calls
      actualLiveData.calls.forEach((call: any) => {
        strikeMap[call.strike] = {
          call_oi: call.oi || 0,
          put_oi: 0,
          call_ltp: call.ltp || 0,
          put_ltp: 0,
          call_volume: call.volume || 0,
          put_volume: 0
        };
      });
      
      // Process puts and merge with existing strikes
      actualLiveData.puts.forEach((put: any) => {
        if (strikeMap[put.strike]) {
          // Merge with existing call data
          strikeMap[put.strike].put_oi = put.oi || 0;
          strikeMap[put.strike].put_ltp = put.ltp || 0;
          strikeMap[put.strike].put_volume = put.volume || 0;
        } else {
          // Add new put-only strike
          strikeMap[put.strike] = {
            call_oi: 0,
            put_oi: put.oi || 0,
            call_ltp: 0,
            put_ltp: put.ltp || 0,
            call_volume: 0,
            put_volume: put.volume || 0
          };
        }
      });

      // Convert strike map to array format for rendering
      const transformedData = Object.entries(strikeMap).map(([strike, data]) => ({
        strike: parseInt(strike),
        oi: data.call_oi,
        change: 0, // Not available in snapshot
        ltp: data.call_ltp,
        volume: data.call_volume,
        iv: 0, // Not available in snapshot
        put_oi: data.put_oi,
        put_change: 0,
        put_ltp: data.put_ltp,
        put_volume: data.put_volume,
        put_iv: 0,
      }));

      // Sort by strike for proper ordering
      transformedData.sort((a, b) => a.strike - b.strike);

      // Filter to ATM window (±500 strikes) - DO NOT filter by OI
      const filteredData = transformedData.filter(row => {
        const diff = Math.abs(row.strike - actualLiveData.atm_strike);
        return diff <= 500;   // keep ±500 window
      });

      console.log("UNIFIED STRIKE MAP:", strikeMap);
      console.log("TOTAL STRIKES:", transformedData.length, "→ FILTERED TO:", filteredData.length);
      console.log("SETTING OI DATA WITH:", filteredData.length, "ROWS");
      console.log("SAMPLE DATA:", filteredData.slice(0, 3));
      setOiData(filteredData);
      setLoading(false);
      setError(null);
    } else {
      console.log("NO VALID CALLS/PUTS DATA");
      console.log("actualLiveData exists:", !!actualLiveData);
      console.log("calls exists:", !!actualLiveData?.calls);
      console.log("puts exists:", !!actualLiveData?.puts);
      console.log("calls is array:", Array.isArray(actualLiveData?.calls));
    }
  }, [actualLiveData]);

  // Debug render logging
  useEffect(() => {
    console.log("🎯 RENDERING OI DATA:", oiData.length, "ROWS");
  }, [oiData]);

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
    <div className="heatmap-container" style={{
      display: 'flex',
      overflowX: 'auto',
      gap: '8px',
      width: '100%'
    }}>
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 min-h-[600px]" style={{ minWidth: '100%' }}>
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
                  <th className="py-4 px-2 text-center" style={{ minWidth: '80px' }}>Call OI</th>
                  <th className="py-4 px-2 text-center" style={{ minWidth: '80px' }}>Call Chg</th>
                  <th className="py-4 px-2 text-center" style={{ minWidth: '80px' }}>Call LTP</th>
                  <th className="py-4 px-2 text-center bg-white/5" style={{ minWidth: '80px' }}>Strike</th>
                  <th className="py-4 px-2 text-center" style={{ minWidth: '80px' }}>Put LTP</th>
                  <th className="py-4 px-2 text-center" style={{ minWidth: '80px' }}>Put Chg</th>
                  <th className="py-4 px-2 text-center" style={{ minWidth: '80px' }}>Put OI</th>
                </tr>
              </thead>
            </table>
          </div>

          {/* Scrollable Body */}
          <div className="overflow-x-auto overflow-y-auto max-h-[500px] scrollbar-thin scrollbar-thumb-white/10" ref={tableRef}>
            <table className="w-full table-auto">
              <tbody className="divide-y divide-white/5">
                {oiData.map((row) => {
                  // Use backend ATM calculation instead of frontend derivation
                  const isATM = actualLiveData?.atm_strike && Math.abs(row.strike - actualLiveData.atm_strike) <= 1;

                  return (
                    <tr
                      key={row.strike}
                      ref={isATM ? atmRowRef : null}
                      className={`hover:bg-white/5 ${isATM ? 'bg-green-500/10' : ''}`}
                    >
                      {/* Call OI with heatmap */}
                      <td className="py-3 text-center" style={{ minWidth: '80px' }}>
                        <div
                          className="px-2 py-1 rounded text-xs font-bold text-white mx-1 overflow-hidden text-ellipsis whitespace-nowrap"
                          style={{ backgroundColor: 'rgba(239, 68, 68, 0.4)' }}
                        >
                          {row.oi.toLocaleString('en-IN')}
                        </div>
                      </td>

                      {/* Call Change */}
                      <td className="py-3 text-center" style={{ minWidth: '80px' }}>
                        <div className={`text-xs font-bold tabular-nums ${row.change > 0 ? 'text-success-500' : row.change < 0 ? 'text-danger-500' : 'text-gray-300'}`}>
                          {row.change > 0 ? '+' : ''}{row.change?.toLocaleString('en-IN')}
                        </div>
                      </td>

                      {/* Call LTP */}
                      <td className="py-3 text-center font-mono text-xs tabular-nums" style={{ minWidth: '80px' }}>
                        {row.ltp?.toLocaleString('en-IN', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })}
                      </td>

                      {/* Strike */}
                      <td className="py-3 px-2 text-center font-bold bg-white/5 relative" style={{ minWidth: '80px' }}>
                        <span className={isATM ? 'text-green-400' : 'text-gray-300'}>
                          {row.strike.toLocaleString('en-IN')}
                        </span>
                        {isATM && <div className="absolute left-0 top-0 bottom-0 w-1 bg-green-500"></div>}
                      </td>

                      {/* Put LTP */}
                      <td className="py-3 text-center font-mono text-xs tabular-nums" style={{ minWidth: '80px' }}>
                        {row.put_ltp?.toLocaleString('en-IN', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2
                        })}
                      </td>

                      {/* Put Change */}
                      <td className="py-3 text-center" style={{ minWidth: '80px' }}>
                        <div className={`text-xs font-bold tabular-nums ${row.put_change > 0 ? 'text-success-500' : row.put_change < 0 ? 'text-danger-500' : 'text-gray-300'}`}>
                          {row.put_change > 0 ? '+' : ''}{row.put_change?.toLocaleString('en-IN')}
                        </div>
                      </td>

                      {/* Put OI with heatmap */}
                      <td className="py-3 text-center" style={{ minWidth: '80px' }}>
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
    </div>
  );
};

export default OIHeatmap;
