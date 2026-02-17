(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[turbopack]/browser/dev/hmr-client/hmr-client.ts [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

/// <reference path="../../../shared/runtime-types.d.ts" />
/// <reference path="../../runtime/base/dev-globals.d.ts" />
/// <reference path="../../runtime/base/dev-protocol.d.ts" />
/// <reference path="../../runtime/base/dev-extensions.ts" />
__turbopack_context__.s([
    "connect",
    ()=>connect,
    "setHooks",
    ()=>setHooks,
    "subscribeToUpdate",
    ()=>subscribeToUpdate
]);
function connect({ addMessageListener, sendMessage, onUpdateError = console.error }) {
    addMessageListener((msg)=>{
        switch(msg.type){
            case 'turbopack-connected':
                handleSocketConnected(sendMessage);
                break;
            default:
                try {
                    if (Array.isArray(msg.data)) {
                        for(let i = 0; i < msg.data.length; i++){
                            handleSocketMessage(msg.data[i]);
                        }
                    } else {
                        handleSocketMessage(msg.data);
                    }
                    applyAggregatedUpdates();
                } catch (e) {
                    console.warn('[Fast Refresh] performing full reload\n\n' + "Fast Refresh will perform a full reload when you edit a file that's imported by modules outside of the React rendering tree.\n" + 'You might have a file which exports a React component but also exports a value that is imported by a non-React component file.\n' + 'Consider migrating the non-React component export to a separate file and importing it into both files.\n\n' + 'It is also possible the parent component of the component you edited is a class component, which disables Fast Refresh.\n' + 'Fast Refresh requires at least one parent function component in your React tree.');
                    onUpdateError(e);
                    location.reload();
                }
                break;
        }
    });
    const queued = globalThis.TURBOPACK_CHUNK_UPDATE_LISTENERS;
    if (queued != null && !Array.isArray(queued)) {
        throw new Error('A separate HMR handler was already registered');
    }
    globalThis.TURBOPACK_CHUNK_UPDATE_LISTENERS = {
        push: ([chunkPath, callback])=>{
            subscribeToChunkUpdate(chunkPath, sendMessage, callback);
        }
    };
    if (Array.isArray(queued)) {
        for (const [chunkPath, callback] of queued){
            subscribeToChunkUpdate(chunkPath, sendMessage, callback);
        }
    }
}
const updateCallbackSets = new Map();
function sendJSON(sendMessage, message) {
    sendMessage(JSON.stringify(message));
}
function resourceKey(resource) {
    return JSON.stringify({
        path: resource.path,
        headers: resource.headers || null
    });
}
function subscribeToUpdates(sendMessage, resource) {
    sendJSON(sendMessage, {
        type: 'turbopack-subscribe',
        ...resource
    });
    return ()=>{
        sendJSON(sendMessage, {
            type: 'turbopack-unsubscribe',
            ...resource
        });
    };
}
function handleSocketConnected(sendMessage) {
    for (const key of updateCallbackSets.keys()){
        subscribeToUpdates(sendMessage, JSON.parse(key));
    }
}
// we aggregate all pending updates until the issues are resolved
const chunkListsWithPendingUpdates = new Map();
function aggregateUpdates(msg) {
    const key = resourceKey(msg.resource);
    let aggregated = chunkListsWithPendingUpdates.get(key);
    if (aggregated) {
        aggregated.instruction = mergeChunkListUpdates(aggregated.instruction, msg.instruction);
    } else {
        chunkListsWithPendingUpdates.set(key, msg);
    }
}
function applyAggregatedUpdates() {
    if (chunkListsWithPendingUpdates.size === 0) return;
    hooks.beforeRefresh();
    for (const msg of chunkListsWithPendingUpdates.values()){
        triggerUpdate(msg);
    }
    chunkListsWithPendingUpdates.clear();
    finalizeUpdate();
}
function mergeChunkListUpdates(updateA, updateB) {
    let chunks;
    if (updateA.chunks != null) {
        if (updateB.chunks == null) {
            chunks = updateA.chunks;
        } else {
            chunks = mergeChunkListChunks(updateA.chunks, updateB.chunks);
        }
    } else if (updateB.chunks != null) {
        chunks = updateB.chunks;
    }
    let merged;
    if (updateA.merged != null) {
        if (updateB.merged == null) {
            merged = updateA.merged;
        } else {
            // Since `merged` is an array of updates, we need to merge them all into
            // one, consistent update.
            // Since there can only be `EcmascriptMergeUpdates` in the array, there is
            // no need to key on the `type` field.
            let update = updateA.merged[0];
            for(let i = 1; i < updateA.merged.length; i++){
                update = mergeChunkListEcmascriptMergedUpdates(update, updateA.merged[i]);
            }
            for(let i = 0; i < updateB.merged.length; i++){
                update = mergeChunkListEcmascriptMergedUpdates(update, updateB.merged[i]);
            }
            merged = [
                update
            ];
        }
    } else if (updateB.merged != null) {
        merged = updateB.merged;
    }
    return {
        type: 'ChunkListUpdate',
        chunks,
        merged
    };
}
function mergeChunkListChunks(chunksA, chunksB) {
    const chunks = {};
    for (const [chunkPath, chunkUpdateA] of Object.entries(chunksA)){
        const chunkUpdateB = chunksB[chunkPath];
        if (chunkUpdateB != null) {
            const mergedUpdate = mergeChunkUpdates(chunkUpdateA, chunkUpdateB);
            if (mergedUpdate != null) {
                chunks[chunkPath] = mergedUpdate;
            }
        } else {
            chunks[chunkPath] = chunkUpdateA;
        }
    }
    for (const [chunkPath, chunkUpdateB] of Object.entries(chunksB)){
        if (chunks[chunkPath] == null) {
            chunks[chunkPath] = chunkUpdateB;
        }
    }
    return chunks;
}
function mergeChunkUpdates(updateA, updateB) {
    if (updateA.type === 'added' && updateB.type === 'deleted' || updateA.type === 'deleted' && updateB.type === 'added') {
        return undefined;
    }
    if (updateA.type === 'partial') {
        invariant(updateA.instruction, 'Partial updates are unsupported');
    }
    if (updateB.type === 'partial') {
        invariant(updateB.instruction, 'Partial updates are unsupported');
    }
    return undefined;
}
function mergeChunkListEcmascriptMergedUpdates(mergedA, mergedB) {
    const entries = mergeEcmascriptChunkEntries(mergedA.entries, mergedB.entries);
    const chunks = mergeEcmascriptChunksUpdates(mergedA.chunks, mergedB.chunks);
    return {
        type: 'EcmascriptMergedUpdate',
        entries,
        chunks
    };
}
function mergeEcmascriptChunkEntries(entriesA, entriesB) {
    return {
        ...entriesA,
        ...entriesB
    };
}
function mergeEcmascriptChunksUpdates(chunksA, chunksB) {
    if (chunksA == null) {
        return chunksB;
    }
    if (chunksB == null) {
        return chunksA;
    }
    const chunks = {};
    for (const [chunkPath, chunkUpdateA] of Object.entries(chunksA)){
        const chunkUpdateB = chunksB[chunkPath];
        if (chunkUpdateB != null) {
            const mergedUpdate = mergeEcmascriptChunkUpdates(chunkUpdateA, chunkUpdateB);
            if (mergedUpdate != null) {
                chunks[chunkPath] = mergedUpdate;
            }
        } else {
            chunks[chunkPath] = chunkUpdateA;
        }
    }
    for (const [chunkPath, chunkUpdateB] of Object.entries(chunksB)){
        if (chunks[chunkPath] == null) {
            chunks[chunkPath] = chunkUpdateB;
        }
    }
    if (Object.keys(chunks).length === 0) {
        return undefined;
    }
    return chunks;
}
function mergeEcmascriptChunkUpdates(updateA, updateB) {
    if (updateA.type === 'added' && updateB.type === 'deleted') {
        // These two completely cancel each other out.
        return undefined;
    }
    if (updateA.type === 'deleted' && updateB.type === 'added') {
        const added = [];
        const deleted = [];
        const deletedModules = new Set(updateA.modules ?? []);
        const addedModules = new Set(updateB.modules ?? []);
        for (const moduleId of addedModules){
            if (!deletedModules.has(moduleId)) {
                added.push(moduleId);
            }
        }
        for (const moduleId of deletedModules){
            if (!addedModules.has(moduleId)) {
                deleted.push(moduleId);
            }
        }
        if (added.length === 0 && deleted.length === 0) {
            return undefined;
        }
        return {
            type: 'partial',
            added,
            deleted
        };
    }
    if (updateA.type === 'partial' && updateB.type === 'partial') {
        const added = new Set([
            ...updateA.added ?? [],
            ...updateB.added ?? []
        ]);
        const deleted = new Set([
            ...updateA.deleted ?? [],
            ...updateB.deleted ?? []
        ]);
        if (updateB.added != null) {
            for (const moduleId of updateB.added){
                deleted.delete(moduleId);
            }
        }
        if (updateB.deleted != null) {
            for (const moduleId of updateB.deleted){
                added.delete(moduleId);
            }
        }
        return {
            type: 'partial',
            added: [
                ...added
            ],
            deleted: [
                ...deleted
            ]
        };
    }
    if (updateA.type === 'added' && updateB.type === 'partial') {
        const modules = new Set([
            ...updateA.modules ?? [],
            ...updateB.added ?? []
        ]);
        for (const moduleId of updateB.deleted ?? []){
            modules.delete(moduleId);
        }
        return {
            type: 'added',
            modules: [
                ...modules
            ]
        };
    }
    if (updateA.type === 'partial' && updateB.type === 'deleted') {
        // We could eagerly return `updateB` here, but this would potentially be
        // incorrect if `updateA` has added modules.
        const modules = new Set(updateB.modules ?? []);
        if (updateA.added != null) {
            for (const moduleId of updateA.added){
                modules.delete(moduleId);
            }
        }
        return {
            type: 'deleted',
            modules: [
                ...modules
            ]
        };
    }
    // Any other update combination is invalid.
    return undefined;
}
function invariant(_, message) {
    throw new Error(`Invariant: ${message}`);
}
const CRITICAL = [
    'bug',
    'error',
    'fatal'
];
function compareByList(list, a, b) {
    const aI = list.indexOf(a) + 1 || list.length;
    const bI = list.indexOf(b) + 1 || list.length;
    return aI - bI;
}
const chunksWithIssues = new Map();
function emitIssues() {
    const issues = [];
    const deduplicationSet = new Set();
    for (const [_, chunkIssues] of chunksWithIssues){
        for (const chunkIssue of chunkIssues){
            if (deduplicationSet.has(chunkIssue.formatted)) continue;
            issues.push(chunkIssue);
            deduplicationSet.add(chunkIssue.formatted);
        }
    }
    sortIssues(issues);
    hooks.issues(issues);
}
function handleIssues(msg) {
    const key = resourceKey(msg.resource);
    let hasCriticalIssues = false;
    for (const issue of msg.issues){
        if (CRITICAL.includes(issue.severity)) {
            hasCriticalIssues = true;
        }
    }
    if (msg.issues.length > 0) {
        chunksWithIssues.set(key, msg.issues);
    } else if (chunksWithIssues.has(key)) {
        chunksWithIssues.delete(key);
    }
    emitIssues();
    return hasCriticalIssues;
}
const SEVERITY_ORDER = [
    'bug',
    'fatal',
    'error',
    'warning',
    'info',
    'log'
];
const CATEGORY_ORDER = [
    'parse',
    'resolve',
    'code generation',
    'rendering',
    'typescript',
    'other'
];
function sortIssues(issues) {
    issues.sort((a, b)=>{
        const first = compareByList(SEVERITY_ORDER, a.severity, b.severity);
        if (first !== 0) return first;
        return compareByList(CATEGORY_ORDER, a.category, b.category);
    });
}
const hooks = {
    beforeRefresh: ()=>{},
    refresh: ()=>{},
    buildOk: ()=>{},
    issues: (_issues)=>{}
};
function setHooks(newHooks) {
    Object.assign(hooks, newHooks);
}
function handleSocketMessage(msg) {
    sortIssues(msg.issues);
    handleIssues(msg);
    switch(msg.type){
        case 'issues':
            break;
        case 'partial':
            // aggregate updates
            aggregateUpdates(msg);
            break;
        default:
            // run single update
            const runHooks = chunkListsWithPendingUpdates.size === 0;
            if (runHooks) hooks.beforeRefresh();
            triggerUpdate(msg);
            if (runHooks) finalizeUpdate();
            break;
    }
}
function finalizeUpdate() {
    hooks.refresh();
    hooks.buildOk();
    // This is used by the Next.js integration test suite to notify it when HMR
    // updates have been completed.
    // TODO: Only run this in test environments (gate by `process.env.__NEXT_TEST_MODE`)
    if (globalThis.__NEXT_HMR_CB) {
        globalThis.__NEXT_HMR_CB();
        globalThis.__NEXT_HMR_CB = null;
    }
}
function subscribeToChunkUpdate(chunkListPath, sendMessage, callback) {
    return subscribeToUpdate({
        path: chunkListPath
    }, sendMessage, callback);
}
function subscribeToUpdate(resource, sendMessage, callback) {
    const key = resourceKey(resource);
    let callbackSet;
    const existingCallbackSet = updateCallbackSets.get(key);
    if (!existingCallbackSet) {
        callbackSet = {
            callbacks: new Set([
                callback
            ]),
            unsubscribe: subscribeToUpdates(sendMessage, resource)
        };
        updateCallbackSets.set(key, callbackSet);
    } else {
        existingCallbackSet.callbacks.add(callback);
        callbackSet = existingCallbackSet;
    }
    return ()=>{
        callbackSet.callbacks.delete(callback);
        if (callbackSet.callbacks.size === 0) {
            callbackSet.unsubscribe();
            updateCallbackSets.delete(key);
        }
    };
}
function triggerUpdate(msg) {
    const key = resourceKey(msg.resource);
    const callbackSet = updateCallbackSets.get(key);
    if (!callbackSet) {
        return;
    }
    for (const callback of callbackSet.callbacks){
        callback(msg);
    }
    if (msg.type === 'notFound') {
        // This indicates that the resource which we subscribed to either does not exist or
        // has been deleted. In either case, we should clear all update callbacks, so if a
        // new subscription is created for the same resource, it will send a new "subscribe"
        // message to the server.
        // No need to send an "unsubscribe" message to the server, it will have already
        // dropped the update stream before sending the "notFound" message.
        updateCallbackSets.delete(key);
    }
}
}),
"[project]/src/lib/api.ts [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>__TURBOPACK__default__export__
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$axios$2f$lib$2f$axios$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/axios/lib/axios.js [client] (ecmascript)");
;
const api = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$axios$2f$lib$2f$axios$2e$js__$5b$client$5d$__$28$ecmascript$29$__["default"].create({
    baseURL: "http://localhost:8000",
    timeout: 30000,
    headers: {
        "Content-Type": "application/json"
    },
    withCredentials: true
});
// Request interceptor
api.interceptors.request.use((config)=>{
    // Add any request modifications here if needed
    return config;
}, (error)=>{
    return Promise.reject(error);
});
// Response interceptor for handling 401 errors
api.interceptors.response.use((response)=>{
    // Any status code that lies within the range of 2xx causes this function to trigger
    return response;
}, (error)=>{
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
        console.warn('🔐 Authentication required - dispatching auth-expired event');
        // Clear any stored auth data
        localStorage.removeItem("upstox_auth");
        sessionStorage.removeItem("upstox_auth");
        // Dispatch global event for auth expiry
        window.dispatchEvent(new Event("auth-expired"));
    }
    // Handle network errors
    if (!error.response) {
        console.error('🌐 Network error - please check your connection');
        return Promise.reject(error);
    }
    // Handle other HTTP errors
    console.error(`❌ API Error: ${error.response?.status} - ${error.response?.data?.detail || error.message}`);
    return Promise.reject(error);
});
const __TURBOPACK__default__export__ = api;
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/hooks/useLiveMarketData.ts [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "useLiveMarketData",
    ()=>useLiveMarketData
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/index.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$api$2e$ts__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/api.ts [client] (ecmascript)");
var _s = __turbopack_context__.k.signature();
;
;
function useLiveMarketData(symbol, expiry) {
    _s();
    const [data, setData] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const [error, setError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [mode, setMode] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])('loading');
    const [websocket, setWebSocket] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const reconnectTimeoutRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const reconnectAttemptsRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useRef"])(0);
    const connectionStartTimeRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useRef"])(Date.now());
    const connectWebSocket = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "useLiveMarketData.useCallback[connectWebSocket]": ()=>{
            try {
                console.log(`🔌 Connecting to WebSocket for ${symbol}...`);
                connectionStartTimeRef.current = Date.now();
                const wsBaseUrl = ("TURBOPACK compile-time value", "ws://localhost:8000") || 'ws://localhost:8000';
                const wsUrl = `${wsBaseUrl}/ws/live-options/${symbol}`;
                console.log("🔍 DEBUG: Connecting to WS URL:", wsUrl);
                console.log("🔍 DEBUG: Window location:", window.location.href);
                console.log("🔍 DEBUG: Protocol:", window.location.protocol);
                console.log("🔍 DEBUG: WS Base URL:", wsBaseUrl);
                if (typeof window.WebSocket === 'undefined') {
                    console.error('❌ WebSocket is not available in this browser');
                    setError('WebSocket not supported');
                    setMode('error');
                    setLoading(false);
                    return;
                }
                const ws = new window.WebSocket(wsUrl);
                ws.onopen = ({
                    "useLiveMarketData.useCallback[connectWebSocket]": ()=>{
                        console.log(`✅ WebSocket connected for ${symbol}`);
                        setWebSocket(ws);
                        setError(null);
                        reconnectAttemptsRef.current = 0;
                        if (reconnectTimeoutRef.current) {
                            clearTimeout(reconnectTimeoutRef.current);
                            reconnectTimeoutRef.current = null;
                        }
                    }
                })["useLiveMarketData.useCallback[connectWebSocket]"];
                ws.onmessage = ({
                    "useLiveMarketData.useCallback[connectWebSocket]": (event)=>{
                        try {
                            const message = JSON.parse(event.data);
                            console.log(`📨 WebSocket message for ${symbol}:`, message);
                            if (message.status === 'auth_required') {
                                console.warn('🔐 Authentication required - redirecting to auth screen');
                                ws.close();
                                window.dispatchEvent(new Event('auth-expired'));
                                setError('Authentication required');
                                setMode('error');
                                setLoading(false);
                                return;
                            }
                            if (message.status === 'connected') {
                                console.log('✅ WebSocket connection established');
                                return;
                            }
                            if (message.status === 'heartbeat') {
                                console.log('💓 WebSocket heartbeat received');
                                return;
                            }
                            if (message.status === 'success') {
                                if (message.mode === 'snapshot') {
                                    console.log('📸 Received snapshot from WebSocket');
                                    setData(message.data);
                                    setMode('snapshot');
                                    setLoading(false);
                                    setError(null);
                                } else if (message.mode === 'live') {
                                    console.log('🔄 Received live update from WebSocket');
                                    setData(message.data);
                                    setMode('live');
                                    setLoading(false);
                                    setError(null);
                                }
                            }
                            if (message.status === 'error') {
                                console.error(`❌ WebSocket error for ${symbol}:`, message.error);
                                setError(message.error || 'WebSocket error');
                                setMode('error');
                                setLoading(false);
                            }
                        } catch (parseError) {
                            console.error('❌ Failed to parse WebSocket message:', parseError);
                            setError('Failed to parse market data');
                            setMode('error');
                            setLoading(false);
                        }
                    }
                })["useLiveMarketData.useCallback[connectWebSocket]"];
                ws.onerror = ({
                    "useLiveMarketData.useCallback[connectWebSocket]": (event)=>{
                        console.error(`❌ WebSocket error for ${symbol}:`, event);
                        const ws = event.target;
                        if (ws && ws.readyState === WebSocket.CLOSED) {
                            console.log('🔐 WebSocket connection was rejected - likely auth error');
                            window.dispatchEvent(new Event('auth-expired'));
                            setError('Authentication required');
                            setMode('error');
                            setLoading(false);
                            return;
                        }
                        const connectionTime = Date.now() - connectionStartTimeRef.current;
                        if (connectionTime < 1000) {
                            console.log('🔐 WebSocket failed to connect immediately - likely auth error');
                            window.dispatchEvent(new Event('auth-expired'));
                            setError('Authentication required');
                            setMode('error');
                            setLoading(false);
                            return;
                        }
                        setError('WebSocket connection error');
                        setMode('error');
                        setLoading(false);
                    }
                })["useLiveMarketData.useCallback[connectWebSocket]"];
                ws.onclose = ({
                    "useLiveMarketData.useCallback[connectWebSocket]": (event)=>{
                        console.log(`🔌 WebSocket closed for ${symbol}:`, event.code, event.reason);
                        setWebSocket(null);
                        if (event.code !== 1000) {
                            console.log('🔄 WebSocket closed unexpectedly, attempting reconnection...');
                            scheduleReconnect();
                        }
                    }
                })["useLiveMarketData.useCallback[connectWebSocket]"];
            } catch (error) {
                console.error('❌ Failed to create WebSocket:', error);
                setError('Failed to connect to market data');
                setMode('error');
                setLoading(false);
            }
        }
    }["useLiveMarketData.useCallback[connectWebSocket]"], [
        symbol
    ]);
    const scheduleReconnect = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "useLiveMarketData.useCallback[scheduleReconnect]": ()=>{
            if (reconnectAttemptsRef.current < 5) {
                reconnectAttemptsRef.current++;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
                console.log(`🔄 Scheduling reconnection attempt ${reconnectAttemptsRef.current} in ${delay}ms`);
                reconnectTimeoutRef.current = setTimeout({
                    "useLiveMarketData.useCallback[scheduleReconnect]": ()=>{
                        connectWebSocket();
                    }
                }["useLiveMarketData.useCallback[scheduleReconnect]"], delay);
            } else {
                console.error('❌ Max reconnection attempts reached');
                setError('Failed to connect after multiple attempts');
                setMode('error');
                setLoading(false);
            }
        }
    }["useLiveMarketData.useCallback[scheduleReconnect]"], []);
    const fallbackToRest = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "useLiveMarketData.useCallback[fallbackToRest]": async ()=>{
            try {
                console.log('🔄 WebSocket failed, falling back to REST API');
                setLoading(true);
                setError(null);
                const response = await __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$api$2e$ts__$5b$client$5d$__$28$ecmascript$29$__["default"].get(`/chain/${symbol}?expiry_date=${expiry}`);
                const fallbackData = {
                    symbol,
                    spot: response.data?.spot || 0,
                    calls: response.data?.calls || [],
                    puts: response.data?.puts || [],
                    analytics: response.data?.analytics || {},
                    intelligence: response.data?.intelligence || {},
                    probability: response.data?.probability || {},
                    timestamp: response.data?.timestamp || new Date().toISOString(),
                    market_status: response.data?.market_status || 'unknown',
                    source: 'rest_api',
                    mode: 'snapshot',
                    change: response.data?.change,
                    change_percent: response.data?.change_percent
                };
                setData(fallbackData);
                setMode('snapshot');
                setLoading(false);
                setError(null);
            } catch (error) {
                console.error('❌ REST API fallback failed:', error);
                setError(error instanceof Error ? error.message : 'Failed to fetch market data');
                setMode('error');
                setLoading(false);
            }
        }
    }["useLiveMarketData.useCallback[fallbackToRest]"], [
        symbol,
        expiry
    ]);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "useLiveMarketData.useEffect": ()=>{
            connectWebSocket();
            const fallbackTimeout = setTimeout({
                "useLiveMarketData.useEffect.fallbackTimeout": ()=>{
                    if (loading && !data && !error) {
                        console.log('⏰ WebSocket timeout, falling back to REST API');
                        fallbackToRest();
                    }
                }
            }["useLiveMarketData.useEffect.fallbackTimeout"], 5000);
            return ({
                "useLiveMarketData.useEffect": ()=>{
                    clearTimeout(fallbackTimeout);
                    if (reconnectTimeoutRef.current) {
                        clearTimeout(reconnectTimeoutRef.current);
                    }
                    if (websocket) {
                        websocket.close();
                    }
                }
            })["useLiveMarketData.useEffect"];
        }
    }["useLiveMarketData.useEffect"], [
        connectWebSocket,
        fallbackToRest,
        loading,
        data,
        error
    ]);
    return {
        data,
        loading,
        error,
        mode,
        websocket
    };
}
_s(useLiveMarketData, "E7m5uf96IlF477dfB8k2KPYv71c=");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/contexts/AuthContext.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "AuthProvider",
    ()=>AuthProvider,
    "useAuth",
    ()=>useAuth
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/index.js [client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature();
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
const AuthContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["createContext"])(undefined);
function AuthProvider({ children }) {
    _s();
    const [state, dispatch] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useReducer"])(authReducer, initialState);
    const checkAuth = async ()=>{
        // Always check auth status, regardless of current state
        dispatch({
            type: 'AUTH_CHECK_START'
        });
        try {
            const response = await fetch('/api/v1/market/status');
            const data = await response.json();
            console.log('🔍 AuthContext: Auth check response:', data);
            if (data.status === 'auth_required') {
                dispatch({
                    type: 'AUTH_REQUIRED',
                    payload: {
                        login_url: data.data.login_url
                    }
                });
            } else {
                dispatch({
                    type: 'AUTH_CHECK_SUCCESS',
                    isAuthenticated: true
                });
            }
        } catch (error) {
            console.error('🔍 AuthContext: Auth check error:', error);
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
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "AuthProvider.useEffect": ()=>{
            console.log('🎧 AuthContext: Setting up event listeners');
            const handleAuthRequired = {
                "AuthProvider.useEffect.handleAuthRequired": (event)=>{
                    console.log('🚫 AuthContext: Received authRequired event', event.detail);
                    const { login_url } = event.detail;
                    dispatch({
                        type: 'AUTH_REQUIRED',
                        payload: {
                            login_url
                        }
                    });
                }
            }["AuthProvider.useEffect.handleAuthRequired"];
            const handleAuthSuccess = {
                "AuthProvider.useEffect.handleAuthSuccess": ()=>{
                    console.log('✅ AuthContext: Received authSuccess event');
                    dispatch({
                        type: 'AUTH_SUCCESS',
                        isAuthenticated: true
                    });
                }
            }["AuthProvider.useEffect.handleAuthSuccess"];
            window.addEventListener('authRequired', handleAuthRequired);
            window.addEventListener('authSuccess', handleAuthSuccess);
            console.log('✅ AuthContext: Event listeners set up');
            return ({
                "AuthProvider.useEffect": ()=>{
                    console.log('🧹 AuthContext: Cleaning up event listeners');
                    window.removeEventListener('authRequired', handleAuthRequired);
                    window.removeEventListener('authSuccess', handleAuthSuccess);
                }
            })["AuthProvider.useEffect"];
        }
    }["AuthProvider.useEffect"], []);
    // Initial auth check on mount
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "AuthProvider.useEffect": ()=>{
            console.log('🔍 AuthContext: Performing initial auth check');
            checkAuth();
        }
    }["AuthProvider.useEffect"], []);
    // Periodic auth check every 30 seconds
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "AuthProvider.useEffect": ()=>{
            const interval = setInterval({
                "AuthProvider.useEffect.interval": ()=>{
                    console.log('🔍 AuthContext: Performing periodic auth check');
                    checkAuth();
                }
            }["AuthProvider.useEffect.interval"], 30000); // Check every 30 seconds
            return ({
                "AuthProvider.useEffect": ()=>clearInterval(interval)
            })["AuthProvider.useEffect"];
        }
    }["AuthProvider.useEffect"], []);
    // Check auth when page becomes visible again (user returns to tab)
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "AuthProvider.useEffect": ()=>{
            const handleVisibilityChange = {
                "AuthProvider.useEffect.handleVisibilityChange": ()=>{
                    if (!document.hidden) {
                        console.log('🔍 AuthContext: Page became visible, checking auth');
                        checkAuth();
                    }
                }
            }["AuthProvider.useEffect.handleVisibilityChange"];
            document.addEventListener('visibilitychange', handleVisibilityChange);
            return ({
                "AuthProvider.useEffect": ()=>{
                    document.removeEventListener('visibilitychange', handleVisibilityChange);
                }
            })["AuthProvider.useEffect"];
        }
    }["AuthProvider.useEffect"], []);
    const value = {
        state,
        dispatch,
        checkAuth,
        handleAuthRequired
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(AuthContext.Provider, {
        value: value,
        children: children
    }, void 0, false, {
        fileName: "[project]/contexts/AuthContext.tsx",
        lineNumber: 191,
        columnNumber: 10
    }, this);
}
_s(AuthProvider, "4iRlf1j8yd8EOnLzdn/Ri/p3tw0=");
_c = AuthProvider;
function useAuth() {
    _s1();
    const context = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useContext"])(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
_s1(useAuth, "b9L3QQ+jgeyIrH0NfHrJ8nn7VMU=");
var _c;
__turbopack_context__.k.register(_c, "AuthProvider");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/MarketMetrics.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>MarketMetrics
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$bar$2d$chart$2d$3$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__BarChart3$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/bar-chart-3.js [client] (ecmascript) <export default as BarChart3>");
;
;
function MarketMetrics({ analytics }) {
    console.log('MarketMetrics render - analytics:', analytics);
    // Compute real metrics from analytics
    const totalCallOI = analytics?.total_call_oi ?? 0;
    const totalPutOI = analytics?.total_put_oi ?? 0;
    const totalOI = totalCallOI + totalPutOI;
    const pcr = analytics?.pcr ?? 0;
    const sentiment = pcr > 1.2 ? "Bullish" : pcr < 0.8 ? "Bearish" : "Neutral";
    const biasStrength = Math.min(Math.abs(pcr - 1) * 100, 100);
    // Safe VWAP calculation (no division by zero)
    const vwapChange = totalOI > 0 ? (0 - totalOI) / totalOI * 100 // Removed data.spot_price reference
     : 0;
    const metrics = [
        {
            label: "Total OI",
            value: (totalOI / 10000000).toFixed(2) + " Cr",
            change: "PCR: " + pcr.toFixed(2),
            changeType: pcr > 1 ? "positive" : "negative",
            icon: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$bar$2d$chart$2d$3$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__BarChart3$3e$__["BarChart3"], {
                className: "w-5 h-5"
            }, void 0, false, {
                fileName: "[project]/components/MarketMetrics.tsx",
                lineNumber: 46,
                columnNumber: 13
            }, this),
            color: "text-primary-500"
        },
        {
            label: "Call OI",
            value: totalCallOI.toLocaleString("en-IN"),
            change: "Resistance @ " + (analytics?.strongest_resistance ?? "-"),
            changeType: "negative",
            icon: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$bar$2d$chart$2d$3$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__BarChart3$3e$__["BarChart3"], {
                className: "w-5 h-5"
            }, void 0, false, {
                fileName: "[project]/components/MarketMetrics.tsx",
                lineNumber: 54,
                columnNumber: 13
            }, this),
            color: "text-danger-500"
        },
        {
            label: "Put OI",
            value: totalPutOI.toLocaleString("en-IN"),
            change: "Support @ " + (analytics?.strongest_support ?? "-"),
            changeType: "positive",
            icon: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$bar$2d$chart$2d$3$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__BarChart3$3e$__["BarChart3"], {
                className: "w-5 h-5"
            }, void 0, false, {
                fileName: "[project]/components/MarketMetrics.tsx",
                lineNumber: 62,
                columnNumber: 13
            }, this),
            color: "text-success-500"
        }
    ];
    const getChangeColor = (changeType)=>{
        return changeType === 'positive' ? 'text-success-500' : 'text-danger-500';
    };
    const getChangeBgColor = (changeType)=>{
        return changeType === 'positive' ? 'bg-success-500/20' : 'bg-danger-500/20';
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "metric-card",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                        className: "text-xl font-semibold",
                        children: "Market Metrics"
                    }, void 0, false, {
                        fileName: "[project]/components/MarketMetrics.tsx",
                        lineNumber: 78,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-sm text-muted-foreground",
                        children: new Date().toLocaleTimeString()
                    }, void 0, false, {
                        fileName: "[project]/components/MarketMetrics.tsx",
                        lineNumber: 79,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/MarketMetrics.tsx",
                lineNumber: 77,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "grid grid-cols-2 gap-4 mb-6",
                children: metrics.map((metric, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "glass-morphism rounded-lg p-4",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center justify-between mb-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: `${metric.color}`,
                                        children: metric.icon
                                    }, void 0, false, {
                                        fileName: "[project]/components/MarketMetrics.tsx",
                                        lineNumber: 89,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: `text-xs px-2 py-1 rounded-full ${getChangeBgColor(metric.changeType)} ${getChangeColor(metric.changeType)}`,
                                        children: metric.change
                                    }, void 0, false, {
                                        fileName: "[project]/components/MarketMetrics.tsx",
                                        lineNumber: 92,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/MarketMetrics.tsx",
                                lineNumber: 88,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-lg font-bold mb-1",
                                children: metric.value
                            }, void 0, false, {
                                fileName: "[project]/components/MarketMetrics.tsx",
                                lineNumber: 96,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-xs text-muted-foreground",
                                children: metric.label
                            }, void 0, false, {
                                fileName: "[project]/components/MarketMetrics.tsx",
                                lineNumber: 97,
                                columnNumber: 13
                            }, this)
                        ]
                    }, index, true, {
                        fileName: "[project]/components/MarketMetrics.tsx",
                        lineNumber: 87,
                        columnNumber: 11
                    }, this))
            }, void 0, false, {
                fileName: "[project]/components/MarketMetrics.tsx",
                lineNumber: 85,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "glass-morphism rounded-lg p-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center justify-between mb-3",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                className: "text-sm font-medium mb-3",
                                children: "Market Sentiment"
                            }, void 0, false, {
                                fileName: "[project]/components/MarketMetrics.tsx",
                                lineNumber: 105,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: `px-3 py-1 rounded-full ${sentiment === 'Bullish' ? 'bg-success-500/20 text-success-500' : sentiment === 'Bearish' ? 'bg-danger-500/20 text-danger-500' : 'bg-warning-500/20 text-warning-500'}`,
                                children: sentiment
                            }, void 0, false, {
                                fileName: "[project]/components/MarketMetrics.tsx",
                                lineNumber: 106,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/MarketMetrics.tsx",
                        lineNumber: 104,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "space-y-2",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex justify-between text-sm mb-1",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Put/Call Ratio"
                                    }, void 0, false, {
                                        fileName: "[project]/components/MarketMetrics.tsx",
                                        lineNumber: 119,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "font-medium",
                                        children: pcr.toFixed(2)
                                    }, void 0, false, {
                                        fileName: "[project]/components/MarketMetrics.tsx",
                                        lineNumber: 120,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/MarketMetrics.tsx",
                                lineNumber: 118,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "h-2 rounded-full bg-gray-500/20",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "h-2 rounded-full bg-primary-500",
                                    style: {
                                        width: `${biasStrength}%`
                                    }
                                }, void 0, false, {
                                    fileName: "[project]/components/MarketMetrics.tsx",
                                    lineNumber: 123,
                                    columnNumber: 13
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/MarketMetrics.tsx",
                                lineNumber: 122,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex justify-between text-sm",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Market Bias"
                                    }, void 0, false, {
                                        fileName: "[project]/components/MarketMetrics.tsx",
                                        lineNumber: 129,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: `font-medium ${sentiment === 'Bullish' ? 'text-success-500' : 'text-danger-500'}`,
                                        children: sentiment
                                    }, void 0, false, {
                                        fileName: "[project]/components/MarketMetrics.tsx",
                                        lineNumber: 130,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/MarketMetrics.tsx",
                                lineNumber: 128,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/MarketMetrics.tsx",
                        lineNumber: 117,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/MarketMetrics.tsx",
                lineNumber: 103,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/MarketMetrics.tsx",
        lineNumber: 76,
        columnNumber: 5
    }, this);
}
_c = MarketMetrics;
var _c;
__turbopack_context__.k.register(_c, "MarketMetrics");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/OIHeatmap.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>OIHeatmap
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/index.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$calendar$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Calendar$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/calendar.js [client] (ecmascript) <export default as Calendar>");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$api$2e$ts__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/api.ts [client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
;
;
;
function OIHeatmap({ symbol, liveData }) {
    _s();
    const [oiData, setOiData] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [spotPrice, setSpotPrice] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [error, setError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [expiryLoading, setExpiryLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [availableExpiries, setAvailableExpiries] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [selectedExpiry, setSelectedExpiry] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])('');
    const tableRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const atmRowRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    // Fetch available expiry dates
    const fetchAvailableExpiries = async ()=>{
        try {
            setExpiryLoading(true);
            const response = await __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$api$2e$ts__$5b$client$5d$__$28$ecmascript$29$__["default"].get(`/api/v1/options/contract/${symbol}`);
            let expiryDates = [];
            if (response.data && response.data.data && Array.isArray(response.data.data)) {
                expiryDates = response.data.data;
            } else if (response.data && Array.isArray(response.data)) {
                expiryDates = response.data;
            }
            const expiries = expiryDates.map((date)=>{
                const expiryDate = new Date(date);
                const today = new Date();
                const daysUntilExpiry = Math.ceil((expiryDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                const isCurrent = daysUntilExpiry >= 0 && daysUntilExpiry <= 7;
                return {
                    date,
                    label: formatExpiryDate(date),
                    isCurrent
                };
            });
            setAvailableExpiries(expiries);
            if (!selectedExpiry && expiries.length > 0) {
                const currentExpiry = expiries.find((e)=>e.isCurrent);
                const nearestExpiry = currentExpiry || expiries[0];
                setSelectedExpiry(nearestExpiry.date);
            }
        } catch (err) {
            console.error('Error fetching expiries:', err);
            setError('Failed to fetch expiry dates');
        } finally{
            setExpiryLoading(false);
        }
    };
    // Format expiry date for display
    const formatExpiryDate = (dateString)=>{
        const date = new Date(dateString);
        const today = new Date();
        const daysUntilExpiry = Math.ceil((date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === new Date(today.getTime() + 24 * 60 * 60 * 1000).toDateString()) {
            return 'Tomorrow';
        } else if (daysUntilExpiry > 0 && daysUntilExpiry <= 7) {
            return `${daysUntilExpiry} days`;
        } else if (daysUntilExpiry > 7 && daysUntilExpiry <= 14) {
            const weeks = Math.floor(daysUntilExpiry / 7);
            return `${weeks} week${weeks > 1 ? 's' : ''}`;
        } else {
            return date.toLocaleDateString('en-IN', {
                day: 'numeric',
                month: 'short',
                year: '2-digit'
            });
        }
    };
    // Handle expiry selection
    const handleExpiryChange = (expiry)=>{
        const date = new Date(expiry);
        const today = new Date();
        if (!isNaN(date.getTime()) && date >= today) {
            setSelectedExpiry(expiry);
        }
    };
    // Auto-scroll to ATM row when data loads
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "OIHeatmap.useEffect": ()=>{
            if (atmRowRef.current && tableRef.current && oiData.length > 0) {
                const tableContainer = tableRef.current;
                const atmRow = atmRowRef.current;
                // Calculate position to center ATM row in view (show 7 rows total)
                const rowHeight = atmRow.offsetHeight;
                const containerHeight = tableContainer.clientHeight;
                const targetScrollTop = atmRow.offsetTop - containerHeight / 2 + rowHeight / 2;
                // Smooth scroll to center ATM row
                tableContainer.scrollTo({
                    top: targetScrollTop,
                    behavior: 'smooth'
                });
            }
        }
    }["OIHeatmap.useEffect"], [
        oiData,
        spotPrice
    ]);
    // Process live data from WebSocket when available
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "OIHeatmap.useEffect": ()=>{
            if (liveData && liveData.calls && liveData.puts) {
                console.log('🔥 OIHeatmap - Processing live WebSocket data');
                // Use spot price from live data
                setSpotPrice(liveData.spot);
                // Transform live data for heatmap
                const transformedData = liveData.calls.map({
                    "OIHeatmap.useEffect.transformedData": (call)=>{
                        const matchingPut = liveData.puts.find({
                            "OIHeatmap.useEffect.transformedData.matchingPut": (p)=>p.strike === call.strike
                        }["OIHeatmap.useEffect.transformedData.matchingPut"]);
                        return {
                            strike: call.strike,
                            oi: call.oi || 0,
                            change: call.change || 0,
                            ltp: call.ltp || 0,
                            volume: call.volume || 0,
                            iv: call.iv || 0,
                            put_oi: matchingPut?.oi || 0,
                            put_change: matchingPut?.change || 0,
                            put_ltp: matchingPut?.ltp || 0,
                            put_volume: matchingPut?.volume || 0,
                            put_iv: matchingPut?.iv || 0
                        };
                    }
                }["OIHeatmap.useEffect.transformedData"]);
                setOiData(transformedData);
                setLoading(false);
                setError(null);
                console.log('🔥 OIHeatmap - Live data processed:', transformedData.length, 'strikes');
            }
        }
    }["OIHeatmap.useEffect"], [
        liveData
    ]);
    // Fetch expiries on component mount (REST - cached)
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "OIHeatmap.useEffect": ()=>{
            fetchAvailableExpiries();
        }
    }["OIHeatmap.useEffect"], [
        symbol
    ]);
    // Fetch option chain data
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "OIHeatmap.useEffect": ()=>{
            if (selectedExpiry) {
                const fetchOptionChain = {
                    "OIHeatmap.useEffect.fetchOptionChain": async ()=>{
                        try {
                            setLoading(true);
                            setError(null);
                            const response = await __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$api$2e$ts__$5b$client$5d$__$28$ecmascript$29$__["default"].get(`/api/v1/options/chain/${symbol}?expiry_date=${selectedExpiry}`);
                            const chain = response.data;
                            const calls = chain?.data?.calls || [];
                            const puts = chain?.data?.puts || [];
                            // Use the actual spot price from API response instead of calculating it
                            let currentSpotPrice = chain?.data?.spot || null;
                            console.log('🔍 OIHeatmap - Raw API Response:', chain);
                            console.log('🔍 OIHeatmap - Extracted spot price:', currentSpotPrice);
                            // Fallback calculation only if spot price is not available
                            if (!currentSpotPrice && calls.length > 0) {
                                console.log('🔍 OIHeatmap - Spot price not found, calculating from options');
                                // Find strike closest to spot (ATM) - this is usually current spot
                                const sortedCalls = [
                                    ...calls
                                ].sort({
                                    "OIHeatmap.useEffect.fetchOptionChain.sortedCalls": (a, b)=>Math.abs(a.strike - (spotPrice || 0)) - Math.abs(b.strike - (spotPrice || 0))
                                }["OIHeatmap.useEffect.fetchOptionChain.sortedCalls"]);
                                const atmCall = sortedCalls[0];
                                // Estimate spot from ATM strike and option prices
                                if (atmCall && atmCall.ltp > 0) {
                                    const matchingPut = puts.find({
                                        "OIHeatmap.useEffect.fetchOptionChain.matchingPut": (p)=>p.strike === atmCall.strike
                                    }["OIHeatmap.useEffect.fetchOptionChain.matchingPut"]);
                                    if (matchingPut && matchingPut.ltp > 0) {
                                        // Spot ≈ Strike + Call LTP - Put LTP (put-call parity approximation)
                                        currentSpotPrice = atmCall.strike + atmCall.ltp - matchingPut.ltp;
                                        console.log('🔍 OIHeatmap - Calculated spot price:', currentSpotPrice);
                                    }
                                }
                            }
                            setSpotPrice(currentSpotPrice);
                            const transformedData = calls.map({
                                "OIHeatmap.useEffect.fetchOptionChain.transformedData": (call)=>{
                                    const matchingPut = puts.find({
                                        "OIHeatmap.useEffect.fetchOptionChain.transformedData.matchingPut": (p)=>p.strike === call.strike
                                    }["OIHeatmap.useEffect.fetchOptionChain.transformedData.matchingPut"]);
                                    return {
                                        strike: call.strike,
                                        oi: call.oi || 0,
                                        change: call.change || 0,
                                        ltp: call.ltp || 0,
                                        volume: call.volume || 0,
                                        iv: call.iv || 0,
                                        put_oi: matchingPut?.oi || 0,
                                        put_change: matchingPut?.change || 0,
                                        put_ltp: matchingPut?.ltp || 0,
                                        put_volume: matchingPut?.volume || 0,
                                        put_iv: matchingPut?.iv || 0
                                    };
                                }
                            }["OIHeatmap.useEffect.fetchOptionChain.transformedData"]);
                            setOiData(transformedData);
                        } catch (err) {
                            console.error("Error fetching option chain:", err);
                            // Check if it's a 401 error - axios interceptor will handle redirect
                            if (err.response?.status === 401) {
                                console.log('🔐 401 detected in OIHeatmap - axios interceptor will handle redirect');
                                return; // Don't set error state, let interceptor handle
                            }
                            if (err?.response?.status === 429) {
                                setError("Rate limit exceeded - please wait");
                            } else {
                                setError("Failed to fetch option chain data");
                            }
                        } finally{
                            setLoading(false);
                        }
                    }
                }["OIHeatmap.useEffect.fetchOptionChain"];
                fetchOptionChain();
            }
        }
    }["OIHeatmap.useEffect"], [
        symbol,
        selectedExpiry
    ]);
    if (loading) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "flex items-center justify-center h-96",
            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "loading-dots",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {}, void 0, false, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 268,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {}, void 0, false, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 269,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {}, void 0, false, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 270,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/OIHeatmap.tsx",
                lineNumber: 267,
                columnNumber: 9
            }, this)
        }, void 0, false, {
            fileName: "[project]/components/OIHeatmap.tsx",
            lineNumber: 266,
            columnNumber: 7
        }, this);
    }
    if (error) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "metric-card",
            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-center h-96",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                            className: "text-xl font-semibold text-danger-500",
                            children: "Error"
                        }, void 0, false, {
                            fileName: "[project]/components/OIHeatmap.tsx",
                            lineNumber: 281,
                            columnNumber: 13
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-muted-foreground",
                            children: error
                        }, void 0, false, {
                            fileName: "[project]/components/OIHeatmap.tsx",
                            lineNumber: 282,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/OIHeatmap.tsx",
                    lineNumber: 280,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/OIHeatmap.tsx",
                lineNumber: 279,
                columnNumber: 9
            }, this)
        }, void 0, false, {
            fileName: "[project]/components/OIHeatmap.tsx",
            lineNumber: 278,
            columnNumber: 7
        }, this);
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "metric-card min-h-screen",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                        className: "text-2xl font-bold",
                        children: [
                            "OI Heatmap - ",
                            symbol
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 292,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center gap-6",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-3 text-base",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "w-4 h-4 bg-danger-500 rounded"
                                    }, void 0, false, {
                                        fileName: "[project]/components/OIHeatmap.tsx",
                                        lineNumber: 295,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Call OI"
                                    }, void 0, false, {
                                        fileName: "[project]/components/OIHeatmap.tsx",
                                        lineNumber: 296,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 294,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-3 text-base",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "w-4 h-4 bg-success-500 rounded"
                                    }, void 0, false, {
                                        fileName: "[project]/components/OIHeatmap.tsx",
                                        lineNumber: 299,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Put OI"
                                    }, void 0, false, {
                                        fileName: "[project]/components/OIHeatmap.tsx",
                                        lineNumber: 300,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 298,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 293,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/OIHeatmap.tsx",
                lineNumber: 291,
                columnNumber: 7
            }, this),
            spotPrice && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mb-4 p-3 glass-morphism rounded-lg border-l-4 border-l-green-500",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center justify-between",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                            className: "text-sm text-muted-foreground",
                            children: "Current Spot Price"
                        }, void 0, false, {
                            fileName: "[project]/components/OIHeatmap.tsx",
                            lineNumber: 309,
                            columnNumber: 13
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "text-right",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-lg font-bold text-green-400",
                                    children: [
                                        "₹",
                                        spotPrice.toLocaleString('en-IN', {
                                            minimumFractionDigits: 2,
                                            maximumFractionDigits: 2
                                        })
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/components/OIHeatmap.tsx",
                                    lineNumber: 311,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "text-xs text-muted-foreground",
                                    children: "Expected: ₹25,471.10"
                                }, void 0, false, {
                                    fileName: "[project]/components/OIHeatmap.tsx",
                                    lineNumber: 314,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/components/OIHeatmap.tsx",
                            lineNumber: 310,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/OIHeatmap.tsx",
                    lineNumber: 308,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/OIHeatmap.tsx",
                lineNumber: 307,
                columnNumber: 9
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mb-4 bg-black/50 border border-red-500/30 rounded-lg p-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                        className: "text-red-400 font-bold mb-2",
                        children: "DEBUG: OIHeatmap Spot Price"
                    }, void 0, false, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 324,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-green-400 text-xs space-y-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    "Current: ₹",
                                    spotPrice?.toLocaleString('en-IN', {
                                        minimumFractionDigits: 2,
                                        maximumFractionDigits: 2
                                    }) || 'null'
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 326,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: "Expected: ₹25,471.10"
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 327,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    "Difference: ",
                                    spotPrice ? (spotPrice - 25471.10).toFixed(2) : 'N/A'
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 328,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 325,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/OIHeatmap.tsx",
                lineNumber: 323,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mb-4 p-3 glass-morphism rounded-lg",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center justify-between",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center gap-2",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$calendar$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Calendar$3e$__["Calendar"], {
                                    className: "w-4 h-4 text-muted-foreground"
                                }, void 0, false, {
                                    fileName: "[project]/components/OIHeatmap.tsx",
                                    lineNumber: 336,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-sm text-muted-foreground",
                                    children: "Expiry Date"
                                }, void 0, false, {
                                    fileName: "[project]/components/OIHeatmap.tsx",
                                    lineNumber: 337,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/components/OIHeatmap.tsx",
                            lineNumber: 335,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center gap-2",
                            children: expiryLoading ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"
                                    }, void 0, false, {
                                        fileName: "[project]/components/OIHeatmap.tsx",
                                        lineNumber: 342,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-sm text-blue-500",
                                        children: "Loading expiries..."
                                    }, void 0, false, {
                                        fileName: "[project]/components/OIHeatmap.tsx",
                                        lineNumber: 343,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 341,
                                columnNumber: 15
                            }, this) : availableExpiries.length > 0 ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                value: selectedExpiry,
                                onChange: (e)=>handleExpiryChange(e.target.value),
                                className: "bg-background border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-32",
                                disabled: loading,
                                children: availableExpiries.map((expiry)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                        value: expiry.date,
                                        children: [
                                            expiry.label,
                                            " ",
                                            expiry.isCurrent && '(Current)'
                                        ]
                                    }, expiry.date, true, {
                                        fileName: "[project]/components/OIHeatmap.tsx",
                                        lineNumber: 353,
                                        columnNumber: 19
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 346,
                                columnNumber: 15
                            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "text-sm text-muted-foreground",
                                children: "No expiries available"
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 359,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/components/OIHeatmap.tsx",
                            lineNumber: 339,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/OIHeatmap.tsx",
                    lineNumber: 334,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/components/OIHeatmap.tsx",
                lineNumber: 333,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "relative",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "sticky top-0 z-10 bg-background/95 backdrop-blur-sm border-b border-white/10",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                            className: "w-full",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("thead", {
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                    className: "text-left text-sm text-muted-foreground",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "py-3 px-2 text-center min-w-[90px]",
                                            children: "Call OI"
                                        }, void 0, false, {
                                            fileName: "[project]/components/OIHeatmap.tsx",
                                            lineNumber: 372,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "py-3 px-2 text-center min-w-[70px]",
                                            children: "Call Chg"
                                        }, void 0, false, {
                                            fileName: "[project]/components/OIHeatmap.tsx",
                                            lineNumber: 373,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "py-3 px-2 text-center min-w-[90px]",
                                            children: "Call LTP"
                                        }, void 0, false, {
                                            fileName: "[project]/components/OIHeatmap.tsx",
                                            lineNumber: 374,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "py-3 px-2 text-center min-w-[80px]",
                                            children: "Strike"
                                        }, void 0, false, {
                                            fileName: "[project]/components/OIHeatmap.tsx",
                                            lineNumber: 375,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "py-3 px-2 text-center min-w-[90px]",
                                            children: "Put LTP"
                                        }, void 0, false, {
                                            fileName: "[project]/components/OIHeatmap.tsx",
                                            lineNumber: 376,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "py-3 px-2 text-center min-w-[70px]",
                                            children: "Put Chg"
                                        }, void 0, false, {
                                            fileName: "[project]/components/OIHeatmap.tsx",
                                            lineNumber: 377,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                            className: "py-3 px-2 text-center min-w-[90px]",
                                            children: "Put OI"
                                        }, void 0, false, {
                                            fileName: "[project]/components/OIHeatmap.tsx",
                                            lineNumber: 378,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/components/OIHeatmap.tsx",
                                    lineNumber: 371,
                                    columnNumber: 15
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 370,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/components/OIHeatmap.tsx",
                            lineNumber: 369,
                            columnNumber: 11
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 368,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "overflow-x-auto overflow-y-auto max-h-96",
                        ref: tableRef,
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                            className: "w-full",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("thead", {
                                    className: "invisible",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                        className: "text-left text-sm text-muted-foreground",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                className: "py-3 px-2 text-center min-w-[90px]",
                                                children: "Call OI"
                                            }, void 0, false, {
                                                fileName: "[project]/components/OIHeatmap.tsx",
                                                lineNumber: 389,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                className: "py-3 px-2 text-center min-w-[70px]",
                                                children: "Call Chg"
                                            }, void 0, false, {
                                                fileName: "[project]/components/OIHeatmap.tsx",
                                                lineNumber: 390,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                className: "py-3 px-2 text-center min-w-[90px]",
                                                children: "Call LTP"
                                            }, void 0, false, {
                                                fileName: "[project]/components/OIHeatmap.tsx",
                                                lineNumber: 391,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                className: "py-3 px-2 text-center min-w-[80px]",
                                                children: "Strike"
                                            }, void 0, false, {
                                                fileName: "[project]/components/OIHeatmap.tsx",
                                                lineNumber: 392,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                className: "py-3 px-2 text-center min-w-[90px]",
                                                children: "Put LTP"
                                            }, void 0, false, {
                                                fileName: "[project]/components/OIHeatmap.tsx",
                                                lineNumber: 393,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                className: "py-3 px-2 text-center min-w-[70px]",
                                                children: "Put Chg"
                                            }, void 0, false, {
                                                fileName: "[project]/components/OIHeatmap.tsx",
                                                lineNumber: 394,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                className: "py-3 px-2 text-center min-w-[90px]",
                                                children: "Put OI"
                                            }, void 0, false, {
                                                fileName: "[project]/components/OIHeatmap.tsx",
                                                lineNumber: 395,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/OIHeatmap.tsx",
                                        lineNumber: 388,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/components/OIHeatmap.tsx",
                                    lineNumber: 387,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tbody", {
                                    children: oiData.map((row, index)=>{
                                        // Check if this strike is closest ATM (single strike only)
                                        const isATM = spotPrice && Math.abs(row.strike - spotPrice) <= 25; // Within 25 points (tighter range)
                                        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                            ref: isATM ? atmRowRef : null,
                                            className: `border-b border-white/5 hover:bg-white/5 ${isATM ? 'bg-green-500/10 border-l-2 border-l-green-500' : ''}`,
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "py-3 text-center",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "px-2 py-1 rounded text-xs font-medium text-white oi-heatmap-cell",
                                                        style: {
                                                            backgroundColor: 'rgba(239, 68, 68, 0.5)'
                                                        },
                                                        children: row.oi.toLocaleString('en-IN')
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/OIHeatmap.tsx",
                                                        lineNumber: 413,
                                                        columnNumber: 19
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/components/OIHeatmap.tsx",
                                                    lineNumber: 412,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "py-3 text-center",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: `px-2 py-1 rounded text-xs font-medium ${row.change > 0 ? 'bg-success-500/20 text-success-500' : row.change < 0 ? 'bg-danger-500/20 text-danger-500' : 'bg-gray-500/20 text-gray-300'}`,
                                                        children: row.change?.toLocaleString('en-IN')
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/OIHeatmap.tsx",
                                                        lineNumber: 423,
                                                        columnNumber: 19
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/components/OIHeatmap.tsx",
                                                    lineNumber: 422,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "py-3 text-center text-sm",
                                                    children: row.ltp?.toLocaleString('en-IN', {
                                                        style: 'currency',
                                                        currency: 'INR'
                                                    })
                                                }, void 0, false, {
                                                    fileName: "[project]/components/OIHeatmap.tsx",
                                                    lineNumber: 433,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "py-3 px-2 text-center font-medium",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                        className: isATM ? 'text-green-400 font-bold' : '',
                                                        children: [
                                                            row.strike.toLocaleString('en-IN'),
                                                            isATM && ' 📍'
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/components/OIHeatmap.tsx",
                                                        lineNumber: 442,
                                                        columnNumber: 19
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/components/OIHeatmap.tsx",
                                                    lineNumber: 441,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "py-3 text-center text-sm",
                                                    children: row.put_ltp?.toLocaleString('en-IN', {
                                                        style: 'currency',
                                                        currency: 'INR'
                                                    })
                                                }, void 0, false, {
                                                    fileName: "[project]/components/OIHeatmap.tsx",
                                                    lineNumber: 449,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "py-3 text-center",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: `px-2 py-1 rounded text-xs font-medium ${row.put_change > 0 ? 'bg-success-500/20 text-success-500' : row.put_change < 0 ? 'bg-danger-500/20 text-danger-500' : 'bg-gray-500/20 text-gray-300'}`,
                                                        children: row.put_change?.toLocaleString('en-IN')
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/OIHeatmap.tsx",
                                                        lineNumber: 458,
                                                        columnNumber: 19
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/components/OIHeatmap.tsx",
                                                    lineNumber: 457,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "py-3 text-center",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "px-2 py-1 rounded text-xs font-medium text-white oi-heatmap-cell",
                                                        style: {
                                                            backgroundColor: 'rgba(34, 197, 94, 0.5)'
                                                        },
                                                        children: row.put_oi.toLocaleString('en-IN')
                                                    }, void 0, false, {
                                                        fileName: "[project]/components/OIHeatmap.tsx",
                                                        lineNumber: 469,
                                                        columnNumber: 19
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/components/OIHeatmap.tsx",
                                                    lineNumber: 468,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, index, true, {
                                            fileName: "[project]/components/OIHeatmap.tsx",
                                            lineNumber: 404,
                                            columnNumber: 15
                                        }, this);
                                    })
                                }, void 0, false, {
                                    fileName: "[project]/components/OIHeatmap.tsx",
                                    lineNumber: 398,
                                    columnNumber: 11
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/components/OIHeatmap.tsx",
                            lineNumber: 386,
                            columnNumber: 11
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 385,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/OIHeatmap.tsx",
                lineNumber: 366,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-4 pt-4 border-t border-white/10",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "font-medium mb-2",
                        children: "Interpretation:"
                    }, void 0, false, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 486,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-sm text-muted-foreground space-y-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: "• 📍 Green highlight indicates ATM (At-The-Money) strike"
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 488,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: "• Darker colors indicate higher Open Interest"
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 489,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: "• Green changes show OI addition, Red shows OI reduction"
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 490,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: "• High Call OI at strikes above spot = Resistance"
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 491,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: "• High Put OI at strikes below spot = Support"
                            }, void 0, false, {
                                fileName: "[project]/components/OIHeatmap.tsx",
                                lineNumber: 492,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/OIHeatmap.tsx",
                        lineNumber: 487,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/OIHeatmap.tsx",
                lineNumber: 485,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/OIHeatmap.tsx",
        lineNumber: 290,
        columnNumber: 5
    }, this);
}
_s(OIHeatmap, "IyhpkLcxbX60ygNj/u5rGk57yck=");
_c = OIHeatmap;
var _c;
__turbopack_context__.k.register(_c, "OIHeatmap");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/AIInterpretationPanel.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>AIInterpretationPanel
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/index.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$brain$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Brain$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/brain.js [client] (ecmascript) <export default as Brain>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$triangle$2d$alert$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__AlertTriangle$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/triangle-alert.js [client] (ecmascript) <export default as AlertTriangle>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$check$2d$big$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__CheckCircle$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/circle-check-big.js [client] (ecmascript) <export default as CheckCircle>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$clock$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Clock$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/clock.js [client] (ecmascript) <export default as Clock>");
;
var _s = __turbopack_context__.k.signature();
;
;
function AIInterpretationPanel({ intelligence }) {
    _s();
    const [interpretation, setInterpretation] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [loading, setLoading] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [error, setError] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])(null);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "AIInterpretationPanel.useEffect": ()=>{
            if (!intelligence) {
                setInterpretation(null);
                return;
            }
            const fetchInterpretation = {
                "AIInterpretationPanel.useEffect.fetchInterpretation": async ()=>{
                    setLoading(true);
                    setError(null);
                    try {
                        const response = await fetch('/api/v1/intelligence/interpret', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(intelligence)
                        });
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        const result = await response.json();
                        setInterpretation(result.data);
                    } catch (err) {
                        console.error('Failed to fetch AI interpretation:', err);
                        setError('AI interpretation temporarily unavailable');
                    } finally{
                        setLoading(false);
                    }
                }
            }["AIInterpretationPanel.useEffect.fetchInterpretation"];
            fetchInterpretation();
        }
    }["AIInterpretationPanel.useEffect"], [
        intelligence
    ]);
    const getConfidenceIcon = (tone)=>{
        switch(tone){
            case 'high':
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$check$2d$big$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__CheckCircle$3e$__["CheckCircle"], {
                    className: "w-4 h-4 text-success-400"
                }, void 0, false, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 64,
                    columnNumber: 16
                }, this);
            case 'medium':
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$brain$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Brain$3e$__["Brain"], {
                    className: "w-4 h-4 text-warning-400"
                }, void 0, false, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 66,
                    columnNumber: 16
                }, this);
            case 'cautious':
            default:
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$triangle$2d$alert$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__AlertTriangle$3e$__["AlertTriangle"], {
                    className: "w-4 h-4 text-danger-400"
                }, void 0, false, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 69,
                    columnNumber: 16
                }, this);
        }
    };
    const getConfidenceColor = (tone)=>{
        switch(tone){
            case 'high':
                return 'text-success-400 bg-success-500/20 border-success-500/30';
            case 'medium':
                return 'text-warning-400 bg-warning-500/20 border-warning-500/30';
            case 'cautious':
            default:
                return 'text-danger-400 bg-danger-500/20 border-danger-500/30';
        }
    };
    if (!intelligence) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "glass-morphism rounded-2xl p-6 border border-white/10",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center gap-3 mb-4",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$brain$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Brain$3e$__["Brain"], {
                            className: "w-5 h-5 text-primary-400"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 89,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                            className: "text-lg font-semibold text-white",
                            children: "AI Interpretation"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 90,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 88,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center text-muted-foreground",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$clock$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Clock$3e$__["Clock"], {
                            className: "w-8 h-8 mx-auto mb-2 opacity-50"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 93,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            children: "Waiting for market intelligence..."
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 94,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 92,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/AIInterpretationPanel.tsx",
            lineNumber: 87,
            columnNumber: 7
        }, this);
    }
    if (loading) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "glass-morphism rounded-2xl p-6 border border-white/10",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center gap-3 mb-4",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$brain$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Brain$3e$__["Brain"], {
                            className: "w-5 h-5 text-primary-400"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 104,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                            className: "text-lg font-semibold text-white",
                            children: "AI Interpretation"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 105,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 103,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center text-muted-foreground",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$brain$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Brain$3e$__["Brain"], {
                            className: "w-8 h-8 mx-auto mb-2 animate-pulse"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 108,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            children: "AI interpretation initializing..."
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 109,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 107,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/AIInterpretationPanel.tsx",
            lineNumber: 102,
            columnNumber: 7
        }, this);
    }
    if (error || !interpretation) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "glass-morphism rounded-2xl p-6 border border-white/10",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center gap-3 mb-4",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$brain$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Brain$3e$__["Brain"], {
                            className: "w-5 h-5 text-primary-400"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 119,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                            className: "text-lg font-semibold text-white",
                            children: "AI Interpretation"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 120,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 118,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center text-muted-foreground",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$triangle$2d$alert$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__AlertTriangle$3e$__["AlertTriangle"], {
                            className: "w-8 h-8 mx-auto mb-2"
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 123,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            children: error || 'AI interpretation temporarily unavailable'
                        }, void 0, false, {
                            fileName: "[project]/components/AIInterpretationPanel.tsx",
                            lineNumber: 124,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/AIInterpretationPanel.tsx",
                    lineNumber: 122,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/AIInterpretationPanel.tsx",
            lineNumber: 117,
            columnNumber: 7
        }, this);
    }
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "glass-morphism rounded-2xl p-6 border border-white/10",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center gap-3",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$brain$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Brain$3e$__["Brain"], {
                                className: "w-5 h-5 text-primary-400"
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 134,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                className: "text-lg font-semibold text-white",
                                children: "AI Interpretation"
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 135,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/AIInterpretationPanel.tsx",
                        lineNumber: 133,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: `flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-medium ${getConfidenceColor(interpretation.confidence_tone)}`,
                        children: [
                            getConfidenceIcon(interpretation.confidence_tone),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "capitalize",
                                children: interpretation.confidence_tone
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 139,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/AIInterpretationPanel.tsx",
                        lineNumber: 137,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/AIInterpretationPanel.tsx",
                lineNumber: 132,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "space-y-6",
                children: [
                    interpretation.narrative && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                className: "text-sm font-medium text-white mb-2",
                                children: "Market Narrative"
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 147,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-sm text-muted-foreground leading-relaxed",
                                children: interpretation.narrative
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 148,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/AIInterpretationPanel.tsx",
                        lineNumber: 146,
                        columnNumber: 11
                    }, this),
                    interpretation.risk_context && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                className: "text-sm font-medium text-white mb-2",
                                children: "Risk Context"
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 157,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-sm text-muted-foreground leading-relaxed",
                                children: interpretation.risk_context
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 158,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/AIInterpretationPanel.tsx",
                        lineNumber: 156,
                        columnNumber: 11
                    }, this),
                    interpretation.positioning_context && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                className: "text-sm font-medium text-white mb-2",
                                children: "Positioning Context"
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 167,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "text-sm text-muted-foreground leading-relaxed",
                                children: interpretation.positioning_context
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 168,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/AIInterpretationPanel.tsx",
                        lineNumber: 166,
                        columnNumber: 11
                    }, this),
                    interpretation.contradiction_flags && interpretation.contradiction_flags.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                className: "text-sm font-medium text-white mb-2",
                                children: "Market Contradictions"
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 177,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "space-y-1",
                                children: interpretation.contradiction_flags.map((flag, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center gap-2 text-sm text-warning-400",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$triangle$2d$alert$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__AlertTriangle$3e$__["AlertTriangle"], {
                                                className: "w-3 h-3 flex-shrink-0"
                                            }, void 0, false, {
                                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                                lineNumber: 181,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: flag
                                            }, void 0, false, {
                                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                                lineNumber: 182,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, index, true, {
                                        fileName: "[project]/components/AIInterpretationPanel.tsx",
                                        lineNumber: 180,
                                        columnNumber: 17
                                    }, this))
                            }, void 0, false, {
                                fileName: "[project]/components/AIInterpretationPanel.tsx",
                                lineNumber: 178,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/AIInterpretationPanel.tsx",
                        lineNumber: 176,
                        columnNumber: 11
                    }, this),
                    interpretation.fallback && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-center text-xs text-muted-foreground pt-4 border-t border-white/10",
                        children: "Using fallback interpretation"
                    }, void 0, false, {
                        fileName: "[project]/components/AIInterpretationPanel.tsx",
                        lineNumber: 190,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/AIInterpretationPanel.tsx",
                lineNumber: 143,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/AIInterpretationPanel.tsx",
        lineNumber: 131,
        columnNumber: 5
    }, this);
}
_s(AIInterpretationPanel, "4ofDhuF3jJM7m4ac2vph4Bci8XQ=");
_c = AIInterpretationPanel;
var _c;
__turbopack_context__.k.register(_c, "AIInterpretationPanel");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/BiasMeter.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>BiasMeter
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/trending-up.js [client] (ecmascript) <export default as TrendingUp>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/trending-down.js [client] (ecmascript) <export default as TrendingDown>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/target.js [client] (ecmascript) <export default as Target>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$activity$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Activity$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/activity.js [client] (ecmascript) <export default as Activity>");
;
;
function BiasMeter({ intelligence }) {
    console.log('🔍 BiasMeter - Received intelligence:', intelligence);
    if (!intelligence || !intelligence.bias) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "glass-morphism rounded-2xl p-6 border border-white/10",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center gap-3 mb-4",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                            className: "w-5 h-5 text-primary-400"
                        }, void 0, false, {
                            fileName: "[project]/components/BiasMeter.tsx",
                            lineNumber: 24,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                            className: "text-lg font-semibold text-white",
                            children: "Market Bias"
                        }, void 0, false, {
                            fileName: "[project]/components/BiasMeter.tsx",
                            lineNumber: 25,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/BiasMeter.tsx",
                    lineNumber: 23,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center text-muted-foreground",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$activity$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Activity$3e$__["Activity"], {
                            className: "w-8 h-8 mx-auto mb-2 opacity-50"
                        }, void 0, false, {
                            fileName: "[project]/components/BiasMeter.tsx",
                            lineNumber: 28,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            children: "Bias data unavailable"
                        }, void 0, false, {
                            fileName: "[project]/components/BiasMeter.tsx",
                            lineNumber: 29,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/BiasMeter.tsx",
                    lineNumber: 27,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/BiasMeter.tsx",
            lineNumber: 22,
            columnNumber: 7
        }, this);
    }
    const { bias } = intelligence;
    const { score, label, strength, confidence, signal, direction } = bias;
    const getBiasColor = (label)=>{
        if (label === null || label === undefined) return 'bg-warning-500/20 text-warning-500';
        switch(label.toUpperCase()){
            case 'BULLISH':
                return 'bg-success-500/20 text-success-500 border-success-500/30';
            case 'BEARISH':
                return 'bg-danger-500/20 text-danger-500 border-danger-500/30';
            default:
                return 'bg-warning-500/20 text-warning-500 border-warning-500/30';
        }
    };
    const getBiasIcon = (label)=>{
        if (label === null || label === undefined) return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
            className: "w-6 h-6"
        }, void 0, false, {
            fileName: "[project]/components/BiasMeter.tsx",
            lineNumber: 51,
            columnNumber: 55
        }, this);
        switch(label.toUpperCase()){
            case 'BULLISH':
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__["TrendingUp"], {
                    className: "w-6 h-6"
                }, void 0, false, {
                    fileName: "[project]/components/BiasMeter.tsx",
                    lineNumber: 54,
                    columnNumber: 16
                }, this);
            case 'BEARISH':
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__["TrendingDown"], {
                    className: "w-6 h-6"
                }, void 0, false, {
                    fileName: "[project]/components/BiasMeter.tsx",
                    lineNumber: 56,
                    columnNumber: 16
                }, this);
            default:
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                    className: "w-6 h-6"
                }, void 0, false, {
                    fileName: "[project]/components/BiasMeter.tsx",
                    lineNumber: 58,
                    columnNumber: 16
                }, this);
        }
    };
    const getConfidenceColor = (confidence)=>{
        if (confidence === null || confidence === undefined) return 'text-warning-500';
        if (confidence >= 70) return 'text-success-500';
        if (confidence >= 50) return 'text-warning-500';
        return 'text-danger-500';
    };
    const biasColor = getBiasColor(label);
    const biasIcon = getBiasIcon(label);
    const confidenceColor = getConfidenceColor(confidence);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "glass-morphism rounded-2xl p-6 border border-white/10",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center gap-3",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                                className: "w-5 h-5 text-primary-400"
                            }, void 0, false, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 77,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                className: "text-lg font-semibold text-white",
                                children: "Market Bias"
                            }, void 0, false, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 78,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/BiasMeter.tsx",
                        lineNumber: 76,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center gap-2",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "w-2 h-2 bg-success-500 rounded-full animate-pulse"
                            }, void 0, false, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 81,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "text-sm text-muted-foreground",
                                children: "Live"
                            }, void 0, false, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 82,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/BiasMeter.tsx",
                        lineNumber: 80,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/BiasMeter.tsx",
                lineNumber: 75,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex flex-col items-center mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: `w-32 h-32 rounded-full flex items-center justify-center text-white ${biasColor} shadow-lg transition-all duration-500`,
                        children: biasIcon
                    }, void 0, false, {
                        fileName: "[project]/components/BiasMeter.tsx",
                        lineNumber: 88,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-4 text-center",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-2xl font-bold mb-1",
                                children: label || 'NEUTRAL'
                            }, void 0, false, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 93,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: `text-lg font-medium ${confidenceColor}`,
                                children: [
                                    confidence !== null && confidence !== undefined ? confidence.toFixed(1) : '0.0',
                                    "% Confidence"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 94,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-sm text-muted-foreground capitalize",
                                children: [
                                    strength || 'unknown',
                                    " signal"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 97,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/BiasMeter.tsx",
                        lineNumber: 92,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/BiasMeter.tsx",
                lineNumber: 87,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "space-y-2",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex justify-between text-sm",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "text-muted-foreground",
                                children: "Confidence Level"
                            }, void 0, false, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 106,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: confidenceColor,
                                children: [
                                    confidence !== null && confidence !== undefined ? confidence.toFixed(1) : '0.0',
                                    "%"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 107,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/BiasMeter.tsx",
                        lineNumber: 105,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "w-full bg-black/30 rounded-full h-3",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: `h-3 rounded-full transition-all duration-500 ${confidence !== null && confidence !== undefined && confidence >= 70 ? 'bg-success-500' : confidence !== null && confidence !== undefined && confidence >= 50 ? 'bg-warning-500' : 'bg-danger-500'}`,
                            style: {
                                width: `${confidence || 0}%`
                            }
                        }, void 0, false, {
                            fileName: "[project]/components/BiasMeter.tsx",
                            lineNumber: 112,
                            columnNumber: 11
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/components/BiasMeter.tsx",
                        lineNumber: 111,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/BiasMeter.tsx",
                lineNumber: 104,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-6 pt-6 border-t border-white/10",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                        className: "text-sm font-medium text-muted-foreground mb-3",
                        children: "Signal Components"
                    }, void 0, false, {
                        fileName: "[project]/components/BiasMeter.tsx",
                        lineNumber: 127,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "space-y-2 text-sm",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex justify-between",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Bias Score"
                                    }, void 0, false, {
                                        fileName: "[project]/components/BiasMeter.tsx",
                                        lineNumber: 130,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "font-medium",
                                        children: [
                                            score !== null && score !== undefined ? score.toFixed(1) : '0.0',
                                            "/100"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/BiasMeter.tsx",
                                        lineNumber: 131,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 129,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex justify-between",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Signal"
                                    }, void 0, false, {
                                        fileName: "[project]/components/BiasMeter.tsx",
                                        lineNumber: 134,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "font-medium",
                                        children: signal || 'NEUTRAL'
                                    }, void 0, false, {
                                        fileName: "[project]/components/BiasMeter.tsx",
                                        lineNumber: 135,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 133,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex justify-between",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Direction"
                                    }, void 0, false, {
                                        fileName: "[project]/components/BiasMeter.tsx",
                                        lineNumber: 138,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "font-medium capitalize",
                                        children: direction || 'neutral'
                                    }, void 0, false, {
                                        fileName: "[project]/components/BiasMeter.tsx",
                                        lineNumber: 139,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 137,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex justify-between",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Strength"
                                    }, void 0, false, {
                                        fileName: "[project]/components/BiasMeter.tsx",
                                        lineNumber: 142,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "font-medium capitalize",
                                        children: strength || 'unknown'
                                    }, void 0, false, {
                                        fileName: "[project]/components/BiasMeter.tsx",
                                        lineNumber: 143,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/BiasMeter.tsx",
                                lineNumber: 141,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/BiasMeter.tsx",
                        lineNumber: 128,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/BiasMeter.tsx",
                lineNumber: 126,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/BiasMeter.tsx",
        lineNumber: 74,
        columnNumber: 5
    }, this);
}
_c = BiasMeter;
var _c;
__turbopack_context__.k.register(_c, "BiasMeter");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/ExpectedMoveChart.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>ExpectedMoveChart
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$arrow$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ArrowUp$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/arrow-up.js [client] (ecmascript) <export default as ArrowUp>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$arrow$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ArrowDown$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/arrow-down.js [client] (ecmascript) <export default as ArrowDown>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/target.js [client] (ecmascript) <export default as Target>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$bar$2d$chart$2d$3$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__BarChart3$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/bar-chart-3.js [client] (ecmascript) <export default as BarChart3>");
;
;
function ExpectedMoveChart({ probability }) {
    console.log('🔍 ExpectedMoveChart - Received probability:', probability);
    if (!probability || probability.expected_move === null || probability.expected_move === undefined) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "glass-morphism rounded-2xl p-6 border border-white/10",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center gap-3 mb-4",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$bar$2d$chart$2d$3$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__BarChart3$3e$__["BarChart3"], {
                            className: "w-5 h-5 text-primary-400"
                        }, void 0, false, {
                            fileName: "[project]/components/ExpectedMoveChart.tsx",
                            lineNumber: 24,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                            className: "text-lg font-semibold text-white",
                            children: "Expected Move Analysis"
                        }, void 0, false, {
                            fileName: "[project]/components/ExpectedMoveChart.tsx",
                            lineNumber: 25,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/ExpectedMoveChart.tsx",
                    lineNumber: 23,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center text-muted-foreground",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                            className: "w-8 h-8 mx-auto mb-2 opacity-50"
                        }, void 0, false, {
                            fileName: "[project]/components/ExpectedMoveChart.tsx",
                            lineNumber: 28,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            children: "Expected move data unavailable"
                        }, void 0, false, {
                            fileName: "[project]/components/ExpectedMoveChart.tsx",
                            lineNumber: 29,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/ExpectedMoveChart.tsx",
                    lineNumber: 27,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/ExpectedMoveChart.tsx",
            lineNumber: 22,
            columnNumber: 7
        }, this);
    }
    const { expected_move, upper_1sd, lower_1sd, upper_2sd, lower_2sd, breach_probability, range_hold_probability, volatility_state } = probability;
    const getVolatilityStateColor = (state)=>{
        if (!state) return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
        switch(state.toLowerCase()){
            case 'overpriced':
                return 'text-danger-400 bg-danger-500/20 border-danger-500/30';
            case 'underpriced':
                return 'text-success-400 bg-success-500/20 border-success-500/30';
            default:
                return 'text-blue-400 bg-blue-500/20 border-blue-500/30';
        }
    };
    const getVolatilityStateIcon = (state)=>{
        if (!state) return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
            className: "w-4 h-4"
        }, void 0, false, {
            fileName: "[project]/components/ExpectedMoveChart.tsx",
            lineNumber: 50,
            columnNumber: 24
        }, this);
        switch(state.toLowerCase()){
            case 'overpriced':
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$arrow$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ArrowUp$3e$__["ArrowUp"], {
                    className: "w-4 h-4"
                }, void 0, false, {
                    fileName: "[project]/components/ExpectedMoveChart.tsx",
                    lineNumber: 53,
                    columnNumber: 16
                }, this);
            case 'underpriced':
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$arrow$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__ArrowDown$3e$__["ArrowDown"], {
                    className: "w-4 h-4"
                }, void 0, false, {
                    fileName: "[project]/components/ExpectedMoveChart.tsx",
                    lineNumber: 55,
                    columnNumber: 16
                }, this);
            default:
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                    className: "w-4 h-4"
                }, void 0, false, {
                    fileName: "[project]/components/ExpectedMoveChart.tsx",
                    lineNumber: 57,
                    columnNumber: 16
                }, this);
        }
    };
    const volatilityColor = getVolatilityStateColor(volatility_state);
    const volatilityIcon = getVolatilityStateIcon(volatility_state);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "glass-morphism rounded-2xl p-6 border border-white/10",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center justify-between mb-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center gap-3",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$bar$2d$chart$2d$3$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__BarChart3$3e$__["BarChart3"], {
                                className: "w-5 h-5 text-primary-400"
                            }, void 0, false, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 68,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                className: "text-lg font-semibold text-white",
                                children: "Expected Move Analysis"
                            }, void 0, false, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 69,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                        lineNumber: 67,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: `flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-medium ${volatilityColor}`,
                        children: [
                            volatilityIcon,
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "capitalize",
                                children: volatility_state || 'unknown'
                            }, void 0, false, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 73,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                        lineNumber: 71,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/ExpectedMoveChart.tsx",
                lineNumber: 66,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "space-y-6",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-center",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-3xl font-bold text-primary-400",
                                children: [
                                    "±",
                                    expected_move.toFixed(2)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 79,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-sm text-muted-foreground",
                                children: "Expected Move (1SD)"
                            }, void 0, false, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 82,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                        lineNumber: 78,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "space-y-4",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "p-4 rounded-lg border border-white/10 bg-black/20",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center justify-between mb-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm text-muted-foreground",
                                                children: "1SD Range (68% prob)"
                                            }, void 0, false, {
                                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                                lineNumber: 90,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm font-medium text-blue-400",
                                                children: [
                                                    range_hold_probability?.toFixed(1) || '0.0',
                                                    "%"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                                lineNumber: 91,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                                        lineNumber: 89,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center justify-between text-sm",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-red-400",
                                                children: [
                                                    "↓ ",
                                                    lower_1sd?.toLocaleString('en-IN', {
                                                        minimumFractionDigits: 2,
                                                        maximumFractionDigits: 2
                                                    }) || '0.00'
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                                lineNumber: 96,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-green-400",
                                                children: [
                                                    "↑ ",
                                                    upper_1sd?.toLocaleString('en-IN', {
                                                        minimumFractionDigits: 2,
                                                        maximumFractionDigits: 2
                                                    }) || '0.00'
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                                lineNumber: 99,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                                        lineNumber: 95,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 88,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "p-4 rounded-lg border border-white/10 bg-black/20",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center justify-between mb-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm text-muted-foreground",
                                                children: "2SD Range (95% prob)"
                                            }, void 0, false, {
                                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                                lineNumber: 107,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm font-medium text-warning-400",
                                                children: [
                                                    100 - Number(breach_probability?.toFixed(1) || 0),
                                                    "%"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                                lineNumber: 108,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                                        lineNumber: 106,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center justify-between text-sm",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-red-300",
                                                children: [
                                                    "↓ ",
                                                    lower_2sd?.toLocaleString('en-IN', {
                                                        minimumFractionDigits: 2,
                                                        maximumFractionDigits: 2
                                                    }) || '0.00'
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                                lineNumber: 113,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-green-300",
                                                children: [
                                                    "↑ ",
                                                    upper_2sd?.toLocaleString('en-IN', {
                                                        minimumFractionDigits: 2,
                                                        maximumFractionDigits: 2
                                                    }) || '0.00'
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                                lineNumber: 116,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                                        lineNumber: 112,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 105,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                        lineNumber: 87,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "grid grid-cols-2 gap-4 mt-4",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-center",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-lg font-semibold text-blue-400",
                                        children: [
                                            breach_probability?.toFixed(1) || '0.0',
                                            "%"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                                        lineNumber: 125,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-muted-foreground",
                                        children: "Breach Probability"
                                    }, void 0, false, {
                                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                                        lineNumber: 128,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 124,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-center",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-lg font-semibold text-green-400",
                                        children: [
                                            range_hold_probability?.toFixed(1) || '0.0',
                                            "%"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                                        lineNumber: 133,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-muted-foreground",
                                        children: "Range Hold Probability"
                                    }, void 0, false, {
                                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                                        lineNumber: 136,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/ExpectedMoveChart.tsx",
                                lineNumber: 132,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/ExpectedMoveChart.tsx",
                        lineNumber: 123,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/ExpectedMoveChart.tsx",
                lineNumber: 77,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/ExpectedMoveChart.tsx",
        lineNumber: 65,
        columnNumber: 5
    }, this);
}
_c = ExpectedMoveChart;
var _c;
__turbopack_context__.k.register(_c, "ExpectedMoveChart");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/SignalCards.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>SignalCards
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$alert$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__AlertCircle$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/circle-alert.js [client] (ecmascript) <export default as AlertCircle>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/trending-up.js [client] (ecmascript) <export default as TrendingUp>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/trending-down.js [client] (ecmascript) <export default as TrendingDown>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/target.js [client] (ecmascript) <export default as Target>");
;
;
function SignalCards({ intelligence }) {
    console.log('🔍 SignalCards - Received intelligence:', intelligence);
    if (!intelligence) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "glass-morphism rounded-xl p-6 border border-white/10",
            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "text-center text-muted-foreground",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$alert$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__AlertCircle$3e$__["AlertCircle"], {
                        className: "w-8 h-8 mx-auto mb-2 opacity-50"
                    }, void 0, false, {
                        fileName: "[project]/components/SignalCards.tsx",
                        lineNumber: 41,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        children: "Signal data unavailable"
                    }, void 0, false, {
                        fileName: "[project]/components/SignalCards.tsx",
                        lineNumber: 42,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 40,
                columnNumber: 9
            }, this)
        }, void 0, false, {
            fileName: "[project]/components/SignalCards.tsx",
            lineNumber: 39,
            columnNumber: 7
        }, this);
    }
    const { bias, probability, liquidity } = intelligence;
    const signalCards = [
        {
            title: 'Bias Signal',
            signal: bias?.signal || 'NEUTRAL',
            strength: bias?.strength || 'UNKNOWN',
            confidence: bias?.confidence || 0,
            icon: bias?.label?.toUpperCase() === 'BULLISH' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__["TrendingUp"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 56,
                columnNumber: 56
            }, this) : bias?.label?.toUpperCase() === 'BEARISH' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__["TrendingDown"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 57,
                columnNumber: 57
            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 58,
                columnNumber: 14
            }, this),
            color: bias?.label?.toUpperCase() === 'BULLISH' ? 'success' : bias?.label?.toUpperCase() === 'BEARISH' ? 'danger' : 'warning',
            description: `Market bias indicates ${bias?.label?.toString().toLowerCase() || 'neutral'} sentiment with ${bias?.strength?.toString().toLowerCase() || 'unknown'} conviction.`
        },
        {
            title: 'Expected Move Signal',
            signal: probability?.volatility_state?.toUpperCase() || 'NEUTRAL',
            strength: probability?.expected_move > 0 ? 'MODERATE' : 'WEAK',
            confidence: probability?.range_hold_probability || 0,
            icon: probability?.volatility_state === 'overpriced' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__["TrendingUp"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 68,
                columnNumber: 62
            }, this) : probability?.volatility_state === 'underpriced' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__["TrendingDown"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 69,
                columnNumber: 64
            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 70,
                columnNumber: 14
            }, this),
            color: probability?.volatility_state === 'overpriced' ? 'danger' : probability?.volatility_state === 'underpriced' ? 'success' : 'warning',
            description: `Expected move of ±${probability?.expected_move?.toFixed(2) || '0.00'} indicates ${probability?.volatility_state || 'neutral'} pricing.`
        },
        {
            title: 'Liquidity Signal',
            signal: liquidity?.flow_direction?.toUpperCase() || 'NEUTRAL',
            strength: liquidity?.depth_score > 0.7 ? 'STRONG' : liquidity?.depth_score > 0.4 ? 'MODERATE' : 'WEAK',
            confidence: liquidity?.concentration ? (1 - liquidity.concentration) * 100 : 0,
            icon: liquidity?.flow_direction?.includes('BULLISH') ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__["TrendingUp"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 80,
                columnNumber: 62
            }, this) : liquidity?.flow_direction?.includes('BEARISH') ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__["TrendingDown"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 81,
                columnNumber: 63
            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$circle$2d$alert$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__AlertCircle$3e$__["AlertCircle"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 82,
                columnNumber: 14
            }, this),
            color: liquidity?.flow_direction?.includes('BULLISH') ? 'success' : liquidity?.flow_direction?.includes('BEARISH') ? 'danger' : 'warning',
            description: `Liquidity depth score of ${(liquidity?.depth_score * 100).toFixed(1)}% with ${liquidity?.flow_direction?.toLowerCase() || 'neutral'} flow.`
        },
        {
            title: 'Overall Signal',
            signal: bias?.signal || 'NEUTRAL',
            strength: bias?.strength || 'UNKNOWN',
            confidence: bias?.confidence || 0,
            icon: bias?.label?.toUpperCase() === 'BULLISH' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__["TrendingUp"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 92,
                columnNumber: 56
            }, this) : bias?.label?.toUpperCase() === 'BEARISH' ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__["TrendingDown"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 93,
                columnNumber: 57
            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                className: "w-6 h-6"
            }, void 0, false, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 94,
                columnNumber: 14
            }, this),
            color: bias?.label?.toUpperCase() === 'BULLISH' ? 'success' : bias?.label?.toUpperCase() === 'BEARISH' ? 'danger' : 'warning',
            description: `Overall market bias is ${bias?.label?.toLowerCase() || 'neutral'} with ${bias?.confidence?.toFixed(1) || '0.0'}% confidence.`
        }
    ];
    const getColorClasses = (color)=>{
        const colorMap = {
            success: {
                bg: 'bg-success-500/20',
                border: 'border-success-500/30',
                text: 'text-success-500',
                iconBg: 'bg-success-500'
            },
            danger: {
                bg: 'bg-danger-500/20',
                border: 'border-danger-500/30',
                text: 'text-danger-500',
                iconBg: 'bg-danger-500'
            },
            warning: {
                bg: 'bg-warning-500/20',
                border: 'border-warning-500/30',
                text: 'text-warning-500',
                iconBg: 'bg-warning-500'
            }
        };
        return colorMap[color] || colorMap.warning;
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4",
        children: signalCards.map((card, index)=>{
            const colors = getColorClasses(card.color);
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "glass-morphism rounded-xl p-6 border border-white/10",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-start justify-between mb-4",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                        className: "text-sm font-medium text-muted-foreground mb-1",
                                        children: card.title
                                    }, void 0, false, {
                                        fileName: "[project]/components/SignalCards.tsx",
                                        lineNumber: 134,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: `text-lg font-bold ${colors.text}`,
                                        children: card.signal
                                    }, void 0, false, {
                                        fileName: "[project]/components/SignalCards.tsx",
                                        lineNumber: 137,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/SignalCards.tsx",
                                lineNumber: 133,
                                columnNumber: 15
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: `p-2 rounded-lg ${colors.iconBg} text-white`,
                                children: card.icon
                            }, void 0, false, {
                                fileName: "[project]/components/SignalCards.tsx",
                                lineNumber: 141,
                                columnNumber: 15
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/SignalCards.tsx",
                        lineNumber: 132,
                        columnNumber: 13
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "space-y-3",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex justify-between text-sm mb-1",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-muted-foreground",
                                                children: "Strength"
                                            }, void 0, false, {
                                                fileName: "[project]/components/SignalCards.tsx",
                                                lineNumber: 149,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "font-medium capitalize",
                                                children: typeof card.strength === 'string' ? card.strength.toLowerCase() : card.strength.toString()
                                            }, void 0, false, {
                                                fileName: "[project]/components/SignalCards.tsx",
                                                lineNumber: 150,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/SignalCards.tsx",
                                        lineNumber: 148,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "w-full bg-black/30 rounded-full h-2",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: `h-2 rounded-full transition-all duration-500 ${card.strength === 'STRONG' ? 'w-4/5' : card.strength === 'MODERATE' ? 'w-1/2' : 'w-1/4'} ${colors.iconBg}`
                                        }, void 0, false, {
                                            fileName: "[project]/components/SignalCards.tsx",
                                            lineNumber: 153,
                                            columnNumber: 19
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/components/SignalCards.tsx",
                                        lineNumber: 152,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/SignalCards.tsx",
                                lineNumber: 147,
                                columnNumber: 15
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex justify-between text-sm mb-1",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-muted-foreground",
                                                children: "Confidence"
                                            }, void 0, false, {
                                                fileName: "[project]/components/SignalCards.tsx",
                                                lineNumber: 164,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "font-medium",
                                                children: [
                                                    card.confidence.toFixed(0),
                                                    "%"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/SignalCards.tsx",
                                                lineNumber: 165,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/SignalCards.tsx",
                                        lineNumber: 163,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "w-full bg-black/30 rounded-full h-2",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: `h-2 rounded-full transition-all duration-500 ${colors.iconBg}`,
                                            style: {
                                                width: `${Math.min(card.confidence, 100)}%`
                                            }
                                        }, void 0, false, {
                                            fileName: "[project]/components/SignalCards.tsx",
                                            lineNumber: 168,
                                            columnNumber: 19
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/components/SignalCards.tsx",
                                        lineNumber: 167,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/SignalCards.tsx",
                                lineNumber: 162,
                                columnNumber: 15
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/SignalCards.tsx",
                        lineNumber: 146,
                        columnNumber: 13
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-4 pt-4 border-t border-white/10",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-xs text-muted-foreground leading-relaxed",
                            children: card.description
                        }, void 0, false, {
                            fileName: "[project]/components/SignalCards.tsx",
                            lineNumber: 177,
                            columnNumber: 15
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/components/SignalCards.tsx",
                        lineNumber: 176,
                        columnNumber: 13
                    }, this)
                ]
            }, index, true, {
                fileName: "[project]/components/SignalCards.tsx",
                lineNumber: 131,
                columnNumber: 11
            }, this);
        })
    }, void 0, false, {
        fileName: "[project]/components/SignalCards.tsx",
        lineNumber: 126,
        columnNumber: 5
    }, this);
}
_c = SignalCards;
var _c;
__turbopack_context__.k.register(_c, "SignalCards");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/InstitutionalBias.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>InstitutionalBias
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/trending-up.js [client] (ecmascript) <export default as TrendingUp>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/trending-down.js [client] (ecmascript) <export default as TrendingDown>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$minus$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Minus$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/minus.js [client] (ecmascript) <export default as Minus>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/target.js [client] (ecmascript) <export default as Target>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$activity$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Activity$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/activity.js [client] (ecmascript) <export default as Activity>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$zap$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Zap$3e$__ = __turbopack_context__.i("[project]/node_modules/lucide-react/dist/esm/icons/zap.js [client] (ecmascript) <export default as Zap>");
;
;
function InstitutionalBias({ intelligence, spotPrice, marketStatus, marketChange, marketChangePercent }) {
    console.log('🔍 InstitutionalBias - Received intelligence:', intelligence);
    if (!intelligence) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "glass-morphism rounded-2xl p-6 border border-white/10",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center gap-3 mb-4",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                            className: "w-5 h-5 text-primary-400"
                        }, void 0, false, {
                            fileName: "[project]/components/InstitutionalBias.tsx",
                            lineNumber: 42,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                            className: "text-lg font-semibold text-white",
                            children: "Institutional Bias"
                        }, void 0, false, {
                            fileName: "[project]/components/InstitutionalBias.tsx",
                            lineNumber: 43,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/InstitutionalBias.tsx",
                    lineNumber: 41,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "text-center text-muted-foreground",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$activity$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Activity$3e$__["Activity"], {
                            className: "w-8 h-8 mx-auto mb-2 opacity-50"
                        }, void 0, false, {
                            fileName: "[project]/components/InstitutionalBias.tsx",
                            lineNumber: 46,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            children: "Loading intelligence..."
                        }, void 0, false, {
                            fileName: "[project]/components/InstitutionalBias.tsx",
                            lineNumber: 47,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/InstitutionalBias.tsx",
                    lineNumber: 45,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/InstitutionalBias.tsx",
            lineNumber: 40,
            columnNumber: 7
        }, this);
    }
    const biasScore = intelligence.bias?.score ?? 0;
    const biasLabel = intelligence.bias?.label ?? "NEUTRAL";
    const oiDominance = intelligence.liquidity?.concentration ? (intelligence.liquidity.concentration - 0.5) * 2 : 0;
    const positionScore = intelligence.liquidity?.depth_score ? intelligence.liquidity.depth_score - 0.5 : 0;
    const strongestSupport = 0; // This would be part of analytics in full implementation
    const strongestResistance = 0; // This would be part of analytics in full implementation
    // Direction indicator
    const getDirectionIcon = ()=>{
        if (biasLabel.includes("BULL")) {
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$up$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingUp$3e$__["TrendingUp"], {
                className: "w-6 h-6 text-success-500"
            }, void 0, false, {
                fileName: "[project]/components/InstitutionalBias.tsx",
                lineNumber: 63,
                columnNumber: 14
            }, this);
        } else if (biasLabel.includes("BEAR")) {
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$trending$2d$down$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__TrendingDown$3e$__["TrendingDown"], {
                className: "w-6 h-6 text-danger-500"
            }, void 0, false, {
                fileName: "[project]/components/InstitutionalBias.tsx",
                lineNumber: 65,
                columnNumber: 14
            }, this);
        } else {
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$minus$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Minus$3e$__["Minus"], {
                className: "w-6 h-6 text-warning-500"
            }, void 0, false, {
                fileName: "[project]/components/InstitutionalBias.tsx",
                lineNumber: 67,
                columnNumber: 14
            }, this);
        }
    };
    // Color scheme based on bias
    const getBiasColorScheme = ()=>{
        if (biasLabel.includes("BULL")) {
            return {
                bg: "bg-gradient-to-br from-success-500/20 to-emerald-500/10",
                border: "border-success-500/30",
                glow: "shadow-success-500/20",
                bar: "bg-gradient-to-r from-success-500 to-emerald-500"
            };
        } else if (biasLabel.includes("BEAR")) {
            return {
                bg: "bg-gradient-to-br from-danger-500/20 to-red-500/10",
                border: "border-danger-500/30",
                glow: "shadow-danger-500/20",
                bar: "bg-gradient-to-r from-danger-500 to-red-500"
            };
        } else {
            return {
                bg: "bg-gradient-to-br from-warning-500/20 to-amber-500/10",
                border: "border-warning-500/30",
                glow: "shadow-warning-500/20",
                bar: "bg-gradient-to-r from-warning-500 to-amber-500"
            };
        }
    };
    const colorScheme = getBiasColorScheme();
    // Generate insight sentence
    const generateInsight = ()=>{
        if (biasLabel.includes("BULL")) {
            return `Institutions are aggressively positioning for upside above ${strongestResistance.toLocaleString('en-IN')}.`;
        } else if (biasLabel.includes("BEAR")) {
            return `Strong put dominance at ${strongestSupport.toLocaleString('en-IN')} strike indicates defensive positioning.`;
        } else {
            return `Balanced institutional activity around current price levels.`;
        }
    };
    const getSecondaryInsight = ()=>{
        if (Math.abs(oiDominance) > 0.3) {
            return `${Math.abs(oiDominance * 100).toFixed(1)}% ${oiDominance > 0 ? 'put' : 'call'} dominance detected.`;
        } else {
            return `OI balance suggests ${biasLabel.toLowerCase()} market structure.`;
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: `glass-morphism rounded-2xl p-6 border ${colorScheme.border} ${colorScheme.bg} ${colorScheme.glow} shadow-2xl relative overflow-hidden lg:sticky lg:top-6`,
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: `absolute inset-0 bg-gradient-to-br ${biasLabel.includes("BULL") ? 'from-success-500/5 to-emerald-500/5' : biasLabel.includes("BEAR") ? 'from-danger-500/5 to-red-500/5' : 'from-warning-500/5 to-amber-500/5'} opacity-50`
            }, void 0, false, {
                fileName: "[project]/components/InstitutionalBias.tsx",
                lineNumber: 121,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "relative z-10",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center justify-between mb-6",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-3",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                                        className: "w-5 h-5 text-primary-400"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 128,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                        className: "text-xl font-bold text-white tracking-wide",
                                        children: "Institutional Bias"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 129,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 127,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-4",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center gap-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: `w-2 h-2 rounded-full ${marketStatus === 'OPEN' ? 'bg-success-500' : 'bg-danger-500'}`
                                            }, void 0, false, {
                                                fileName: "[project]/components/InstitutionalBias.tsx",
                                                lineNumber: 134,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "capitalize text-xs text-muted-foreground",
                                                children: marketStatus || 'Loading...'
                                            }, void 0, false, {
                                                fileName: "[project]/components/InstitutionalBias.tsx",
                                                lineNumber: 137,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 133,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-right",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "text-2xl font-black text-white",
                                                children: spotPrice ? `₹${spotPrice.toLocaleString('en-IN', {
                                                    minimumFractionDigits: 2,
                                                    maximumFractionDigits: 2
                                                })}` : '₹--'
                                            }, void 0, false, {
                                                fileName: "[project]/components/InstitutionalBias.tsx",
                                                lineNumber: 143,
                                                columnNumber: 15
                                            }, this),
                                            marketChange !== undefined && marketChange !== null && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: `text-sm font-bold ${marketChange >= 0 ? 'text-success-500' : 'text-danger-500'}`,
                                                children: [
                                                    marketChange >= 0 ? '+' : '',
                                                    marketChange.toFixed(2),
                                                    " (",
                                                    marketChangePercent && marketChangePercent >= 0 ? '+' : '',
                                                    marketChangePercent ? (marketChangePercent * 100).toFixed(2) : '0.00',
                                                    "%)"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/components/InstitutionalBias.tsx",
                                                lineNumber: 150,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 142,
                                        columnNumber: 13
                                    }, this),
                                    getDirectionIcon(),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: `px-4 py-2 rounded-full font-bold text-sm ${biasLabel.includes("BULL") ? "bg-success-500/20 text-success-400 border border-success-500/30" : biasLabel.includes("BEAR") ? "bg-danger-500/20 text-danger-400 border border-danger-500/30" : "bg-warning-500/20 text-warning-400 border border-warning-500/30"}`,
                                        children: biasLabel.replace("_", " ")
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 159,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 131,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/InstitutionalBias.tsx",
                        lineNumber: 126,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-center mb-8",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-7xl font-black text-white mb-1 tracking-tight",
                                children: [
                                    biasScore,
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-2xl font-light text-white/50",
                                        children: "/100"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 173,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 171,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-sm text-muted-foreground mb-4",
                                children: "Bias Strength Score"
                            }, void 0, false, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 175,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "w-full h-4 bg-black/30 rounded-full overflow-hidden backdrop-blur-sm",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: `h-full ${colorScheme.bar} transition-all duration-1000 ease-out relative overflow-hidden`,
                                    style: {
                                        width: `${biasScore}%`
                                    },
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 184,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/components/InstitutionalBias.tsx",
                                    lineNumber: 179,
                                    columnNumber: 13
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 178,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/InstitutionalBias.tsx",
                        lineNumber: 170,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mb-6 p-4 rounded-xl border border-white/10 bg-black/20 backdrop-blur-sm",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center justify-between mb-3",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center gap-2",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$zap$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Zap$3e$__["Zap"], {
                                                className: "w-4 h-4 text-primary-400"
                                            }, void 0, false, {
                                                fileName: "[project]/components/InstitutionalBias.tsx",
                                                lineNumber: 193,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm font-medium text-white",
                                                children: "Volatility Regime"
                                            }, void 0, false, {
                                                fileName: "[project]/components/InstitutionalBias.tsx",
                                                lineNumber: 194,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 192,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: `px-3 py-1 rounded-full text-xs font-bold ${intelligence.volatility.current === 'extreme' ? 'bg-danger-500/20 text-danger-400 border border-danger-500/30' : intelligence.volatility.current === 'elevated' ? 'bg-warning-500/20 text-warning-400 border border-warning-500/30' : intelligence.volatility.current === 'normal' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30' : 'bg-success-500/20 text-success-400 border border-success-500/30'}`,
                                        children: intelligence.volatility.current.toUpperCase()
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 196,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 191,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center justify-between text-sm",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Risk Environment"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 207,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: `font-medium capitalize ${intelligence.volatility.risk === 'extreme' ? 'text-danger-400' : intelligence.volatility.risk === 'high' ? 'text-warning-400' : intelligence.volatility.risk === 'medium' ? 'text-blue-400' : 'text-success-400'}`,
                                        children: intelligence.volatility.risk
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 208,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 206,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center justify-between text-sm mt-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "text-muted-foreground",
                                        children: "Market Phase"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 219,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        className: "font-medium capitalize text-primary-400",
                                        children: intelligence.volatility.environment
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 220,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 218,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/InstitutionalBias.tsx",
                        lineNumber: 190,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "space-y-4 mb-6",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-start gap-3",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$activity$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Activity$3e$__["Activity"], {
                                        className: "w-4 h-4 text-primary-400 mt-0.5 flex-shrink-0"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 229,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "text-sm text-white leading-relaxed",
                                        children: generateInsight()
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 230,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 228,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-start gap-3",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$lucide$2d$react$2f$dist$2f$esm$2f$icons$2f$target$2e$js__$5b$client$5d$__$28$ecmascript$29$__$3c$export__default__as__Target$3e$__["Target"], {
                                        className: "w-4 h-4 text-primary-400 mt-0.5 flex-shrink-0"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 235,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "text-sm text-muted-foreground leading-relaxed",
                                        children: getSecondaryInsight()
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 236,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 234,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/InstitutionalBias.tsx",
                        lineNumber: 227,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "grid grid-cols-2 gap-4 pt-4 border-t border-white/10",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-center",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: `text-lg font-bold ${oiDominance > 0 ? "text-success-400" : "text-danger-400"}`,
                                        children: [
                                            (Math.abs(oiDominance) * 100).toFixed(1),
                                            "%"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 245,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-muted-foreground",
                                        children: [
                                            "OI ",
                                            oiDominance > 0 ? 'Put' : 'Call',
                                            " Dom"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 250,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 244,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-center",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: `text-lg font-bold ${positionScore > 0 ? "text-success-400" : "text-danger-400"}`,
                                        children: [
                                            (Math.abs(positionScore) * 100).toFixed(1),
                                            "%"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 253,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "text-xs text-muted-foreground",
                                        children: "Position"
                                    }, void 0, false, {
                                        fileName: "[project]/components/InstitutionalBias.tsx",
                                        lineNumber: 258,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/components/InstitutionalBias.tsx",
                                lineNumber: 252,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/InstitutionalBias.tsx",
                        lineNumber: 243,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/InstitutionalBias.tsx",
                lineNumber: 124,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/InstitutionalBias.tsx",
        lineNumber: 119,
        columnNumber: 5
    }, this);
}
_c = InstitutionalBias;
var _c;
__turbopack_context__.k.register(_c, "InstitutionalBias");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/AuthScreen.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>__TURBOPACK__default__export__
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = /*#__PURE__*/ __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/index.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$contexts$2f$AuthContext$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/contexts/AuthContext.tsx [client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
;
;
function AuthScreen({ authData }) {
    _s();
    const { checkAuth } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$contexts$2f$AuthContext$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["useAuth"])();
    const handleReconnect = async ()=>{
        // Stop any existing polling
        const event = new CustomEvent('stopPolling');
        window.dispatchEvent(event);
        try {
            // Get the actual Upstox auth URL from backend
            // Use absolute URL to ensure it hits the backend on port 8000
            const baseUrl = ("TURBOPACK compile-time value", "http://localhost:8000") || 'http://localhost:8000';
            const authUrl = authData.login_url.startsWith('http') ? authData.login_url : `${baseUrl}${authData.login_url}`;
            console.log('🔍 AuthScreen: Fetching auth URL from:', authUrl);
            const response = await fetch(authUrl);
            // Check if response is a redirect (direct URL) or JSON
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                // JSON response - parse it
                const result = await response.json();
                if (result.status === 'success' && result.data?.authorization_url) {
                    window.location.href = result.data.authorization_url;
                } else {
                    console.error('Failed to get auth URL:', result);
                    alert('Failed to get authentication URL. Please try again.');
                }
            } else {
                // Direct URL response - redirect to it
                const url = await response.text();
                console.log('🔍 AuthScreen: Got direct URL, redirecting to:', url);
                window.location.href = url;
            }
        } catch (error) {
            console.error('Error getting auth URL:', error);
            alert('Error getting authentication URL. Please try again.');
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "max-w-md w-full mx-4",
            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "glass-morphism rounded-2xl p-8 text-center",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "w-20 h-20 bg-orange-500 rounded-full flex items-center justify-center mx-auto mb-6",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                            className: "w-10 h-10 text-white",
                            fill: "none",
                            stroke: "currentColor",
                            viewBox: "0 0 24 24",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                strokeLinecap: "round",
                                strokeLinejoin: "round",
                                strokeWidth: 2,
                                d: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                            }, void 0, false, {
                                fileName: "[project]/components/AuthScreen.tsx",
                                lineNumber: 64,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/components/AuthScreen.tsx",
                            lineNumber: 58,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/components/AuthScreen.tsx",
                        lineNumber: 57,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                        className: "text-3xl font-bold text-white mb-2",
                        children: "Authentication Required"
                    }, void 0, false, {
                        fileName: "[project]/components/AuthScreen.tsx",
                        lineNumber: 74,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "text-gray-300 mb-8 leading-relaxed",
                        children: authData.message
                    }, void 0, false, {
                        fileName: "[project]/components/AuthScreen.tsx",
                        lineNumber: 79,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "inline-flex items-center gap-2 bg-orange-500/20 text-orange-400 px-4 py-2 rounded-full mb-8",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "w-2 h-2 bg-orange-400 rounded-full animate-pulse"
                            }, void 0, false, {
                                fileName: "[project]/components/AuthScreen.tsx",
                                lineNumber: 85,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                className: "text-sm font-medium",
                                children: "Session Expired"
                            }, void 0, false, {
                                fileName: "[project]/components/AuthScreen.tsx",
                                lineNumber: 86,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/AuthScreen.tsx",
                        lineNumber: 84,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                        onClick: handleReconnect,
                        className: "w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 transform hover:scale-105 shadow-lg hover:shadow-orange-500/25",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center justify-center gap-3",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                    className: "w-5 h-5",
                                    fill: "none",
                                    stroke: "currentColor",
                                    viewBox: "0 0 24 24",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                        strokeLinecap: "round",
                                        strokeLinejoin: "round",
                                        strokeWidth: 2,
                                        d: "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                                    }, void 0, false, {
                                        fileName: "[project]/components/AuthScreen.tsx",
                                        lineNumber: 101,
                                        columnNumber: 17
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/components/AuthScreen.tsx",
                                    lineNumber: 95,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    children: "Get Authorization"
                                }, void 0, false, {
                                    fileName: "[project]/components/AuthScreen.tsx",
                                    lineNumber: 108,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/components/AuthScreen.tsx",
                            lineNumber: 94,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/components/AuthScreen.tsx",
                        lineNumber: 90,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-6 text-sm text-gray-400",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                children: "You'll be redirected to the authorization server."
                            }, void 0, false, {
                                fileName: "[project]/components/AuthScreen.tsx",
                                lineNumber: 114,
                                columnNumber: 13
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "mt-1",
                                children: "After authorization, you'll be returned here automatically."
                            }, void 0, false, {
                                fileName: "[project]/components/AuthScreen.tsx",
                                lineNumber: 115,
                                columnNumber: 13
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/AuthScreen.tsx",
                        lineNumber: 113,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-8 pt-6 border-t border-gray-700",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-xs text-gray-500",
                            children: [
                                "Detected at: ",
                                new Date(authData.timestamp).toLocaleString()
                            ]
                        }, void 0, true, {
                            fileName: "[project]/components/AuthScreen.tsx",
                            lineNumber: 120,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/components/AuthScreen.tsx",
                        lineNumber: 119,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/AuthScreen.tsx",
                lineNumber: 55,
                columnNumber: 9
            }, this)
        }, void 0, false, {
            fileName: "[project]/components/AuthScreen.tsx",
            lineNumber: 54,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/components/AuthScreen.tsx",
        lineNumber: 53,
        columnNumber: 5
    }, this);
}
_s(AuthScreen, "6Y0yrwAoWqcNL/V7fsysn8AlgCY=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$contexts$2f$AuthContext$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["useAuth"]
    ];
});
_c = AuthScreen;
const __TURBOPACK__default__export__ = /*#__PURE__*/ _c1 = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["default"].memo(AuthScreen);
var _c, _c1;
__turbopack_context__.k.register(_c, "AuthScreen");
__turbopack_context__.k.register(_c1, "%default%");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/components/Dashboard.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>DashboardComponent
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/index.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$hooks$2f$useLiveMarketData$2e$ts__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/hooks/useLiveMarketData.ts [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$contexts$2f$AuthContext$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/contexts/AuthContext.tsx [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$MarketMetrics$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/MarketMetrics.tsx [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$OIHeatmap$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/OIHeatmap.tsx [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$AIInterpretationPanel$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/AIInterpretationPanel.tsx [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BiasMeter$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/BiasMeter.tsx [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$ExpectedMoveChart$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/ExpectedMoveChart.tsx [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$SignalCards$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/SignalCards.tsx [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$InstitutionalBias$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/InstitutionalBias.tsx [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$AuthScreen$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/AuthScreen.tsx [client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
;
;
;
;
;
;
;
// Debug component to show connection status
function DebugPanel({ data, symbol }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "mb-6 p-4 bg-black/20 rounded-lg border border-white/10",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                className: "text-sm font-medium text-white mb-2",
                children: "CONNECTION STATUS"
            }, void 0, false, {
                fileName: "[project]/components/Dashboard.tsx",
                lineNumber: 20,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "text-xs text-gray-300 space-y-1",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Symbol: ",
                            symbol
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 22,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Market Status: ",
                            data?.market_status || 'UNKNOWN'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 23,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Spot Price: ",
                            data?.spot || 'N/A'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 24,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Data Source: ",
                            data?.source || 'Unknown'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 25,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Timestamp: ",
                            data?.timestamp || 'N/A'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 26,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Mode: ",
                            data?.mode || 'Unknown'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 27,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Analytics: ",
                            data?.analytics ? 'Present' : 'Missing'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 28,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Intelligence: ",
                            data?.intelligence ? 'Present' : 'Missing'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 29,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Total Call OI: ",
                            data?.analytics?.total_call_oi || 'N/A'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 30,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        children: [
                            "Total Put OI: ",
                            data?.analytics?.total_put_oi || 'N/A'
                        ]
                    }, void 0, true, {
                        fileName: "[project]/components/Dashboard.tsx",
                        lineNumber: 31,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/components/Dashboard.tsx",
                lineNumber: 21,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/components/Dashboard.tsx",
        lineNumber: 19,
        columnNumber: 5
    }, this);
}
_c = DebugPanel;
// Loading component
function ErrorBlock({ message, onRetry }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "text-center text-white",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "w-16 h-16 border-4 border-red-500 border-t-transparent rounded-full mx-auto mb-4"
                }, void 0, false, {
                    fileName: "[project]/components/Dashboard.tsx",
                    lineNumber: 42,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                    className: "mb-4",
                    children: message
                }, void 0, false, {
                    fileName: "[project]/components/Dashboard.tsx",
                    lineNumber: 43,
                    columnNumber: 9
                }, this),
                onRetry && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: onRetry,
                    className: "px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors",
                    children: "Retry"
                }, void 0, false, {
                    fileName: "[project]/components/Dashboard.tsx",
                    lineNumber: 45,
                    columnNumber: 11
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/Dashboard.tsx",
            lineNumber: 41,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/components/Dashboard.tsx",
        lineNumber: 40,
        columnNumber: 5
    }, this);
}
_c1 = ErrorBlock;
function DashboardComponent({ symbol }) {
    _s();
    console.log('🔍 DashboardComponent - Render called with symbol:', symbol);
    // Use AuthContext instead of local state
    const { state: authState } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$contexts$2f$AuthContext$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["useAuth"])();
    const today = new Date().toISOString().split('T')[0];
    const selectedExpiry = today;
    const { data, loading, error } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$hooks$2f$useLiveMarketData$2e$ts__$5b$client$5d$__$28$ecmascript$29$__["useLiveMarketData"])(symbol, selectedExpiry);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "DashboardComponent.useEffect": ()=>{
            const handleAuthExpired = {
                "DashboardComponent.useEffect.handleAuthExpired": ()=>{
                    console.log('🔐 DashboardComponent - Auth expired event received');
                }
            }["DashboardComponent.useEffect.handleAuthExpired"];
            window.addEventListener('auth-expired', handleAuthExpired);
            return ({
                "DashboardComponent.useEffect": ()=>{
                    window.removeEventListener('auth-expired', handleAuthExpired);
                }
            })["DashboardComponent.useEffect"];
        }
    }["DashboardComponent.useEffect"], []);
    // Authentication checks
    if (!authState.isAuthenticated && authState.mode === 'AUTH') {
        console.log('🔐 DashboardComponent - Not authenticated (AuthContext), showing AuthScreen');
        const authData = {
            session_type: 'AUTH_REQUIRED',
            mode: 'AUTH',
            message: authState.error || 'Authentication required',
            login_url: '/api/v1/auth/upstox',
            timestamp: new Date().toISOString()
        };
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$AuthScreen$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
            authData: authData
        }, void 0, false, {
            fileName: "[project]/components/Dashboard.tsx",
            lineNumber: 88,
            columnNumber: 12
        }, this);
    }
    // Show loading if AuthContext is checking
    if (authState.isLoading) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ErrorBlock, {
            message: "Checking authentication..."
        }, void 0, false, {
            fileName: "[project]/components/Dashboard.tsx",
            lineNumber: 93,
            columnNumber: 12
        }, this);
    }
    // Data loading and error states
    if (loading) {
        console.log('🔍 DashboardComponent - Loading market data...');
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ErrorBlock, {
            message: "Loading market data..."
        }, void 0, false, {
            fileName: "[project]/components/Dashboard.tsx",
            lineNumber: 99,
            columnNumber: 12
        }, this);
    }
    if (error) {
        console.log('🔍 DashboardComponent - Error:', error);
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ErrorBlock, {
            message: error,
            onRetry: ()=>window.location.reload()
        }, void 0, false, {
            fileName: "[project]/components/Dashboard.tsx",
            lineNumber: 104,
            columnNumber: 12
        }, this);
    }
    if (!data) {
        console.log('🔍 DashboardComponent - No data available');
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ErrorBlock, {
            message: "Waiting for market data..."
        }, void 0, false, {
            fileName: "[project]/components/Dashboard.tsx",
            lineNumber: 109,
            columnNumber: 12
        }, this);
    }
    // Market status
    const marketStatus = data?.market_status || 'UNKNOWN';
    const isMarketOpen = marketStatus === 'OPEN';
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "container mx-auto px-4 py-6",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "mb-8 text-center",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                            className: "text-4xl font-black text-white mb-2",
                            children: "StrikeIQ"
                        }, void 0, false, {
                            fileName: "[project]/components/Dashboard.tsx",
                            lineNumber: 121,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-xl text-gray-300 mb-4",
                            children: "Options Intelligence Dashboard"
                        }, void 0, false, {
                            fileName: "[project]/components/Dashboard.tsx",
                            lineNumber: 124,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center justify-center gap-4 mb-6",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: `px-4 py-2 rounded-full text-sm font-medium ${isMarketOpen ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`,
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "w-2 h-2 rounded-full mr-2 bg-current"
                                        }, void 0, false, {
                                            fileName: "[project]/components/Dashboard.tsx",
                                            lineNumber: 133,
                                            columnNumber: 15
                                        }, this),
                                        "Market ",
                                        isMarketOpen ? 'Open' : 'Closed'
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/components/Dashboard.tsx",
                                    lineNumber: 128,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "text-sm text-gray-400",
                                    children: [
                                        "Last updated: ",
                                        new Date().toLocaleTimeString()
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/components/Dashboard.tsx",
                                    lineNumber: 136,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/components/Dashboard.tsx",
                            lineNumber: 127,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/Dashboard.tsx",
                    lineNumber: 120,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(DebugPanel, {
                    data: data,
                    symbol: symbol
                }, void 0, false, {
                    fileName: "[project]/components/Dashboard.tsx",
                    lineNumber: 143,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "grid grid-cols-1 xl:grid-cols-12 gap-6",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "xl:col-span-8 space-y-6",
                            children: [
                                data?.analytics && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$MarketMetrics$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                                    analytics: data.analytics
                                }, void 0, false, {
                                    fileName: "[project]/components/Dashboard.tsx",
                                    lineNumber: 151,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$OIHeatmap$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                                    symbol: symbol,
                                    liveData: data
                                }, void 0, false, {
                                    fileName: "[project]/components/Dashboard.tsx",
                                    lineNumber: 155,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "grid grid-cols-1 lg:grid-cols-2 gap-6",
                                    children: data?.intelligence && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["Fragment"], {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$BiasMeter$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                                                intelligence: data.intelligence
                                            }, void 0, false, {
                                                fileName: "[project]/components/Dashboard.tsx",
                                                lineNumber: 161,
                                                columnNumber: 19
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$ExpectedMoveChart$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                                                probability: data.intelligence?.probability
                                            }, void 0, false, {
                                                fileName: "[project]/components/Dashboard.tsx",
                                                lineNumber: 162,
                                                columnNumber: 19
                                            }, this)
                                        ]
                                    }, void 0, true)
                                }, void 0, false, {
                                    fileName: "[project]/components/Dashboard.tsx",
                                    lineNumber: 158,
                                    columnNumber: 13
                                }, this),
                                data?.intelligence && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$SignalCards$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                                    intelligence: data.intelligence
                                }, void 0, false, {
                                    fileName: "[project]/components/Dashboard.tsx",
                                    lineNumber: 169,
                                    columnNumber: 15
                                }, this),
                                data?.intelligence && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$AIInterpretationPanel$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                                    intelligence: data.intelligence
                                }, void 0, false, {
                                    fileName: "[project]/components/Dashboard.tsx",
                                    lineNumber: 174,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/components/Dashboard.tsx",
                            lineNumber: 148,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "xl:col-span-4",
                            children: data?.intelligence && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$InstitutionalBias$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                                intelligence: data.intelligence,
                                spotPrice: data.spot,
                                marketStatus: marketStatus,
                                marketChange: data.change,
                                marketChangePercent: data.change_percent
                            }, void 0, false, {
                                fileName: "[project]/components/Dashboard.tsx",
                                lineNumber: 181,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/components/Dashboard.tsx",
                            lineNumber: 179,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/components/Dashboard.tsx",
                    lineNumber: 146,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/components/Dashboard.tsx",
            lineNumber: 118,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/components/Dashboard.tsx",
        lineNumber: 117,
        columnNumber: 5
    }, this);
}
_s(DashboardComponent, "hC5tG7eR4Hudgq0rB9BeOWwBHaE=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$contexts$2f$AuthContext$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["useAuth"],
        __TURBOPACK__imported__module__$5b$project$5d2f$hooks$2f$useLiveMarketData$2e$ts__$5b$client$5d$__$28$ecmascript$29$__["useLiveMarketData"]
    ];
});
_c2 = DashboardComponent;
var _c, _c1, _c2;
__turbopack_context__.k.register(_c, "DebugPanel");
__turbopack_context__.k.register(_c1, "ErrorBlock");
__turbopack_context__.k.register(_c2, "DashboardComponent");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/pages/index.tsx [client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>Home
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/jsx-dev-runtime.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/react/index.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$head$2e$js__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/head.js [client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Dashboard$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/components/Dashboard.tsx [client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
;
;
;
function Home() {
    _s();
    const [selectedSymbol, setSelectedSymbol] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$index$2e$js__$5b$client$5d$__$28$ecmascript$29$__["useState"])('NIFTY');
    console.log('🔍 Home page - Rendered with symbol:', selectedSymbol);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["Fragment"], {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$head$2e$js__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("title", {
                        children: "StrikeIQ - Options Market Intelligence"
                    }, void 0, false, {
                        fileName: "[project]/pages/index.tsx",
                        lineNumber: 13,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("meta", {
                        name: "description",
                        content: "AI-powered options market intelligence for Indian markets"
                    }, void 0, false, {
                        fileName: "[project]/pages/index.tsx",
                        lineNumber: 14,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("meta", {
                        name: "viewport",
                        content: "width=device-width, initial-scale=1"
                    }, void 0, false, {
                        fileName: "[project]/pages/index.tsx",
                        lineNumber: 15,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("link", {
                        rel: "icon",
                        href: "/favicon.ico"
                    }, void 0, false, {
                        fileName: "[project]/pages/index.tsx",
                        lineNumber: 16,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/pages/index.tsx",
                lineNumber: 12,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("main", {
                className: "min-h-screen bg-background text-foreground",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "container mx-auto px-4 py-6",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("header", {
                            className: "mb-8",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center justify-between",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                                                className: "text-4xl font-bold text-gradient mb-2",
                                                children: "StrikeIQ"
                                            }, void 0, false, {
                                                fileName: "[project]/pages/index.tsx",
                                                lineNumber: 24,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                className: "text-muted-foreground",
                                                children: "AI-Powered Options Market Intelligence"
                                            }, void 0, false, {
                                                fileName: "[project]/pages/index.tsx",
                                                lineNumber: 25,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/pages/index.tsx",
                                        lineNumber: 23,
                                        columnNumber: 15
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "flex items-center gap-4",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                            value: selectedSymbol,
                                            onChange: (e)=>{
                                                console.log('🔄 Symbol changed from', selectedSymbol, 'to', e.target.value);
                                                setSelectedSymbol(e.target.value);
                                            },
                                            className: "glass-morphism px-4 py-2 rounded-lg border border-white/10 focus:outline-none focus:ring-2 focus:ring-primary-500",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                    value: "NIFTY",
                                                    children: "NIFTY"
                                                }, void 0, false, {
                                                    fileName: "[project]/pages/index.tsx",
                                                    lineNumber: 37,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                    value: "BANKNIFTY",
                                                    children: "BANKNIFTY"
                                                }, void 0, false, {
                                                    fileName: "[project]/pages/index.tsx",
                                                    lineNumber: 38,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/pages/index.tsx",
                                            lineNumber: 29,
                                            columnNumber: 17
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/pages/index.tsx",
                                        lineNumber: 28,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/pages/index.tsx",
                                lineNumber: 22,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/pages/index.tsx",
                            lineNumber: 21,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mb-4 p-4 bg-yellow-500/20 border border-yellow-500 rounded-lg",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-yellow-300 text-sm font-medium",
                                children: "🧪 TEST: DashboardComponent should render below this line"
                            }, void 0, false, {
                                fileName: "[project]/pages/index.tsx",
                                lineNumber: 46,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/pages/index.tsx",
                            lineNumber: 45,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$components$2f$Dashboard$2e$tsx__$5b$client$5d$__$28$ecmascript$29$__["default"], {
                            symbol: selectedSymbol
                        }, void 0, false, {
                            fileName: "[project]/pages/index.tsx",
                            lineNumber: 51,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/pages/index.tsx",
                    lineNumber: 20,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/pages/index.tsx",
                lineNumber: 19,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true);
}
_s(Home, "llISky7eso3d52GtgyjfWdaFUWE=");
_c = Home;
var _c;
__turbopack_context__.k.register(_c, "Home");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[next]/entry/page-loader.ts { PAGE => \"[project]/pages/index.tsx [client] (ecmascript)\" } [client] (ecmascript)", ((__turbopack_context__, module, exports) => {

const PAGE_PATH = "/";
(window.__NEXT_P = window.__NEXT_P || []).push([
    PAGE_PATH,
    ()=>{
        return __turbopack_context__.r("[project]/pages/index.tsx [client] (ecmascript)");
    }
]);
// @ts-expect-error module.hot exists
if (module.hot) {
    // @ts-expect-error module.hot exists
    module.hot.dispose(function() {
        window.__NEXT_P.push([
            PAGE_PATH
        ]);
    });
}
}),
"[hmr-entry]/hmr-entry.js { ENTRY => \"[project]/pages/index\" }", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.r("[next]/entry/page-loader.ts { PAGE => \"[project]/pages/index.tsx [client] (ecmascript)\" } [client] (ecmascript)");
}),
]);

//# sourceMappingURL=%5Broot-of-the-server%5D__a9a2567b._.js.map