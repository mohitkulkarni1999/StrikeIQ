import React, { createContext, useContext, useReducer, useEffect, useRef, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import api from '../api/axios';
import { DashboardResponse, isAuthRequired, AuthRequiredData, MarketData } from '@/types/dashboard';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastCheck: number;
  mode: 'NORMAL' | 'AUTH';
  loginUrl: string | null;
  backendStatus: "unknown" | "online" | "offline";
}

type AuthAction =
  | { type: 'AUTH_CHECK_START' }
  | { type: 'AUTH_CHECK_SUCCESS'; isAuthenticated: boolean }
  | { type: 'AUTH_CHECK_ERROR'; error: string }
  | { type: 'AUTH_REQUIRED'; payload: { login_url: string } }
  | { type: 'AUTH_SUCCESS'; isAuthenticated: true }
  | { type: 'AUTH_CHECK_COMPLETE' }
  | { type: 'BACKEND_ONLINE' }
  | { type: 'BACKEND_OFFLINE' };

const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: true,
  error: null,
  lastCheck: Date.now(),
  mode: 'NORMAL',
  loginUrl: null,
  backendStatus: "unknown",
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'AUTH_CHECK_START':
      return { ...state, isLoading: true, error: null };

    case 'AUTH_CHECK_SUCCESS':
      return {
        ...state,
        isAuthenticated: action.isAuthenticated,
        isLoading: false,
        error: null,
        lastCheck: Date.now(),
      };

    case 'AUTH_CHECK_ERROR':
      return {
        ...state,
        isAuthenticated: false,
        isLoading: false,
        error: action.error,
        lastCheck: Date.now(),
      };

    case 'AUTH_REQUIRED':
      return {
        ...state,
        isAuthenticated: false,
        isLoading: false,
        error: 'Authentication required',
        lastCheck: Date.now(),
        mode: 'AUTH',
        loginUrl: action.payload.login_url,
      };

    case 'AUTH_SUCCESS':
      return {
        ...state,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        lastCheck: Date.now(),
      };

    case 'AUTH_CHECK_COMPLETE':
      return {
        ...state,
        isLoading: false,
      };

    case 'BACKEND_ONLINE':
      return {
        ...state,
        backendStatus: "online",
      };

    case 'BACKEND_OFFLINE':
      return {
        ...state,
        backendStatus: "offline",
      };

    default:
      return state;
  }
}

interface AuthContextType {
  state: AuthState;
  dispatch: React.Dispatch<AuthAction>;
  checkAuth: () => Promise<void>;
  handleAuthRequired: (authData: AuthRequiredData) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const isCheckingAuth = useRef(false);
  const router = useRouter();
  const pathname = usePathname();

  // Listen for auth status updates from polling
  useEffect(() => {
    console.log('🎧 AuthContext: Setting up event listeners');

    const handleAuthRequired = (event: CustomEvent) => {
      console.log('🚫 AuthContext: Received authRequired event', event.detail);
      const { login_url } = event.detail;
      dispatch({ type: 'AUTH_REQUIRED', payload: { login_url } });
    };

    const handleAuthSuccess = () => {
      console.log('✅ AuthContext: Received authSuccess event');
      dispatch({ type: 'AUTH_SUCCESS', isAuthenticated: true });
    };

    const handleBackendOnline = () => {
      console.log('🌐 AuthContext: Backend is online');
      dispatch({ type: 'BACKEND_ONLINE' });
    };

    const handleBackendOffline = () => {
      console.log('🔌 AuthContext: Backend is offline');
      dispatch({ type: 'BACKEND_OFFLINE' });
    };

    window.addEventListener('authRequired', handleAuthRequired as EventListener);
    window.addEventListener('authSuccess', handleAuthSuccess);
    window.addEventListener('backend-online', handleBackendOnline);
    window.addEventListener('backend-offline', handleBackendOffline);

    // Skip auth check if on auth page
    if (pathname?.startsWith('/auth')) {
      console.log("On auth page → skipping auth check");
      dispatch({ type: 'AUTH_CHECK_COMPLETE' });
    } else {
      // Initial auth check
      checkAuth();
    }

    console.log('✅ AuthContext: Event listeners set up and initial check started');

    return () => {
      console.log('🧹 AuthContext: Cleaning up event listeners');
      window.removeEventListener('authRequired', handleAuthRequired as EventListener);
      window.removeEventListener('authSuccess', handleAuthSuccess);
      window.removeEventListener('backend-online', handleBackendOnline);
      window.removeEventListener('backend-offline', handleBackendOffline);
    };
  }, [pathname]);

  const checkAuth = async () => {
    // Prevent duplicate checks
    if (isCheckingAuth.current) {
      console.log('🔄 Auth check already in progress, skipping');
      return;
    }

    // TODO: REMOVE AFTER MARKET TESTING
    // TEMPORARY MARKET TEST BYPASS
    console.log('🔓 TEMPORARY AUTH BYPASS FOR MARKET TESTING');
    dispatch({ type: 'BACKEND_ONLINE' });
    dispatch({ type: 'AUTH_CHECK_SUCCESS', isAuthenticated: true });
    dispatch({ type: 'AUTH_CHECK_COMPLETE' });
    return;

    isCheckingAuth.current = true;
    dispatch({ type: 'AUTH_CHECK_START' });

    try {
      // Check auth status using the dedicated endpoint
      const response = await api.get('/api/v1/auth/status');
      
      // Backend is online
      dispatch({ type: 'BACKEND_ONLINE' });
      
      if (response.data.authenticated) {
        dispatch({ type: 'AUTH_CHECK_SUCCESS', isAuthenticated: true });
      } else {
        // Not authenticated, check if login_url is provided
        if (response.data.login_url) {
          console.log("Auth required, redirecting to OAuth");
          window.location.href = response.data.login_url;
        } else {
          console.warn("Auth required but no login URL provided");
          dispatch({ type: 'AUTH_CHECK_ERROR', error: 'Authentication required' });
          router.replace('/auth');
        }
        return;
      }
    } catch (error: any) {
      // Handle network errors (no response)
      if (!error.response) {
        console.warn("Backend unreachable");
        dispatch({ type: 'BACKEND_OFFLINE' });
        dispatch({ type: 'AUTH_CHECK_ERROR', error: 'Backend unreachable' });
        return;
      }
      
      // Handle other server errors (503, etc.)
      console.warn("Backend server error");
      dispatch({ type: 'BACKEND_OFFLINE' });
      dispatch({ type: 'AUTH_CHECK_ERROR', error: 'Backend server error' });
    } finally {
      isCheckingAuth.current = false;
    }
  };

  const handleAuthRequired = (authData: AuthRequiredData) => {
    // Prevent redundant setState calls
    if (!state.isAuthenticated && !state.isLoading) {
      return; // Already in auth required state
    }

    dispatch({ type: 'AUTH_REQUIRED', payload: { login_url: authData.login_url } });
    // Stop any polling here
    console.log('Authentication required, stopping polling');
  };

  const value: AuthContextType = {
    state,
    dispatch,
    checkAuth,
    handleAuthRequired,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
