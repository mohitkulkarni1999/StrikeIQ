import { useState } from 'react';
import Head from 'next/head';
import Dashboard from '@/components/Dashboard';

export default function Home() {
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');

  return (
    <>
      <Head>
        <title>StrikeIQ - Options Market Intelligence</title>
        <meta name="description" content="AI-powered options market intelligence for Indian markets" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
              STRIKE IQ
            </h1>
            <p className="text-slate-400 text-sm font-mono">NEURAL OPTIONS INTELLIGENCE</p>
          </div>

          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-white px-4 py-2 rounded-lg focus:ring-2 focus:ring-blue-500 transition-all outline-none"
          >
            <option value="NIFTY">NIFTY</option>
            <option value="BANKNIFTY">BANKNIFTY</option>
            <option value="FINNIFTY">FINNIFTY</option>
          </select>
        </div>

        <Dashboard initialSymbol={selectedSymbol} key={selectedSymbol} />
      </main>
    </>
  );
}
