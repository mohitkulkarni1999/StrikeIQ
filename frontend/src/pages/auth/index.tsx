import React, { useEffect, useState } from 'react';
import AuthScreen from '../../components/AuthScreen';
import { AuthRequiredData } from '../../types/dashboard';

export default function AuthPage() {
  const [authData, setAuthData] = useState<AuthRequiredData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get auth data from URL params or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const message = urlParams.get('message') || 'Authentication required to access market data';
    
    // Default auth data
    const defaultAuthData: AuthRequiredData = {
      session_type: 'AUTH_REQUIRED',
      mode: 'AUTH',
      login_url: 'https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id=53c878a9-3f5d-44f9-aa2d-2528d34a24cd&redirect_uri=http://localhost:8000/api/v1/auth/upstox/callback',
      message: error || message,
      timestamp: new Date().toISOString()
    };

    setAuthData(defaultAuthData);
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-white text-center">
          <div className="w-16 h-16 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p>Loading authentication...</p>
        </div>
      </div>
    );
  }

  if (!authData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-white text-center">
          <p>Error: Authentication data not available</p>
        </div>
      </div>
    );
  }

  return <AuthScreen authData={authData} />;
}
