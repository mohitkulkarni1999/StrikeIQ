import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { DashboardResponse, isAuthRequired, AuthRequiredData, MarketData } from '../types/dashboard';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastCheck: number;
  mode: 'NORMAL' | 'AUTH';
  loginUrl: string | null;
}

type AuthAction = 
  | { type: 'AUTH_CHECK_START' }
  | { type: 'AUTH_CHECK_SUCCESS'; isAuthenticated: boolean }
  | { type: 'AUTH_CHECK_ERROR'; error: string }
  | { type: 'AUTH_REQUIRED'; payload: { login_url: string } }
  | { type: 'AUTH_SUCCESS'; isAuthenticated: true };

const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: true,
  error: null,
  lastCheck: Date.now(),
  mode: 'NORMAL',
  loginUrl: null,
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

  const checkAuth = async () => {
    // Don't check if already in auth required state
    if (!state.isAuthenticated) return;
    
    dispatch({ type: 'AUTH_CHECK_START' });
    
    try {
      const response = await fetch('/api/dashboard/NIFTY');
      const data: DashboardResponse = await response.json();
      
      if (isAuthRequired(data)) {
        dispatch({ type: 'AUTH_REQUIRED', payload: { login_url: data.login_url } });
      } else {
        dispatch({ type: 'AUTH_CHECK_SUCCESS', isAuthenticated: true });
      }
    } catch (error) {
      dispatch({ type: 'AUTH_CHECK_ERROR', error: error instanceof Error ? error.message : 'Unknown error' });
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

  // Check auth on mount only
  useEffect(() => {
    checkAuth();
  }, []); // Empty dependency array - only run once

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
