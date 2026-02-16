module.exports = [
"[externals]/react/jsx-dev-runtime [external] (react/jsx-dev-runtime, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("react/jsx-dev-runtime", () => require("react/jsx-dev-runtime"));

module.exports = mod;
}),
"[externals]/react [external] (react, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("react", () => require("react"));

module.exports = mod;
}),
"[project]/types/dashboard.ts [ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "isAuthRequired",
    ()=>isAuthRequired,
    "isMarketData",
    ()=>isMarketData,
    "isRateLimit",
    ()=>isRateLimit
]);
function isAuthRequired(data) {
    return 'session_type' in data && data.session_type === 'AUTH_REQUIRED';
}
function isRateLimit(data) {
    return 'session_type' in data && data.session_type === 'RATE_LIMIT';
}
function isMarketData(data) {
    return !isAuthRequired(data) && !isRateLimit(data);
}
}),
"[project]/contexts/AuthContext.tsx [ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "AuthProvider",
    ()=>AuthProvider,
    "useAuth",
    ()=>useAuth
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$react$2f$jsx$2d$dev$2d$runtime__$5b$external$5d$__$28$react$2f$jsx$2d$dev$2d$runtime$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/react/jsx-dev-runtime [external] (react/jsx-dev-runtime, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$react__$5b$external$5d$__$28$react$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/react [external] (react, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$types$2f$dashboard$2e$ts__$5b$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/types/dashboard.ts [ssr] (ecmascript)");
;
;
;
const initialState = {
    isAuthenticated: false,
    isLoading: true,
    error: null,
    lastCheck: Date.now(),
    mode: 'NORMAL',
    loginUrl: null
};
function authReducer(state, action) {
    switch(action.type){
        case 'AUTH_CHECK_START':
            return {
                ...state,
                isLoading: true,
                error: null
            };
        case 'AUTH_CHECK_SUCCESS':
            return {
                ...state,
                isAuthenticated: action.isAuthenticated,
                isLoading: false,
                error: null,
                lastCheck: Date.now()
            };
        case 'AUTH_CHECK_ERROR':
            return {
                ...state,
                isAuthenticated: false,
                isLoading: false,
                error: action.error,
                lastCheck: Date.now()
            };
        case 'AUTH_REQUIRED':
            return {
                ...state,
                isAuthenticated: false,
                isLoading: false,
                error: 'Authentication required',
                lastCheck: Date.now(),
                mode: 'AUTH',
                loginUrl: action.payload.login_url
            };
        case 'AUTH_SUCCESS':
            return {
                ...state,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                lastCheck: Date.now()
            };
        default:
            return state;
    }
}
const AuthContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$externals$5d2f$react__$5b$external$5d$__$28$react$2c$__cjs$29$__["createContext"])(undefined);
function AuthProvider({ children }) {
    const [state, dispatch] = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$react__$5b$external$5d$__$28$react$2c$__cjs$29$__["useReducer"])(authReducer, initialState);
    const checkAuth = async ()=>{
        // Always check auth status, regardless of current state
        dispatch({
            type: 'AUTH_CHECK_START'
        });
        try {
            const response = await fetch('/api/dashboard/NIFTY');
            const data = await response.json();
            if ((0, __TURBOPACK__imported__module__$5b$project$5d2f$types$2f$dashboard$2e$ts__$5b$ssr$5d$__$28$ecmascript$29$__["isAuthRequired"])(data)) {
                dispatch({
                    type: 'AUTH_REQUIRED',
                    payload: {
                        login_url: data.login_url
                    }
                });
            } else {
                dispatch({
                    type: 'AUTH_CHECK_SUCCESS',
                    isAuthenticated: true
                });
            }
        } catch (error) {
            dispatch({
                type: 'AUTH_CHECK_ERROR',
                error: error instanceof Error ? error.message : 'Unknown error'
            });
        }
    };
    const handleAuthRequired = (authData)=>{
        // Prevent redundant setState calls
        if (!state.isAuthenticated && !state.isLoading) {
            return; // Already in auth required state
        }
        dispatch({
            type: 'AUTH_REQUIRED',
            payload: {
                login_url: authData.login_url
            }
        });
        // Stop any polling here
        console.log('Authentication required, stopping polling');
    };
    // Listen for auth status updates from polling
    (0, __TURBOPACK__imported__module__$5b$externals$5d2f$react__$5b$external$5d$__$28$react$2c$__cjs$29$__["useEffect"])(()=>{
        console.log('🎧 AuthContext: Setting up event listeners');
        const handleAuthRequired = (event)=>{
            console.log('🚫 AuthContext: Received authRequired event', event.detail);
            const { login_url } = event.detail;
            dispatch({
                type: 'AUTH_REQUIRED',
                payload: {
                    login_url
                }
            });
        };
        const handleAuthSuccess = ()=>{
            console.log('✅ AuthContext: Received authSuccess event');
            dispatch({
                type: 'AUTH_SUCCESS',
                isAuthenticated: true
            });
        };
        window.addEventListener('authRequired', handleAuthRequired);
        window.addEventListener('authSuccess', handleAuthSuccess);
        console.log('✅ AuthContext: Event listeners set up');
        return ()=>{
            console.log('🧹 AuthContext: Cleaning up event listeners');
            window.removeEventListener('authRequired', handleAuthRequired);
            window.removeEventListener('authSuccess', handleAuthSuccess);
        };
    }, []);
    const value = {
        state,
        dispatch,
        checkAuth,
        handleAuthRequired
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$externals$5d2f$react$2f$jsx$2d$dev$2d$runtime__$5b$external$5d$__$28$react$2f$jsx$2d$dev$2d$runtime$2c$__cjs$29$__["jsxDEV"])(AuthContext.Provider, {
        value: value,
        children: children
    }, void 0, false, {
        fileName: "[project]/contexts/AuthContext.tsx",
        lineNumber: 156,
        columnNumber: 10
    }, this);
}
function useAuth() {
    const context = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$react__$5b$external$5d$__$28$react$2c$__cjs$29$__["useContext"])(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
}),
"[project]/pages/_app.tsx [ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>__TURBOPACK__default__export__
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$react$2f$jsx$2d$dev$2d$runtime__$5b$external$5d$__$28$react$2f$jsx$2d$dev$2d$runtime$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/react/jsx-dev-runtime [external] (react/jsx-dev-runtime, cjs)");
var __TURBOPACK__imported__module__$5b$externals$5d2f$react__$5b$external$5d$__$28$react$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/react [external] (react, cjs)");
var __TURBOPACK__imported__module__$5b$project$5d2f$contexts$2f$AuthContext$2e$tsx__$5b$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/contexts/AuthContext.tsx [ssr] (ecmascript)");
;
;
;
;
function MyApp({ Component, pageProps }) {
    (0, __TURBOPACK__imported__module__$5b$externals$5d2f$react__$5b$external$5d$__$28$react$2c$__cjs$29$__["useEffect"])(()=>{
        // Apply dark mode by default
        document.documentElement.classList.add('dark');
        // � AUTH EXPIRY LISTENER
        const handleAuthExpired = ()=>{
            console.warn('🔐 Auth expired event received - redirecting to /auth');
            // Clear any stored auth data
            localStorage.removeItem("upstox_auth");
            sessionStorage.removeItem("upstox_auth");
            // Redirect to auth screen
            window.location.href = "/auth";
        };
        // Add global event listener for auth expiry
        window.addEventListener("auth-expired", handleAuthExpired);
        // �🔍 GLOBAL REST CALL INTERCEPTOR FOR AUDIT
        const originalFetch = window.fetch;
        window.fetch = async (...args)=>{
            console.log("🌐 REST CALL DETECTED:", args[0]);
            console.log("🌐 REST METHOD:", args[1]?.method || 'GET');
            console.log("🌐 REST TIMESTAMP:", new Date().toISOString());
            const start = performance.now();
            const response = await originalFetch(...args);
            const duration = performance.now() - start;
            console.log("🌐 REST STATUS:", response.status);
            console.log("🌐 REST DURATION:", `${duration.toFixed(2)}ms`);
            return response;
        };
        // 🔍 AXIOS INTERCEPTOR (if axios is used)
        if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
        ;
        console.log("🔍 REST/WINDOW INTERCEPTORS INSTALLED");
        // Cleanup on unmount
        return ()=>{
            window.removeEventListener("auth-expired", handleAuthExpired);
        };
    }, []);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$externals$5d2f$react$2f$jsx$2d$dev$2d$runtime__$5b$external$5d$__$28$react$2f$jsx$2d$dev$2d$runtime$2c$__cjs$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$contexts$2f$AuthContext$2e$tsx__$5b$ssr$5d$__$28$ecmascript$29$__["AuthProvider"], {
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$externals$5d2f$react$2f$jsx$2d$dev$2d$runtime__$5b$external$5d$__$28$react$2f$jsx$2d$dev$2d$runtime$2c$__cjs$29$__["jsxDEV"])(Component, {
            ...pageProps
        }, void 0, false, {
            fileName: "[project]/pages/_app.tsx",
            lineNumber: 61,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/pages/_app.tsx",
        lineNumber: 60,
        columnNumber: 5
    }, this);
}
const __TURBOPACK__default__export__ = MyApp;
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__0cda883f._.js.map