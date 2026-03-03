import React from 'react';
import { useMarketStore } from '@/stores/marketStore';

const SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY"];

export default function SymbolSelector() {
  const currentSymbol = useMarketStore(state => state.currentSymbol);
  const setCurrentSymbol = useMarketStore(state => state.setCurrentSymbol);

  return (
    <div className="flex gap-2">
      {SYMBOLS.map(s => (
        <button
          key={s}
          onClick={() => setCurrentSymbol(s)}
          className={s === currentSymbol ? "chip-active" : "chip"}
        >
          {s}
        </button>
      ))}
    </div>
  );
}
