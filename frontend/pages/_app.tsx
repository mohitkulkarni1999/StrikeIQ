import type { AppProps } from 'next/app';
import { useEffect } from 'react';
import { AuthProvider } from '../contexts/AuthContext';
import '../styles/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  useEffect(() => {
    // Apply dark mode by default
    document.documentElement.classList.add('dark');
    
    // � AUTH EXPIRY LISTENER
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
    
    // �🔍 GLOBAL REST CALL INTERCEPTOR FOR AUDIT
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      console.log("🌐 REST CALL DETECTED:", args[0]);
      console.log("🌐 REST METHOD:", args[1]?.method || 'GET');
      console.log("🌐 REST TIMESTAMP:", new Date().toISOString());
      
      const start = performance.now();
      const response = await originalFetch(...args);
      const duration = performance.now() - start;
      
      console.log("🌐 REST STATUS:", response.status);
      console.log("🌐 REST DURATION:", `${duration.toFixed(2)}ms`);
      
      return response;
    };
    
    // 🔍 AXIOS INTERCEPTOR (if axios is used)
    if (typeof window !== 'undefined' && window.axios) {
      window.axios.interceptors.request.use((config) => {
        console.log("🌐 AXIOS REST CALL:", config.url);
        console.log("🌐 AXIOS METHOD:", config.method);
        return config;
      });
    }
    
    console.log("🔍 REST/WINDOW INTERCEPTORS INSTALLED");
    
    // Cleanup on unmount
    return () => {
      window.removeEventListener("auth-expired", handleAuthExpired)
    }
  }, []);

  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

export default MyApp;
