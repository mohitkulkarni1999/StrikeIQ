import { useEffect, useState } from 'react';
import Head from 'next/head';
import Dashboard from '../components/Dashboard';
import { MarketData } from '../types/market';

export default function Home() {
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');

  useEffect(() => {
    fetchMarketData();
    
    // Only set up interval if we don't have market closed data yet
    let interval: NodeJS.Timeout | null = null;
    
    if (!marketData?.current_market?.market_status || marketData?.current_market?.market_status !== 'CLOSED') {
      interval = setInterval(fetchMarketData, 5000); // Refresh every 5 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [selectedSymbol, marketData?.current_market?.market_status]);

  // Prevent scroll anchoring on data updates - only when market is open
  useEffect(() => {
    // Only prevent scrolling when market is open and data is changing
    if (marketData?.current_market?.market_status !== 'CLOSED') {
      const preventScrollAnchoring = () => {
        if ('scrollRestoration' in history) {
          history.scrollRestoration = 'manual';
        }
        window.scrollTo({ top: window.scrollY, behavior: 'auto' });
      };

      preventScrollAnchoring();
    }
  }, [marketData]);

  const fetchMarketData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/dashboard/${selectedSymbol}`);
      const data = await response.json();
      
      setMarketData(data);
      
      // Stop polling if market is closed
      if (data.market_status === 'closed') {
        setLoading(false);
        return; // Don't continue polling
      }

    } catch (error) {
      console.error('Error fetching market data:', error);
    } finally {
      setLoading(false);
    }
  };

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
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                  className="glass-morphism px-4 py-2 rounded-lg border border-white/10 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="NIFTY">NIFTY</option>
                  <option value="BANKNIFTY">BANKNIFTY</option>
                </select>
                
                <div className="flex items-center gap-2">
                  <div className="status-indicator status-online"></div>
                  <span className="text-sm text-muted-foreground">Live</span>
                </div>
              </div>
            </div>
          </header>

          {loading ? (
            <div className="flex items-center justify-center h-96">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          ) : (
            <Dashboard data={marketData} />
          )}
        </div>
      </main>
    </>
  );
}
