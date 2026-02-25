import type { AppProps } from 'next/app';
import { useEffect } from 'react';
import { AuthProvider } from '@/contexts/AuthContext';
import Navbar from '@/components/layout/Navbar';
import AppBootstrapGuard from '@/components/AppBootstrapGuard';
import WebSocketManager from '@/components/WebSocketManager';
import '@/styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  useEffect(() => {
    // Apply dark mode by default
    document.documentElement.classList.add('dark');

    // AUTH EXPIRY LISTENER
    const handleAuthExpired = () => {
      console.warn('🔐 Auth expired event received - redirecting to /auth')
      // Clear any stored auth data
      localStorage.removeItem("upstox_auth")
      sessionStorage.removeItem("upstox_auth")

      // Redirect to auth screen
      window.location.href = "/auth"
    }

    // Add global event listener for auth expiry
    window.addEventListener("auth-expired", handleAuthExpired)

    console.log("🔍 AUTH EXPIRY LISTENER INSTALLED");

    // Cleanup on unmount
    return () => {
      window.removeEventListener("auth-expired", handleAuthExpired);
    }
  }, []);

  return (
    <AuthProvider>
      <AppBootstrapGuard>
        <div className="min-h-screen bg-background text-text-primary">
          <Navbar />
          {/* WebSocket Manager - ensures persistent connection */}
          <WebSocketManager symbol="NIFTY" expiry="2026-02-26" />
          <Component {...pageProps} />
        </div>
      </AppBootstrapGuard>
    </AuthProvider>
  );
}

export default MyApp;
