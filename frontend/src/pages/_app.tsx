import type { AppProps } from 'next/app'
import { useEffect } from 'react'
import { AuthProvider } from '@/contexts/AuthContext'
import Navbar from '@/components/layout/Navbar'
import AppBootstrapGuard from '@/components/AppBootstrapGuard'
import { useWSStore } from '@/core/ws/wsStore'
import '@/styles/globals.css'

function MyApp({ Component, pageProps }: AppProps) {

  useEffect(() => {

    // Apply dark mode
    document.documentElement.classList.add('dark')

    // ===============================
    // GLOBAL WEBSOCKET INITIALIZATION
    // ===============================

    if (typeof window !== "undefined") {

      const store = useWSStore.getState()

      // Prevent duplicate sockets (React StrictMode safe)
      if (!(window as any).__STRIKEIQ_WS_STARTED) {

        if (!store.connected && !store.ws) {

          console.log("🚀 Initializing global WebSocket connection")

          store.connect("NIFTY", "")

        }

        ;(window as any).__STRIKEIQ_WS_STARTED = true
      }
    }

    // ===============================
    // AUTH EXPIRY LISTENER
    // ===============================

    const handleAuthExpired = () => {

      console.warn("🔐 Auth expired event received - redirecting to /auth")

      localStorage.removeItem("upstox_auth")
      sessionStorage.removeItem("upstox_auth")

      window.location.href = "/auth"
    }

    window.addEventListener("auth-expired", handleAuthExpired)

    console.log("🔍 AUTH EXPIRY LISTENER INSTALLED")

    return () => {
      window.removeEventListener("auth-expired", handleAuthExpired)
    }

  }, [])

  return (
    <AuthProvider>
      <AppBootstrapGuard>
        <div className="min-h-screen bg-background text-text-primary">
          <Navbar />
          <Component {...pageProps} />
        </div>
      </AppBootstrapGuard>
    </AuthProvider>
  )
}

export default MyApp