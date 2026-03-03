/**
 * Production App Bootstrap Guard for StrikeIQ
 * Ensures single auth check and stable app initialization
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth, checkGlobalAuth } from '@/stores/productionAuthStore';

interface AppBootstrapGuardProps {
  children: React.ReactNode;
}

const AppBootstrapGuard: React.FC<AppBootstrapGuardProps> = ({ children }) => {
  const router = useRouter();
  const { authenticated, loading, checked, error, backendStatus } = useAuth();
  const [isClient, setIsClient] = useState(false);
  const [bootstrapComplete, setBootstrapComplete] = useState(false);

  // Ensure we're on client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Perform ONE-TIME auth check
  useEffect(() => {
    if (!isClient || bootstrapComplete) return;

    const performBootstrap = async () => {
      console.log('🚀 Starting app bootstrap...');
      
      try {
        await checkGlobalAuth();
        console.log('✅ App bootstrap completed');
      } catch (error) {
        console.error('❌ App bootstrap failed:', error);
      } finally {
        setBootstrapComplete(true);
      }
    };

    performBootstrap();
  }, [isClient, bootstrapComplete]);

  // Show loading screen during bootstrap
  if (!isClient || !bootstrapComplete || loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">Initializing StrikeIQ...</p>
          <p className="text-gray-400 text-sm mt-2">Please wait</p>
        </div>
      </div>
    );
  }

  // Handle backend offline state
  if (backendStatus === 'offline') {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-500 text-6xl mb-4">🔌</div>
          <h1 className="text-white text-2xl font-bold mb-2">Backend Offline</h1>
          <p className="text-gray-400 mb-6">
            The StrikeIQ backend is currently unavailable. Please check your connection and try again.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Render children after bootstrap is complete
  return <>{children}</>;
};

export default AppBootstrapGuard;
