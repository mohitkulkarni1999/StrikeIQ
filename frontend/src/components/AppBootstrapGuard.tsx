import { useAuth } from "../contexts/AuthContext";
import AuthScreen from "./AuthScreen";

export default function AppBootstrapGuard({ children }: { children: React.ReactNode }) {
    const { state } = useAuth();
    const { isLoading, mode, loginUrl } = state;

    console.log("🛡️ AppBootstrapGuard State:", { isLoading, mode, hasLoginUrl: !!loginUrl });

    if (isLoading) {
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
