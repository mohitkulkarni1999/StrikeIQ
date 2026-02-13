import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface ExpiryDate {
  date: string;
  label: string;
  isCurrent: boolean;
}

interface OIData {
  strike: number;
  oi: number;
  change: number;
  ltp: number;
  put_ltp: number;
  put_change: number;
  put_oi: number;
}

interface OIHeatmapProps {
  symbol: string;
}

export default function OIHeatmap({ symbol }: OIHeatmapProps) {
  const [availableExpiries, setAvailableExpiries] = useState<ExpiryDate[]>([]);
  const [selectedExpiry, setSelectedExpiry] = useState<string>('');
  const [expiryLoading, setExpiryLoading] = useState<boolean>(false);
  const [oiData, setOiData] = useState<OIData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [spotPrice, setSpotPrice] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Format expiry date for display
  const formatExpiryDate = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    
    // Calculate days until expiry
    const daysUntilExpiry = Math.ceil((date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (daysUntilExpiry === 1) {
      return 'Tomorrow';
    } else if (daysUntilExpiry > 1 && daysUntilExpiry <= 7) {
      // Show "X days" for expiries within a week
      return `${daysUntilExpiry} days`;
    } else if (daysUntilExpiry > 7 && daysUntilExpiry <= 14) {
      // Show "X weeks" for expiries between 7-14 days
      const weeks = Math.floor(daysUntilExpiry / 7);
      return `${weeks} weeks`;
    } else {
      // Show formatted date for longer expiries
      return date.toLocaleDateString('en-IN', { 
        day: 'numeric', 
        month: 'short', 
        year: '2-digit' 
      });
    }
  };

  // Fetch available expiry dates
  const fetchAvailableExpiries = async () => {
    try {
      setExpiryLoading(true);
      const response = await axios.get(`http://localhost:8000/api/v1/options/contract/${symbol}`);
      
      console.log('Expiry response:', response.data); // Debug log
      
      // Handle different response formats
      let expiryDates: string[] = [];
      if (response.data && response.data.data && Array.isArray(response.data.data)) {
        expiryDates = response.data.data;
      } else if (response.data && Array.isArray(response.data)) {
        expiryDates = response.data;
      } else {
        console.error('Unexpected response format:', response.data);
      }
      
      const expiries: ExpiryDate[] = expiryDates.map((date: string) => {
        const expiryDate = new Date(date);
        const today = new Date();
        
        // Calculate if this is the current/near expiry
        const daysUntilExpiry = Math.ceil((expiryDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
        const isCurrent = daysUntilExpiry >= 0 && daysUntilExpiry <= 7; // Within next week
        
        return {
          date,
          label: formatExpiryDate(date),
          isCurrent
        };
      });
      
      setAvailableExpiries(expiries);
      
      // Auto-select nearest expiry if none selected
      if (!selectedExpiry && expiries.length > 0) {
        // Prioritize current expiries (within next week)
        const currentExpiry = expiries.find(e => e.isCurrent);
        const nearestExpiry = currentExpiry || expiries[0];
        console.log('Auto-selecting expiry:', nearestExpiry.date, nearestExpiry.label);
        setSelectedExpiry(nearestExpiry.date);
      }
      
      console.log('Available expiries:', expiries); // Debug log
      console.log('Selected expiry:', selectedExpiry); // Debug log
      
    } catch (err) {
      console.error('Error fetching expiries:', err);
      setError('Failed to fetch expiry dates');
    } finally {
      setExpiryLoading(false);
    }
  };

  // Handle expiry selection
  const handleExpiryChange = (expiry: string) => {
    setSelectedExpiry(expiry);
  };

  // Fetch expiries on component mount
  useEffect(() => {
    fetchAvailableExpiries();
  }, [symbol]);

  // Fetch option chain data
  useEffect(() => {
    // Only fetch if we have a selected expiry
    if (selectedExpiry) {
      const fetchOptionChain = async () => {
        try {
          setLoading(true);
          setError(null);
          
          console.log("Fetching option chain with expiry:", selectedExpiry);
          const response = await axios.get(
            `http://localhost:8000/api/v1/options/chain/${symbol}?expiry_date=${selectedExpiry}`
          );
        
          console.log("BACKEND OPTION CHAIN:", response.data);
          console.log("FULL RESPONSE STRUCTURE:", JSON.stringify(response.data, null, 2));
          
          const chain = response.data;
          
          // Backend returns: {status: "success", data: {symbol, expiry, calls, puts}}
          const calls = chain?.data?.calls || [];
          const puts = chain?.data?.puts || [];
          
          console.log("=== DEBUG: First 3 calls ===");
          console.table(calls?.slice(0, 3));
          console.log("=== DEBUG: First 3 puts ===");
          console.table(puts?.slice(0, 3));
          console.log("=== DEBUG: Expected data path: chain.data.calls ===");
          console.log("=== DEBUG: Actual calls path:", chain?.data?.calls);
          console.log("=== DEBUG: Backend 25600 strike data:", calls.find(c => c.strike === 25600));
          console.log("=== DEBUG: Backend 25600 OI:", calls.find(c => c.strike === 25600)?.oi);
        
          const transformedData = calls.map((call: any) => {
            const matchingPut = puts.find(
              (p: any) => p.strike === call.strike
            );
        
            return {
              strike: call.strike,
              oi: call.oi || 0,
              change: call.change || 0,
              ltp: call.ltp || 0,
              put_ltp: matchingPut?.ltp || 0,
              put_change: matchingPut?.change || 0,
              put_oi: matchingPut?.oi || 0,
            };
          });
        
          setOiData(transformedData);
        
        } catch (err: any) {
          console.error("AXIOS ERROR FULL:", err);
          if (err.response) {
            console.error("Response data:", err.response.data);
            console.error("Response status:", err.response.status);
          }
          setError('Failed to fetch option chain data');
        } finally {
          setLoading(false);
        }
      };

      fetchOptionChain();
    }
  }, [symbol, selectedExpiry]);

  if (loading) {
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

  if (error) {
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
    <div className="space-y-4">
      {/* Header */}
      <div className="mb-4 p-3 glass-morphism rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gradient mb-2">StrikeIQ</h1>
            <p className="text-muted-foreground">AI-Powered Options Market Intelligence</p>
          </div>
          <div className="flex items-center gap-4">
            <select 
              value={symbol}
              onChange={(e) => setSelectedExpiry('')}
              className="glass-morphism px-4 py-2 rounded-lg border border-white/10 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="NIFTY" selected="">NIFTY</option>
              <option value="BANKNIFTY">BANKNIFTY</option>
            </select>
            <div className="flex items-center gap-2">
              <div className="status-indicator status-offline"></div>
              <span className="text-sm text-muted-foreground">Loading</span>
            </div>
          </div>
        </div>
      </div>

      {/* Expiry Selector */}
      <div className="mb-4 p-3 glass-morphism rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold mb-2">Option Chain</h2>
            <p className="text-sm text-muted-foreground">Select expiry date</p>
          </div>
          <div className="flex items-center gap-2">
            {expiryLoading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm text-blue-500">Loading expiries...</span>
              </div>
            ) : availableExpiries.length > 0 ? (
              <div className="flex items-center gap-2">
                <select
                  value={selectedExpiry}
                  onChange={(e) => handleExpiryChange(e.target.value)}
                  className="bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-32"
                  disabled={loading}
                >
                  {availableExpiries.map((expiry) => (
                    <option key={expiry.date} value={expiry.date}>
                      {expiry.label} {expiry.isCurrent && '(Current)'}
                    </option>
                  ))}
                </select>
                {selectedExpiry && (
                  <span className="text-xs text-muted-foreground">
                    {formatExpiryDate(selectedExpiry)}
                  </span>
                )}
              </div>
            ) : (
              <span className="text-sm text-muted-foreground">No expiries available</span>
            )}
          </div>
        </div>
      </div>

      {/* Current Price Indicator */}
      <div className="mb-4 p-3 glass-morphism rounded-lg">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Current Price</span>
          <span className="text-lg font-bold">
            {spotPrice ? `₹${spotPrice.toLocaleString('en-IN')}` : '₹--'}
          </span>
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
            {console.log("=== DEBUG: About to render oiData with", oiData?.length, "rows")}
            {oiData.map((row, index) => {
              if (index < 3) {
                console.log(`=== DEBUG: Row ${index} strike=${row.strike} oi=${row.oi} ltp=${row.ltp}`);
              }
              return (
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
                      style={{ backgroundColor: 'rgba(239, 68, 68, 0.5)' }}
                    >
                      {row.oi.toLocaleString('en-IN')}
                    </div>
                  </td>
                  
                  {/* Call Change */}
                  <td className="py-3 text-center">
                    <div className={`px-2 py-1 rounded text-xs font-medium ${
                      row.change > 0 ? 'bg-success-500/20 text-success-500' :
                      row.change < 0 ? 'bg-danger-500/20 text-danger-500' :
                      'bg-gray-500/20 text-gray-300'
                    }`}>
                      {row.change?.toLocaleString('en-IN')}
                    </div>
                  </td>
                  
                  {/* Call LTP */}
                  <td className="py-3 text-center text-sm">
                    {row.ltp?.toLocaleString('en-IN', {
                      style: 'currency',
                      currency: 'INR'
                    })}
                  </td>
                  
                  {/* Put LTP */}
                  <td className="py-3 text-center text-sm">
                    {row.put_ltp?.toLocaleString('en-IN', {
                      style: 'currency',
                      currency: 'INR'
                    })}
                  </td>
                  
                  {/* Put Change */}
                  <td className="py-3 text-center">
                    <div className={`px-2 py-1 rounded text-xs font-medium ${
                      row.put_change > 0 ? 'bg-success-500/20 text-success-500' :
                      row.put_change < 0 ? 'bg-danger-500/20 text-danger-500' :
                      'bg-gray-500/20 text-gray-300'
                    }`}>
                      {row.put_change?.toLocaleString('en-IN')}
                    </div>
                  </td>
                  
                  {/* Put OI with heatmap */}
                  <td className="py-3 text-center">
                    <div 
                      className="px-2 py-1 rounded text-xs font-medium text-white oi-heatmap-cell"
                      style={{ backgroundColor: 'rgba(239, 68, 68, 0.5)' }}
                    >
                      {row.put_oi?.toLocaleString('en-IN')}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
