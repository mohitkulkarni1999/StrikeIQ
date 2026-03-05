import React, { useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import { useOptionChain } from '../stores/marketStore';
import type { OptionData } from '../stores/marketStore';

interface VirtualizedOptionChainProps {
  height?: number;
}

const VirtualizedOptionChain: React.FC<VirtualizedOptionChainProps> = ({ height = 400 }) => {
  const optionChain = useOptionChain();

  const items = useMemo(() => {
    if (!optionChain?.strikes) return [];
    
    // Sort strikes by distance from ATM
    return [...optionChain.strikes].sort((a, b) => {
      const distanceA = Math.abs(a.strike - optionChain.atm_strike);
      const distanceB = Math.abs(b.strike - optionChain.atm_strike);
      return distanceA - distanceB;
    });
  }, [optionChain]);

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const item = items[index];
    if (!item) return null;

    return (
      <div style={style} className="flex border-b border-gray-200 hover:bg-gray-50">
        {/* Strike */}
        <div className="w-20 px-2 py-1 text-sm font-medium text-gray-900 border-r">
          {item.strike}
        </div>
        
        {/* Call Data */}
        <div className="flex-1 grid grid-cols-3 gap-2 px-2 py-1">
          <div className="text-sm text-green-600">
            <div className="font-medium">{item.call_ltp.toFixed(2)}</div>
            <div className="text-xs text-gray-500">{item.call_oi.toLocaleString()}</div>
          </div>
          <div className="text-sm text-gray-400">
            <div className="font-medium">{item.call_volume.toLocaleString()}</div>
          </div>
          <div className="text-sm text-gray-300">
            {/* IV placeholder */}
            {((item.call_ltp / item.strike) * 100).toFixed(1)}%
          </div>
        </div>
        
        {/* Put Data */}
        <div className="flex-1 grid grid-cols-3 gap-2 px-2 py-1">
          <div className="text-sm text-red-600">
            <div className="font-medium">{item.put_ltp.toFixed(2)}</div>
            <div className="text-xs text-gray-500">{item.put_oi.toLocaleString()}</div>
          </div>
          <div className="text-sm text-gray-400">
            <div className="font-medium">{item.put_volume.toLocaleString()}</div>
          </div>
          <div className="text-sm text-gray-300">
            {/* IV placeholder */}
            {((item.put_ltp / item.strike) * 100).toFixed(1)}%
          </div>
        </div>
      </div>
    );
  };

  if (!optionChain) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading option chain...</div>
      </div>
    );
  }

  return (
    <div className="border border-gray-300 rounded-lg">
      {/* Header */}
      <div className="flex bg-gray-50 border-b border-gray-200">
        <div className="w-20 px-2 py-2 text-sm font-semibold text-gray-900 border-r">
          Strike
        </div>
        <div className="flex-1 grid grid-cols-3 gap-2 px-2 py-2">
          <div className="text-sm font-semibold text-green-600">Call LTP / OI</div>
          <div className="text-sm font-semibold text-gray-600">Volume</div>
          <div className="text-sm font-semibold text-gray-400">IV</div>
        </div>
        <div className="flex-1 grid grid-cols-3 gap-2 px-2 py-2">
          <div className="text-sm font-semibold text-red-600">Put LTP / OI</div>
          <div className="text-sm font-semibold text-gray-600">Volume</div>
          <div className="text-sm font-semibold text-gray-400">IV</div>
        </div>
      </div>
      
      {/* Virtualized List */}
      <List
        height={height}
        itemCount={items.length}
        itemSize={40}
        itemData={items}
        width="100%"
      >
        {Row}
      </List>
    </div>
  );
};

export default VirtualizedOptionChain;
