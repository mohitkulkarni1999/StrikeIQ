import { useAuth } from "../contexts/AuthContext";
import AuthScreen from "./AuthScreen";
import { useState, useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import axios from "axios";

export default function AppBootstrapGuard({ children }: { children: React.ReactNode }) {
    const { state, dispatch } = useAuth();
    const { isLoading, mode, loginUrl, backendStatus } = state;
    const [isClient, setIsClient] = useState(false);
    const [showConnectionRestored, setShowConnectionRestored] = useState(false);
    const [previousBackendStatus, setPreviousBackendStatus] = useState(backendStatus);
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const pathname = usePathname();

    // Set client flag
    useEffect(() => {
        setIsClient(true);
    }, []);

    // Skip all bootstrap logic on auth routes
    useEffect(() => {
        if (pathname?.startsWith('/auth')) {
            console.log("Auth route → marking bootstrap complete");
            
            dispatch({ type: 'AUTH_CHECK_COMPLETE' });
            
            return;
        }
    }, [pathname]);

    // Handle backend status changes (only run when not on auth routes)
    useEffect(() => {
        if (pathname?.startsWith('/auth')) return;
        
        if (previousBackendStatus === "offline" && backendStatus === "online") {
            setShowConnectionRestored(true);
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        }
        setPreviousBackendStatus(backendStatus);
    }, [backendStatus, previousBackendStatus, pathname]);

    // Backend recovery polling logic (only run when not on auth routes)
    useEffect(() => {
        if (pathname?.startsWith('/auth')) return;
        
        // Start polling only when backend is offline
        if (backendStatus === "offline") {
            console.log("🔄 Starting backend recovery polling...");
            
            // Prevent multiple polling loops
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }
            
            const checkBackendHealth = async () => {
                try {
                    console.log("🔍 Checking backend health...");
                    
                    // Use environment-based API base URL with fallback
                    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                    const response = await axios.get(`${API_BASE}/health`);
                    
                    if (response.status === 200) {
                        console.log("✅ Backend is back online!");
                        
                        // Dispatch backend-online event
                        window.dispatchEvent(new CustomEvent("backend-online"));
                        
                        // Stop polling
                        if (pollingIntervalRef.current) {
                            clearInterval(pollingIntervalRef.current);
                            pollingIntervalRef.current = null;
                        }
                    }
                } catch (error) {
                    console.log("❌ Backend still offline, continuing polling...");
                    // Continue polling on failure
                }
            };
            
            // Start polling every 10 seconds
            pollingIntervalRef.current = setInterval(checkBackendHealth, 10000);
            
            // Check immediately on start
            checkBackendHealth();
        } else {
            // Stop polling when backend is online or unknown
            if (pollingIntervalRef.current) {
                console.log("🛑 Stopping backend recovery polling");
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        }
        
        // Cleanup on unmount
        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
                pollingIntervalRef.current = null;
            }
        };
    }, [backendStatus, pathname]);

    console.log("🛡️ AppBootstrapGuard State:", { isLoading, mode, hasLoginUrl: !!loginUrl, backendStatus, isClient });

    // During SSR, return static placeholder to prevent hydration mismatch
    if (!isClient) {
        return (
            <div className="w-screen h-screen flex flex-col items-center justify-center bg-slate-900 text-white">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
                <div className="space-y-2 text-center">
                    <p className="text-xl font-bold tracking-widest text-blue-400">STRIKE IQ</p>
                    <p className="text-slate-400 font-mono text-sm animate-pulse uppercase">Loading...</p>
                </div>
            </div>
        );
    }

    // Show splash screen only when loading (not based on backendStatus)
    if (isLoading && !pathname?.startsWith('/auth')) {
        return (
            <div className="w-screen h-screen flex flex-col items-center justify-center bg-slate-900 text-white">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
                <div className="space-y-2 text-center">
                    <p className="text-xl font-bold tracking-widest text-blue-400">STRIKE IQ</p>
                    <p className="text-slate-400 font-mono text-sm animate-pulse uppercase">Synchronizing Neural Market State...</p>
                </div>
            </div>
        );
    }

    // Show connection restored state
    if (showConnectionRestored) {
        return (
            <div className="w-screen h-screen flex flex-col items-center justify-center" style={{ backgroundColor: '#0B0F19' }}>
                <div className="relative mb-8">
                    <div className="w-20 h-20 rounded-full flex items-center justify-center" style={{ backgroundColor: 'rgba(34, 197, 94, 0.1)' }}>
                        <svg className="w-12 h-12" style={{ color: '#22C55E' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                </div>
                <div className="space-y-3 text-center">
                    <p className="text-2xl font-semibold text-gray-200">Connection Restored</p>
                    <p className="text-base text-green-400">✓ Live market feed active</p>
                </div>
            </div>
        );
    }

    // Show offline state when backend is unavailable
    if (backendStatus === "offline") {
        return (
            <div className="w-screen h-screen flex flex-col items-center justify-center relative overflow-hidden" style={{ backgroundColor: '#0B0F19' }}>
                {/* Visible radial gradient background for depth */}
                <div className="absolute inset-0" style={{
                    background: 'radial-gradient(circle at center, rgba(239,68,68,0.12) 0%, transparent 60%)'
                }}></div>
                
                <div className="relative z-10 mb-8">
                    <div 
                        className="w-20 h-20 rounded-full flex items-center justify-center transition-all duration-1800 ease-in-out"
                        style={{ 
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            boxShadow: '0 0 60px rgba(248,113,113,0.25)',
                            animation: 'breathe 1.8s ease-in-out infinite'
                        }}
                    >
                        <svg className="w-16 h-16" style={{ color: '#F87171' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6" />
                        </svg>
                    </div>
                </div>
                <div className="relative z-10 space-y-4 text-center">
                    <p className="text-3xl font-semibold text-gray-200" style={{ letterSpacing: '0.5px' }}>Connection Lost</p>
                    <p className="text-lg text-gray-300">Reconnecting to live market feed...</p>
                    <p className="text-sm text-gray-400">Auto-retrying...</p>
                </div>
                <div className="relative z-10 mt-8 flex items-center gap-3">
                    <div className="w-3 h-3 bg-gray-500 rounded-full animate-pulse"></div>
                    <div className="w-3 h-3 bg-gray-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    <div className="w-3 h-3 bg-gray-500 rounded-full animate-pulse" style={{ animationDelay: '0.8s' }}></div>
                </div>
                
                {/* Enhanced breathing animation */}
                <style jsx>{`
                    @keyframes breathe {
                        0%, 100% { 
                            transform: scale(1); 
                            opacity: 0.7; 
                        }
                        50% { 
                            transform: scale(1.08); 
                            opacity: 1; 
                        }
                    }
                `}</style>
            </div>
        );
    }

    if (isLoading && !pathname?.startsWith('/auth')) {
        return (
            <div className="w-screen h-screen flex flex-col items-center justify-center bg-slate-900 text-white">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
                <div className="space-y-2 text-center">
                    <p className="text-xl font-bold tracking-widest text-blue-400">STRIKE IQ</p>
                    <p className="text-slate-400 font-mono text-sm animate-pulse uppercase">Synchronizing Neural Market State...</p>
                </div>
            </div>
        );
    }

    if (mode === 'AUTH' && loginUrl) {
        return (
            <AuthScreen
                authData={{
                    session_type: 'AUTH_REQUIRED',
                    mode: 'AUTH',
                    login_url: loginUrl,
                    message: 'Your Upstox session has expired or requires authorization. Please reconnect to continue receiving live market intelligence.',
                    timestamp: new Date().toISOString()
                }}
            />
        );
    }

    return <>{children}</>;
}
