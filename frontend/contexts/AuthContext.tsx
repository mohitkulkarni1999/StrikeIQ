import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import { DashboardResponse, isAuthRequired, AuthRequiredData, MarketData } from '../types/dashboard';

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastCheck: number;
}

type AuthAction = 
  | { type: 'AUTH_CHECK_START' }
  | { type: 'AUTH_CHECK_SUCCESS'; isAuthenticated: boolean }
  | { type: 'AUTH_CHECK_ERROR'; error: string }
  | { type: 'AUTH_REQUIRED' }
  | { type: 'AUTH_SUCCESS'; isAuthenticated: true };

const initialState: AuthState = {
  isAuthenticated: false,
  isLoading: true,
  error: null,
  lastCheck: Date.now(),
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
    dispatch({ type: 'AUTH_CHECK_START' });
    
    try {
      const response = await fetch('/api/dashboard/NIFTY');
      const data: DashboardResponse = await response.json();
      
      if (isAuthRequired(data)) {
        dispatch({ type: 'AUTH_REQUIRED' });
      } else {
        dispatch({ type: 'AUTH_CHECK_SUCCESS', isAuthenticated: true });
      }
    } catch (error) {
      dispatch({ type: 'AUTH_CHECK_ERROR', error: error instanceof Error ? error.message : 'Unknown error' });
    }
  };

  const handleAuthRequired = (authData: AuthRequiredData) => {
    dispatch({ type: 'AUTH_REQUIRED' });
    // Stop any polling here
    console.log('Authentication required, stopping polling');
  };

  // Check auth on mount and periodically
  useEffect(() => {
    checkAuth();
    
    const interval = setInterval(() => {
      // Only check if not currently loading
      if (!state.isLoading) {
        checkAuth();
      }
    }, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, []);

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
