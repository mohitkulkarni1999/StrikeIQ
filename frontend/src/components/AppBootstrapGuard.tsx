import { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuthStore, useAuthStatus, useBackendStatus } from '../stores/authStore'

export default function AppBootstrapGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  
  const status = useAuthStatus()
  const backendStatus = useBackendStatus()
  const { checkAuth } = useAuthStore()
  
  const [isClient, setIsClient] = useState(false)
  const [authChecked, setAuthChecked] = useState(false)
  const [storeRehydrated, setStoreRehydrated] = useState(false)

  // BLOCK ANY REDIRECTS TO /AUTH
  useEffect(() => {
    if (isClient && pathname === '/auth') {
      console.log(' BLOCKING redirect to /auth - staying on current page')
      // Prevent any automatic redirects to auth
      return
    }
  }, [isClient, pathname])

  // SSR hydration guard
  useEffect(() => {
    setIsClient(true)
    // Wait a bit for Zustand store to rehydrate from localStorage
    setTimeout(() => setStoreRehydrated(true), 100)
  }, [])

  // One-time auth check on mount - DISABLED
  useEffect(() => {
    console.log(' AppBootstrapGuard: Auth check DISABLED')
    setAuthChecked(true)
    setStoreRehydrated(true)
  }, [])

  console.log(' AppBootstrapGuard', {
    status,
    backendStatus,
    pathname,
    isClient,
    authChecked,
    storeRehydrated
  })

  // DEBUG: Log when accessing root path
  if (pathname === '/') {
    console.log(' ACCESSING ROOT PATH - Should show dashboard')
  }

  // SSR placeholder - render immediately
  if (!isClient) {
    return (
      <div className="w-screen h-screen flex items-center justify-center bg-slate-900 text-white">
        Loading StrikeIQ...
      </div>
    )
  }

  // Always render children - auth checks disabled
  console.log(' Rendering children - auth checks disabled')
  return <>{children}</>
}