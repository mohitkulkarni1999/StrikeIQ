import { useEffect } from 'react';

interface OAuthHandlerProps {
  onAuthSuccess: () => void;
}

export default function OAuthHandler({ onAuthSuccess }: OAuthHandlerProps) {
  useEffect(() => {
    // Check if we're returning from Upstox OAuth with success
    const urlParams = new URLSearchParams(window.location.search);
    const authStatus = urlParams.get('status');
    
    if (authStatus === 'success' && window.location.pathname.includes('/auth/success')) {
      console.log('OAuth success detected, triggering auth refresh immediately');
      
      // SECURITY: No state validation needed - backend handles it
      // Clean up any stored data
      sessionStorage.removeItem('oauth_state');
      sessionStorage.removeItem('upstox_auth_url');
      
      // Trigger auth success callback immediately
      onAuthSuccess();
      
      // Then redirect to dashboard after a short delay
      setTimeout(() => {
        window.location.href = '/';
      }, 500);
    }
  }, [onAuthSuccess]);

  return null; // This component doesn't render anything
}
