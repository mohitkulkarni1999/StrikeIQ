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
      console.log('OAuth success detected, triggering auth refresh');
      // Clean up any stored auth URL
      sessionStorage.removeItem('upstox_auth_url');
      
      // Trigger auth success callback
      setTimeout(() => {
        onAuthSuccess();
      }, 100);
    }
  }, [onAuthSuccess]);

  return null; // This component doesn't render anything
}
