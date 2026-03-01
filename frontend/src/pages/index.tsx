import { useState } from 'react';
import Head from 'next/head';
import Dashboard from '@/components/Dashboard';
import Footer, { type FooterProps } from '@/components/layout/Footer';

const SYMBOLS = ['NIFTY', 'BANKNIFTY', 'FINNIFTY'] as const;
type Symbol = typeof SYMBOLS[number];

const OPEN_STATES = ['OPEN', 'PRE_OPEN', 'OPENING_END'];

export default function Home() {
  const [selectedSymbol, setSelectedSymbol] = useState<Symbol>('NIFTY');

  return (
    <>
      <Head>
        <title>StrikeIQ — Options Market Intelligence</title>
        <meta name="description" content="AI-powered options market intelligence for Indian markets" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
      </Head>

      {/* ── PAGE SHELL ─────────────────────────────────────────────────────── */}
      <div
        className="min-h-screen text-white pb-20 md:pb-0"
        style={{
          background: 'radial-gradient(ellipse 120% 60% at 50% -10%, #0e1726 0%, #0B0E11 55%)',
          fontFamily: "'Space Grotesk', sans-serif",
        }}
      >
        {/* Scanline grid overlay */}
        <div
          className="pointer-events-none fixed inset-0 z-0 opacity-[0.025]"
          style={{
            backgroundImage:
              'linear-gradient(#00E5FF 1px, transparent 1px), linear-gradient(90deg, #00E5FF 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />

        {/* ── SYMBOL + MARKET STATUS CONTROL BAR ────────────────────────── */}
        <div className="relative z-10 max-w-[1920px] mx-auto px-3 sm:px-5 lg:px-8 pt-4 sm:pt-5 pb-2">
          <div className="flex flex-wrap items-center justify-between gap-3">

            {/* Symbol pills */}
            <div className="flex items-center gap-1.5 sm:gap-2">
              <span
                className="hidden xs:block text-[10px] text-slate-600 uppercase tracking-widest mr-1"
                style={{ fontFamily: "'JetBrains Mono', monospace" }}
              >
                Index
              </span>
              {SYMBOLS.map((sym) => {
                const isActive = selectedSymbol === sym;
                return (
                  <button
                    key={sym}
                    onClick={() => setSelectedSymbol(sym)}
                    className="px-3 sm:px-4 py-1.5 rounded-full text-[11px] sm:text-xs font-bold tracking-wide transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00E5FF]/40"
                    style={
                      isActive
                        ? {
                          background: 'linear-gradient(135deg, rgba(0,229,255,0.18) 0%, rgba(79,140,255,0.12) 100%)',
                          border: '1px solid rgba(0,229,255,0.40)',
                          color: '#00E5FF',
                          boxShadow: '0 0 12px rgba(0,229,255,0.18)',
                          fontFamily: "'JetBrains Mono', monospace",
                        }
                        : {
                          background: 'rgba(255,255,255,0.04)',
                          border: '1px solid rgba(255,255,255,0.08)',
                          color: '#6B7280',
                          fontFamily: "'JetBrains Mono', monospace",
                        }
                    }
                  >
                    {sym}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── DASHBOARD ──────────────────────────────────────────────────── */}
        <div className="relative z-10 pt-20">
          <Dashboard initialSymbol={selectedSymbol} key={selectedSymbol} />
        </div>

        {/* ── FOOTER ─────────────────────────────────────────────────────── */}
        <div className="relative z-10">
          <Footer onSymbolSelect={(sym) => {
            if (SYMBOLS.includes(sym as Symbol)) setSelectedSymbol(sym as Symbol);
          }} />
        </div>
      </div>
    </>
  );
}
