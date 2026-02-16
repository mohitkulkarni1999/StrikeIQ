import { useEffect, useState } from 'react';
import Head from 'next/head';
import DashboardComponent from '../components/Dashboard';

export default function Home() {
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');

  console.log('🔍 Home page - Rendered with symbol:', selectedSymbol);

  return (
    <>
      <Head>
        <title>StrikeIQ - Options Market Intelligence</title>
        <meta name="description" content="AI-powered options market intelligence for Indian markets" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-background text-foreground">
        <div className="container mx-auto px-4 py-6">
          <header className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-gradient mb-2">StrikeIQ</h1>
                <p className="text-muted-foreground">AI-Powered Options Market Intelligence</p>
              </div>

              <div className="flex items-center gap-4">
                <select
                  value={selectedSymbol}
                  onChange={(e) => {
                    console.log('🔄 Symbol changed from', selectedSymbol, 'to', e.target.value);
                    setSelectedSymbol(e.target.value);
                  }}
                  className="glass-morphism px-4 py-2 rounded-lg border border-white/10 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="NIFTY">NIFTY</option>
                  <option value="BANKNIFTY">BANKNIFTY</option>
                </select>
              </div>
            </div>
          </header>

          {/* Test to verify DashboardComponent is being used */}
          <div className="mb-4 p-4 bg-yellow-500/20 border border-yellow-500 rounded-lg">
            <div className="text-yellow-300 text-sm font-medium">
              🧪 TEST: DashboardComponent should render below this line
            </div>
          </div>

          <DashboardComponent symbol={selectedSymbol} />
        </div>
      </main>
    </>
  );
}
