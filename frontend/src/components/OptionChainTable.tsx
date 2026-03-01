import React from 'react';
import { useDashboardData } from '@/hooks/useDashboardData';

interface OptionChainTableProps {
  symbol: string;
}

const OptionChainTable: React.FC<OptionChainTableProps> = ({ symbol }) => {
  const { calls, puts, spot, connected } = useDashboardData();

  return (
    <div className="bg-gray-900 text-white p-4 rounded-lg">
      <h3 className="text-lg font-bold mb-4">{symbol} Option Chain</h3>
      
      {connected ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="p-2 text-left">Strike</th>
                <th className="p-2 text-right">Call LTP</th>
                <th className="p-2 text-right">Call OI</th>
                <th className="p-2 text-center">Spot</th>
                <th className="p-2 text-right">Put OI</th>
                <th className="p-2 text-right">Put LTP</th>
              </tr>
            </thead>
            <tbody>
              {calls.slice(0, 10).map((call, index) => (
                <tr key={`call-${call.strike}`} className="border-b border-gray-800">
                  <td className="p-2">{call.strike}</td>
                  <td className="p-2 text-right">{call.ltp || '-'}</td>
                  <td className="p-2 text-right">{call.oi || '-'}</td>
                  <td className="p-2 text-center font-bold text-yellow-400">
                    {spot > 0 ? spot.toFixed(2) : '-'}
                  </td>
                  <td className="p-2 text-right">{puts[index]?.oi || '-'}</td>
                  <td className="p-2 text-right">{puts[index]?.ltp || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-8">
          <div className="text-gray-400">Connecting to market data...</div>
        </div>
      )}
    </div>
  );
};

export default OptionChainTable;
