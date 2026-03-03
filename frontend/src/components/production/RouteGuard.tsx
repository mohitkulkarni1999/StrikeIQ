/**
 * Production Route Guard for StrikeIQ
 * Implements stable routing logic without redirect loops
 */

import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/stores/productionAuthStore';

interface RouteGuardProps {
  children: React.ReactNode;
}

const RouteGuard: React.FC<RouteGuardProps> = ({ children }) => {
  const router = useRouter();
  const { authenticated, checked, loginUrl } = useAuth();

  useEffect(() => {
    // Only apply routing logic after auth check is complete
    if (!checked) {
      return;
    }

    const currentPath = router.pathname;
    console.log('🛡️ RouteGuard evaluating:', { currentPath, authenticated, checked });

    // Rule 1: If authenticated AND on /auth, redirect to dashboard
    if (authenticated && currentPath === '/auth') {
      console.log('🔐 Authenticated user on /auth - redirecting to dashboard');
      router.replace('/');
      return;
    }

    // Rule 2: If NOT authenticated AND NOT on /auth, redirect to /auth
    if (!authenticated && currentPath !== '/auth') {
      console.log('🔓 Unauthenticated user on protected route - redirecting to /auth');
      router.replace(loginUrl || '/auth');
      return;
    }

    // Rule 3: Allow access to current route
    console.log('✅ Route access granted');
  }, [router, authenticated, checked, loginUrl]);

  // Show loading while auth check is in progress
  if (!checked) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Render children if routing rules allow
  return <>{children}</>;
};

export default RouteGuard;
