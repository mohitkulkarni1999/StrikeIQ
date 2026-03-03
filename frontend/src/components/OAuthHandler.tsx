import { useEffect } from 'react';

interface OAuthHandlerProps {
  onAuthSuccess: () => void;
}

export default function OAuthHandler({ onAuthSuccess }: OAuthHandlerProps) {
  useEffect(() => {
    // Check if we're returning from Upstox OAuth with success
    const urlParams = new URLSearchParams(window.location.search);
    const authStatus = urlParams.get('status');
    const upstoxStatus = urlParams.get('upstox');
    
    // Check for either status=success or upstox=connected
    const isSuccess = authStatus === 'success' || upstoxStatus === 'connected';
    
    if (isSuccess && window.location.pathname.includes('/auth/success')) {
      console.log('OAuth success detected, triggering auth refresh immediately');
      
      // SECURITY: No state validation needed - backend handles it
      // Clean up any stored data
      sessionStorage.removeItem('oauth_state');
      sessionStorage.removeItem('upstox_auth_url');
      
      // Trigger auth success callback immediately
      onAuthSuccess();
      
      // NO REDIRECT HERE - Let RouteGuard handle navigation
    }
  }, [onAuthSuccess]);

  return null; // This component doesn't render anything
}
