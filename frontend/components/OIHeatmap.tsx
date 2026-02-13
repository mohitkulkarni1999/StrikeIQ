import React, { useState, useEffect, useMemo } from 'react';
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
  isATM?: boolean;
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

  // Fetch spot price from dashboard API
  const fetchSpotPrice = async () => {
    try {
      console.log(`=== DEBUG: Fetching spot price from dashboard API for ${symbol} ===`);
      const response = await axios.get(`http://localhost:8000/api/dashboard/${symbol}`);
      console.log("=== DEBUG: Dashboard response:", response.data);
      
      // Extract spot price from dashboard response
      const dashboardData = response.data;
      const price = dashboardData?.data?.spot_price || dashboardData?.spot_price || null;
      
      console.log("=== DEBUG: Extracted spot price:", price);
      setSpotPrice(price);
      
    } catch (err: any) {
      console.error("=== DEBUG: Error fetching spot price:", err);
      // Don't set error for spot price failure, just log it
    }
  };

  // Fetch available expiry dates
  const fetchAvailableExpiries = async () => {
    try {
      setExpiryLoading(true);
      console.log(`🔍 Fetching contracts for ${symbol}...`);
      console.log(`🔍 Full API URL: http://localhost:8000/api/v1/options/contract/${symbol}`);
      const response = await axios.get(`http://localhost:8000/api/v1/options/contract/${symbol}`);
      
      console.log('📊 Expiry response:', response.data);
      console.log('📊 Response status:', response.status);
      console.log('📊 Response type:', typeof response.data);
      
      // Check if response is AUTH_REQUIRED
      if (response.data && response.data.session_type === 'AUTH_REQUIRED') {
        console.log('🚫 AUTH_REQUIRED received for contracts - authentication needed');
        setError('Authentication required to fetch option contracts');
        setAvailableExpiries([]);
        return;
      }
      
      // Handle successful response with real data
      let expiryDates: string[] = [];
      if (response.data && response.data.status === 'success' && response.data.data) {
        expiryDates = response.data.data;
        console.log(`✅ Got ${expiryDates.length} expiry dates for ${symbol}`);
      } else if (Array.isArray(response.data)) {
        expiryDates = response.data;
        console.log(`✅ Got ${expiryDates.length} expiry dates (direct array)`);
      } else {
        console.error('❌ Unexpected response format:', response.data);
        setError('Invalid response format from contracts API');
        setAvailableExpiries([]);
        return;
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
      
      // Auto-select nearest expiry (always select when new expiries are loaded)
      if (expiries.length > 0) {
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
    console.log(`📅 Expiry selected: ${expiry} for ${symbol}`);
    setSelectedExpiry(expiry);
  };

  // Reset expiry when symbol changes
  useEffect(() => {
    console.log(`🔄 Symbol changed to ${symbol}, resetting expiry`);
    setSelectedExpiry('');
    setOiData([]);
  }, [symbol]);

  // Fetch spot price when symbol changes
  useEffect(() => {
    if (symbol) {
      fetchSpotPrice();
    }
  }, [symbol]);

  // Find closest strike to spot price
  const closestStrike = useMemo(() => {
    if (!spotPrice || oiData.length === 0) return null;
    
    let closest = null;
    let closestDistance = Infinity;
    
    oiData.forEach((row) => {
      const distance = Math.abs(row.strike - spotPrice);
      if (distance < closestDistance) {
        closestDistance = distance;
        closest = row.strike;
      }
    });
    
    return closest;
  }, [spotPrice, oiData]);

  // Fetch available expiry dates
  useEffect(() => {
    console.log(`🔄 Fetching expiries for ${symbol}...`);
    fetchAvailableExpiries();
  }, [symbol]);

  // Fetch option chain data
  useEffect(() => {
    console.log(`🔍 Option chain useEffect triggered. selectedExpiry: "${selectedExpiry}", symbol: ${symbol}`);
    // Only fetch if we have a selected expiry
    if (selectedExpiry) {
      console.log(`🔍 Starting option chain fetch for ${symbol} with expiry: ${selectedExpiry}`);
      const fetchOptionChain = async () => {
        try {
          setLoading(true);
          setError(null);
          
          console.log(`📡 Fetching option chain for ${symbol} with expiry: ${selectedExpiry}`);
          console.log(`📡 Full API URL: http://localhost:8000/api/v1/options/chain/${symbol}?expiry_date=${selectedExpiry}`);
          if (symbol === 'BANKNIFTY') {
            console.log('📡 Option chain API called for BANKNIFTY');
          }
          const response = await axios.get(
            `http://localhost:8000/api/v1/options/chain/${symbol}?expiry_date=${selectedExpiry}`
          );
        
          console.log("📊 Option chain response:", response.data);
          
          // Check if response is AUTH_REQUIRED
          if (response.data && response.data.session_type === 'AUTH_REQUIRED') {
            console.log('🚫 AUTH_REQUIRED received for option chain - authentication needed');
            setError('Authentication required to fetch option chain data');
            setOiData([]);
            return;
          }
          
          // Handle successful response with real data
          if (response.data && response.data.status === 'success') {
            console.log(`✅ Got option chain data for ${symbol}`);
            const chain = response.data;
            
            // Backend returns: {status: "success", data: {symbol, expiry, calls, puts}}
            const calls = chain?.data?.calls || [];
            const puts = chain?.data?.puts || [];
            
            console.log(`📊 Got ${calls.length} calls and ${puts.length} puts`);
            console.log("=== DEBUG: First 3 calls ===");
            console.table(calls?.slice(0, 3));
            console.log("=== DEBUG: First 3 puts ===");
            console.table(puts?.slice(0, 3));
            
            // Find ATM strike and transform data
            const transformedData = transformOptionChainData(calls, puts, spotPrice);
            console.log(`🔄 Transformed data: ${transformedData.length} rows`);
            setOiData(transformedData);
            setError(null); // Clear any previous errors
            
          } else {
            console.error('❌ Invalid option chain response format:', response.data);
            setError('Invalid response format from option chain API');
            setOiData([]);
            return;
          }
        
        } catch (error: any) {
          console.error('❌ Error fetching option chain:', error);
          setError('Failed to fetch option chain data');
          setOiData([]);
        } finally {
          setLoading(false);
        }
      };

      fetchOptionChain();
    }
  }, [symbol, selectedExpiry, spotPrice]);

  // Transform option chain data into the format expected by the table
  const transformOptionChainData = (calls: any[], puts: any[], spotPrice: number) => {
    const transformedData = calls.map((call: any) => {
      const matchingPut = puts.find(
        (p: any) => p.strike === call.strike
      );
    
      return {
        strike: call.strike,
        oi: call.oi || 0,
        change: call.change || 0,
        ltp: call.ltp || 0,
        putOi: matchingPut?.oi || 0,
        putChange: matchingPut?.change || 0,
        putLtp: matchingPut?.ltp || 0,
      };
    });
    
    // Find ATM strike (closest to spot price)
    const atmStrike = transformedData.reduce((closest: any, current: any) => {
      return Math.abs(current.strike - spotPrice) < Math.abs(closest.strike - spotPrice)
        ? current
        : closest;
    }, transformedData[0]);
    
    // Mark ATM strike
    const finalData = transformedData.map((item: any) => ({
      ...item,
      isATM: item.strike === atmStrike.strike,
    }));
    
    return finalData;
  };

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

  // Debug logs before rendering
  console.log("=== DEBUG: About to render oiData with", oiData?.length, "rows");
  console.log("=== DEBUG: Current symbol:", symbol);
  console.log("=== DEBUG: Current spot price:", spotPrice);
  console.log("=== DEBUG: Closest strike to spot price:", closestStrike);
  console.log("=== DEBUG: Selected expiry:", selectedExpiry);
  oiData.forEach((row, index) => {
    if (index < 3) {
      console.log(`=== DEBUG: Row ${index} strike=${row.strike} oi=${row.oi} ltp=${row.ltp} spotMatch=${row.strike === spotPrice}`);
    }
  });

  return (
    <div className="space-y-4">
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
      <div className="overflow-x-auto overflow-y-auto h-[500px] border border-white/10 rounded-lg shadow-lg">
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-muted-foreground border-b border-white/20 bg-muted/50 sticky top-0 z-10">
              <th className="pb-4 px-4">Strike</th>
              <th className="pb-4 px-4 text-center">Call OI</th>
              <th className="pb-4 px-4 text-center">Call Chg</th>
              <th className="pb-4 px-4 text-center">Call LTP</th>
              <th className="pb-4 px-4 text-center">Put LTP</th>
              <th className="pb-4 px-4 text-center">Put Chg</th>
              <th className="pb-4 px-4 text-center">Put OI</th>
            </tr>
          </thead>
          <tbody>
            {oiData.map((row, index) => {
              const isATM = row.isATM || false;
              
              // Debug first few rows
              if (index < 3) {
                console.log(`🔍 Rendering row ${index}: strike=${row.strike}, callOI=${row.oi}, putOI=${row.putOi}, callLTP=${row.ltp}, putLTP=${row.putLtp}`);
              }
              
              return (
                <tr 
                  key={row.strike} 
                  data-strike={row.strike}
                  className={`border-b border-white/5 hover:bg-white/5 transition-colors ${
                    isATM ? 'bg-green-500/20 border-green-500/50 shadow-lg shadow-green-500/20' : ''
                  }`}
                >
                  <td className={`py-4 px-4 font-bold text-sm ${
                    isATM ? 'text-green-500 border-l-4 border-l-green-500' : ''
                  }`}>
                    <div className="flex items-center justify-between">
                      <span>{row.strike.toLocaleString('en-IN')}</span>
                      {isATM && (
                        <span className="text-xs bg-green-500 text-white px-2 py-1 rounded-full">ATM</span>
                      )}
                    </div>
                  </td>
                  
                  {/* Call OI with heatmap */}
                  <td className="py-4 px-4 text-center">
                    <div 
                      className="px-3 py-2 rounded text-sm font-medium text-white oi-heatmap-cell"
                      style={{ backgroundColor: 'rgba(239, 68, 68, 0.5)' }}
                    >
                      {row.oi.toLocaleString('en-IN')}
                    </div>
                  </td>
                  
                  {/* Call Change */}
                  <td className="py-4 px-4 text-center">
                    <div className={`px-3 py-2 rounded text-sm font-medium ${
                      row.change > 0 ? 'bg-success-500/20 text-success-500' :
                      row.change < 0 ? 'bg-danger-500/20 text-danger-500' :
                      'bg-gray-500/20 text-gray-300'
                    }`}>
                      {row.change?.toLocaleString('en-IN')}
                    </div>
                  </td>
                  
                  {/* Call LTP */}
                  <td className="py-4 px-4 text-center text-sm font-medium">
                    {row.ltp?.toLocaleString('en-IN', {
                      style: 'currency',
                      currency: 'INR'
                    })}
                  </td>
                  
                  {/* Put LTP */}
                  <td className="py-4 px-4 text-center text-sm font-medium">
                    {row.putLtp?.toLocaleString('en-IN', {
                      style: 'currency',
                      currency: 'INR'
                    })}
                  </td>
                  
                  {/* Put Change */}
                  <td className="py-4 px-4 text-center">
                    <div className={`px-3 py-2 rounded text-sm font-medium ${
                      row.putChange > 0 ? 'bg-success-500/20 text-success-500' :
                      row.putChange < 0 ? 'bg-danger-500/20 text-danger-500' :
                      'bg-gray-500/20 text-gray-300'
                    }`}>
                      {row.putChange?.toLocaleString('en-IN')}
                    </div>
                  </td>
                  
                  {/* Put OI with heatmap */}
                  <td className="py-4 px-4 text-center">
                    <div 
                      className="px-3 py-2 rounded text-sm font-medium text-white oi-heatmap-cell"
                      style={{ backgroundColor: 'rgba(239, 68, 68, 0.5)' }}
                    >
                      {row.putOi?.toLocaleString('en-IN')}
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
