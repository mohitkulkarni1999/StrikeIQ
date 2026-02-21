import React, { memo, useMemo, useCallback, useState } from 'react';
import { OptionChainData } from '../../types/dashboard';

interface VirtualizedOptionChainProps {
  optionChainData: OptionChainData;
}

// Row component for virtualized list
const OptionRow = memo(({ 
  index, 
  style, 
  data 
}: { 
  index: number; 
  style: React.CSSProperties; 
  data: any;
}) => {
  const item = data[index];
  
  if (!item) return null;
  
  return (
    <div style={style} className="flex items-center border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
      <div className="flex-1 text-xs font-mono text-gray-300 px-2 py-1">
        {item.strike}
      </div>
      <div className="w-24 text-xs font-mono text-red-400 px-2 py-1 text-right">
        {item.call_oi ? (item.call_oi / 1000).toFixed(1) + 'k' : '-'}
      </div>
      <div className="w-24 text-xs font-mono text-green-400 px-2 py-1 text-right">
        {item.put_oi ? (item.put_oi / 1000).toFixed(1) + 'k' : '-'}
      </div>
      <div className="w-24 text-xs font-mono text-blue-400 px-2 py-1 text-right">
        {item.total_oi ? (item.total_oi / 1000).toFixed(1) + 'k' : '-'}
      </div>
      <div className="w-20 text-xs font-mono text-gray-400 px-2 py-1 text-right">
        {item.oi_concentration ? item.oi_concentration.toFixed(1) + '%' : '-'}
      </div>
    </div>
  );
});

OptionRow.displayName = 'OptionRow';

const VirtualizedOptionChain: React.FC<VirtualizedOptionChainProps> = memo(({ optionChainData }) => {
  const [selectedType, setSelectedType] = useState<'calls' | 'puts' | 'both'>('both');
  
  // Memoized data processing
  const processedData = useMemo(() => {
    if (!optionChainData) return { calls: [], puts: [], combined: [] };
    
    const calls = optionChainData.calls || [];
    const puts = optionChainData.puts || [];
    
    // Process calls
    const processedCalls = calls.map(call => ({
      strike: call.strike,
      call_oi: call.open_interest || 0,
      put_oi: 0,
      total_oi: call.open_interest || 0,
      oi_concentration: 0, // Would calculate from total
      type: 'call' as const,
      ltp: call.ltp || 0,
      change: call.change || 0,
      volume: call.volume || 0
    }));
    
    // Process puts
    const processedPuts = puts.map(put => ({
      strike: put.strike,
      call_oi: 0,
      put_oi: put.open_interest || 0,
      total_oi: put.open_interest || 0,
      oi_concentration: 0, // Would calculate from total
      type: 'put' as const,
      ltp: put.ltp || 0,
      change: put.change || 0,
      volume: put.volume || 0
    }));
    
    // Combine for unified view
    const combined = [];
    const strikeMap = new Map();
    
    // Add calls to map
    processedCalls.forEach(call => {
      const existing = strikeMap.get(call.strike) || { strike: call.strike, call_oi: 0, put_oi: 0, total_oi: 0 };
      strikeMap.set(call.strike, {
        ...existing,
        call_oi: call.call_oi,
        total_oi: existing.total_oi + call.call_oi
      });
    });
    
    // Add puts to map
    processedPuts.forEach(put => {
      const existing = strikeMap.get(put.strike) || { strike: put.strike, call_oi: 0, put_oi: 0, total_oi: 0 };
      strikeMap.set(put.strike, {
        ...existing,
        put_oi: put.put_oi,
        total_oi: existing.total_oi + put.put_oi
      });
    });
    
    // Convert map to array and calculate concentrations
    const totalOI = Array.from(strikeMap.values()).reduce((sum, item) => sum + item.total_oi, 0);
    
    strikeMap.forEach((value, key) => {
      value.oi_concentration = totalOI > 0 ? (value.total_oi / totalOI) * 100 : 0;
      combined.push(value);
    });
    
    // Sort by strike
    combined.sort((a, b) => a.strike - b.strike);
    
    return {
      calls: processedCalls,
      puts: processedPuts,
      combined
    };
  }, [optionChainData]);
  
  // Filter data based on selected type
  const filteredData = useMemo(() => {
    switch (selectedType) {
      case 'calls':
        return processedData.calls;
      case 'puts':
        return processedData.puts;
      case 'both':
      default:
        return processedData.combined;
    }
  }, [processedData, selectedType]);
  
  // Memoized item renderer
  const RowRenderer = useCallback(({ index, style }) => {
    return (
      <OptionRow
        index={index}
        style={style}
        data={filteredData}
      />
    );
  }, [filteredData]);
  
  // Memoized item size getter
  const getItemSize = useCallback(() => 32, []); // 32px per row
  
  // Memoized item key getter
  const getItemKey = useCallback((index: number) => {
    const item = filteredData[index];
    return `${item.strike}-${item.type}`;
  }, [filteredData]);
  
  if (!optionChainData || filteredData.length === 0) {
    return (
      <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-8 text-center">
        <div className="text-gray-400">No option chain data available</div>
      </div>
    );
  }
  
  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Option Chain</h3>
        
        {/* Filter buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => setSelectedType('both')}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              selectedType === 'both'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Both
          </button>
          <button
            onClick={() => setSelectedType('calls')}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              selectedType === 'calls'
                ? 'bg-red-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Calls
          </button>
          <button
            onClick={() => setSelectedType('puts')}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              selectedType === 'puts'
                ? 'bg-green-500 text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Puts
          </button>
        </div>
      </div>
      
      {/* Column headers */}
      <div className="flex items-center border-b border-gray-700 pb-2 mb-2">
        <div className="flex-1 text-xs font-bold text-gray-400 px-2">Strike</div>
        <div className="w-24 text-xs font-bold text-red-400 px-2 text-right">Call OI</div>
        <div className="w-24 text-xs font-bold text-green-400 px-2 text-right">Put OI</div>
        <div className="w-24 text-xs font-bold text-blue-400 px-2 text-right">Total OI</div>
        <div className="w-20 text-xs font-bold text-gray-400 px-2 text-right">Conc</div>
      </div>
      
      {/* Virtualized list */}
      <div className="border border-gray-800 rounded">
        <List
          height={400} // Fixed height for virtualization
          itemCount={filteredData.length}
          itemSize={getItemSize()}
          itemData={filteredData}
          itemKey={getItemKey}
          children={RowRenderer}
          overscanCount={5} // Render 5 extra items above/below
        />
      </div>
      
      {/* Footer with stats */}
      <div className="mt-4 text-xs text-gray-400 text-center">
        Showing {filteredData.length} strikes • Virtual rendering enabled
      </div>
    </div>
  );
});

VirtualizedOptionChain.displayName = 'VirtualizedOptionChain';

export default VirtualizedOptionChain;
