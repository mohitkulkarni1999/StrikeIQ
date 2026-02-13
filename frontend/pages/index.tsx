import { useEffect, useState } from 'react';
import Head from 'next/head';
import Dashboard from '../components/Dashboard';
import { DashboardResponse, isAuthRequired, isRateLimit } from '../types/dashboard';

export default function Home() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState('NIFTY');
  const [authStatus, setAuthStatus] = useState<any>(null);

  useEffect(() => {
    fetchMarketData();
  }, []);

  // Fetch market data when symbol changes
  useEffect(() => {
    if (authStatus && 'authenticated' in authStatus && authStatus.authenticated) {
      fetchMarketData();
    }
  }, [selectedSymbol]);

  useEffect(() => {
    const interval = setInterval(() => {
      // Only fetch if we have valid auth status
      if (authStatus && 'authenticated' in authStatus && authStatus.authenticated) {
        fetchMarketData();
      }
    }, 60000); // 60 seconds

    return () => clearInterval(interval);
  }, [selectedSymbol, authStatus]); // Include authStatus in dependencies

  const fetchMarketData = async () => {
    try {
      console.log('📊 Fetching market data for:', selectedSymbol);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/dashboard/${selectedSymbol}`);
      const responseData: DashboardResponse = await response.json();

      console.log("📊 DASHBOARD RESPONSE:", responseData);

      // AUTH_REQUIRED must be handled BEFORE any normal data logic
      if (isAuthRequired(responseData)) {
        console.warn("AUTH_REQUIRED received - stopping polling");
        // Let Dashboard component handle auth required
        setData(responseData);
        setLoading(false);
        return;
      }

      // RATE_LIMIT handling
      if (isRateLimit(responseData)) {
        console.warn("RATE_LIMIT received - stopping polling");
        setData(responseData);
        setLoading(false);
        return;
      }

      // Only call setData for normal data if session_type is NOT present
      setData(responseData);
      setLoading(false);

    } catch (error) {
      console.error('Error fetching market data:', error);
      setLoading(false);
    }
  };

  const fetchAuthStatus = async () => {
    try {
      console.log('🔍 Checking auth status...');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/options/auth/status`);
      const status = await response.json();
      
      console.log('📊 Auth status response:', status);
      
      // Update auth context state based on auth status response
      if (status.session_type === 'AUTH_REQUIRED') {
        console.log('🚫 Auth required - dispatching authRequired event');
        window.dispatchEvent(new CustomEvent('authRequired', { 
          detail: { login_url: status.login_url } 
        }));
      } else if (status.authenticated) {
        console.log('✅ Auth successful - dispatching authSuccess event');
        window.dispatchEvent(new CustomEvent('authSuccess'));
      } else {
        console.log('⚠️ Unknown auth status:', status);
      }
      
      setAuthStatus(status);
      return status;
    } catch (error) {
      console.error('❌ Auth status check failed:', error);
      return null;
    }
  };

  // Check auth status frequently (every 5 seconds)
  useEffect(() => {
    fetchAuthStatus(); // Initial check

    const authInterval = setInterval(() => {
      fetchAuthStatus();
    }, 5000);

    return () => clearInterval(authInterval);
  }, []);

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
                  onChange={(e) => {
  console.log('🔄 Symbol changed from', selectedSymbol, 'to', e.target.value);
  setSelectedSymbol(e.target.value);
}}
                  className="glass-morphism px-4 py-2 rounded-lg border border-white/10 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="NIFTY">NIFTY</option>
                  <option value="BANKNIFTY">BANKNIFTY</option>
                </select>

                <div className="flex items-center gap-2">
                  <div className={`status-indicator ${
                    authStatus && 'session_type' in authStatus ? 'status-error' : 
                    authStatus && 'authenticated' in authStatus && authStatus.authenticated ? 'status-online' : 'status-offline'
                  }`}></div>
                  <span className="text-sm text-muted-foreground">
                    {authStatus && 'session_type' in authStatus ? 'Auth Required' : 
                     authStatus && 'authenticated' in authStatus && authStatus.authenticated ? 'Authenticated' : 
                     authStatus ? 'Auth Checking...' : 'Loading'}
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
            <Dashboard data={data} symbol={selectedSymbol} />
          )}
        </div>
      </main>
    </>
  );
}
