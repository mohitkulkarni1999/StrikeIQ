import { useEffect, useState } from 'react';
import Head from 'next/head';
import Dashboard from '../components/Dashboard';
import { DashboardResponse } from '../types/dashboard';

export default function Home() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');

  useEffect(() => {
    fetchMarketData();

    // Set up polling only if not loading and not in auth mode
    let interval: NodeJS.Timeout | null = null;

    const shouldPoll = () => {
      if (data && 'session_type' in data && data.session_type === 'AUTH_REQUIRED') {
        return false; // Don't poll if auth required
      }
      if (data && 'market_status' in data && data.market_status === 'CLOSED') {
        return false; // Don't poll if market closed
      }
      return true;
    };

    if (shouldPoll()) {
      interval = setInterval(fetchMarketData, 5000); // Refresh every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [selectedSymbol, data]);

  const fetchMarketData = async () => {
    try {
      console.log('Fetching market data for:', selectedSymbol);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/dashboard/${selectedSymbol}`);
      const responseData: DashboardResponse = await response.json();

      console.log('Received data:', responseData);
      console.log('Response status:', response.status);

      setData(responseData);
      setLoading(false);

    } catch (error) {
      console.error('Error fetching market data:', error);
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>StrikeIQ - Options Market Intelligence</title>
        <meta name="description" content="AI-powered options market intelligence for Indian markets" />
        <meta name="viewport" content="width=device-width= initial-scale=1" />
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
                  <div className={`status-indicator ${
                    data && 'market_status' in data && data.market_status === 'OPEN' ? 'status-online' : 'status-offline'
                  }`}></div>
                  <span className="text-sm text-muted-foreground">
                    {data && 'session_type' in data ? 'Auth Required' : 
                     data && 'market_status' in data ? data.market_status : 'Loading'}
                  </span>
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
            <Dashboard data={data} />
          )}
        </div>
      </main>
    </>
  );
}
