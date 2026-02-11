import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { AuthRequiredData } from '../types/dashboard';

interface AuthScreenProps {
  authData: AuthRequiredData;
}

function AuthScreen({ authData }: AuthScreenProps) {
  const { checkAuth } = useAuth();

  const handleReconnect = () => {
    // Stop any existing polling
    const event = new CustomEvent('stopPolling');
    window.dispatchEvent(event);
    
    // Store the auth URL temporarily and redirect to Upstox
    sessionStorage.setItem('upstox_auth_url', authData.login_url);
    window.location.href = authData.login_url;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="glass-morphism rounded-2xl p-8 text-center">
          {/* Icon */}
          <div className="w-20 h-20 bg-orange-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg 
              className="w-10 h-10 text-white" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" 
              />
            </svg>
          </div>

          {/* Title */}
          <h1 className="text-3xl font-bold text-white mb-2">
            Authentication Required
          </h1>

          {/* Message */}
          <p className="text-gray-300 mb-8 leading-relaxed">
            {authData.message}
          </p>

          {/* Status Badge */}
          <div className="inline-flex items-center gap-2 bg-orange-500/20 text-orange-400 px-4 py-2 rounded-full mb-8">
            <div className="w-2 h-2 bg-orange-400 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium">Session Expired</span>
          </div>

          {/* Reconnect Button */}
          <button
            onClick={handleReconnect}
            className="w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-orange-500/25"
          >
            <div className="flex items-center justify-center gap-3">
              <svg 
                className="w-5 h-5" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" 
                />
              </svg>
              <span>Get Authorization</span>
            </div>
          </button>

          {/* Help Text */}
          <div className="mt-6 text-sm text-gray-400">
            <p>You'll be redirected to the authorization server.</p>
            <p className="mt-1">After authorization, you'll be returned here automatically.</p>
          </div>

          {/* Timestamp */}
          <div className="mt-8 pt-6 border-t border-gray-700">
            <p className="text-xs text-gray-500">
              Detected at: {new Date(authData.timestamp).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default React.memo(AuthScreen);
