import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import { useAuth } from '../../contexts/AuthContext'
import { useWebSocket } from '../../contexts/WebSocketContext'
import OAuthHandler from '../../components/OAuthHandler'
import api from '../../api/axios'

export default function AuthSuccess() {
  const router = useRouter()
  const { checkAuth } = useAuth()
  const { connect } = useWebSocket()
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const authStatus = urlParams.get('status')
    const upstoxStatus = urlParams.get('upstox')
    
    // Check for either status=success or upstox=connected
    const isSuccess = authStatus === 'success' || upstoxStatus === 'connected'
    
    setStatus(isSuccess ? 'success' : 'unknown')
    
    // If auth successful, trigger WebSocket init and redirect
    if (isSuccess) {
      console.log('OAuth success detected, initializing WebSocket')
      
      // Initialize WebSocket connection
      const initWebSocket = async () => {
        try {
          console.log('Calling WS init API...')
          const response = await api.get('/api/ws/init')
          console.log('WS init successful:', response.data)
          
          // Connect to WebSocket for NIFTY with current expiry
          // Use today's date or next Thursday as expiry
          const today = new Date()
          const expiry = new Date(today)
          const daysUntilThursday = (4 - today.getDay() + 7) % 7 || 7
          expiry.setDate(today.getDate() + daysUntilThursday)
          const expiryStr = expiry.toISOString().split('T')[0]
          
          console.log(`Connecting to WebSocket for NIFTY with expiry ${expiryStr}`)
          await connect('NIFTY', expiryStr)
          
          // Trigger auth context refresh
          await checkAuth()
          
          // Redirect to dashboard after short delay
          setTimeout(() => {
            router.push('/')
          }, 500)
        } catch (error) {
          console.error('WS init failed:', error)
          setStatus('error')
        }
      }
      
      initWebSocket()
    }
  }, [router, checkAuth, connect])

  return (
    <>
      <Head>
        <title>Authentication Status - StrikeIQ</title>
        <meta name="description" content="Upstox authentication status" />
      </Head>
      
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <OAuthHandler onAuthSuccess={() => {
            setStatus('success');
            setTimeout(() => {
              checkAuth().then(() => {
                router.push('/')
              })
            }, 1000);
          }} />
          {status === 'success' ? (
            <>
              <div className="mb-8">
                <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h1 className="text-3xl font-bold text-white mb-2">Authentication Successful!</h1>
                <p className="text-gray-300 mb-4">Your Upstox account has been connected successfully</p>
                <p className="text-sm text-gray-400">Redirecting to dashboard...</p>
              </div>
              
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto"></div>
            </>
          ) : (
            <>
              <div className="mb-8">
                <div className="w-20 h-20 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <h1 className="text-3xl font-bold text-white mb-2">Authentication Failed</h1>
                <p className="text-gray-300">There was an issue connecting your Upstox account</p>
              </div>
              
              <button
                onClick={() => router.push('/')}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-lg transition-colors"
              >
                Try Again
              </button>
            </>
          )}
        </div>
      </div>
    </>
  )
}
