/**

* 🔒 WS CONNECTION LIFECYCLE - LOCKED MODULE
*
* Handles:
* * OAuth success → WS init
* * Single WS handshake
* * Live options feed lifecycle
*
* Store is the single source of truth.
  */

import { useEffect, useRef, useCallback } from "react";
import { useWSStore } from "./wsStore";
import { initWebSocketOnce, isWSInitialized, markWSInitialized } from "./wsInitController";
import { getValidExpiries } from "@/lib/axios";

interface LiveOptionsWSOptions {
symbol: string;
expiry: string;
onMessage?: (data: any) => void;
onError?: (error: string) => void;
onConnect?: () => void;
onDisconnect?: () => void;
}

export function useLiveOptionsWS(options: LiveOptionsWSOptions) {

const {
ws,
connected,
isInitializing,
setWS,
setInitializing,
setError,
} = useWSStore();

const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
const mountedRef = useRef(true);
const initializedRef = useRef(false);
const optionsRef = useRef(options);
optionsRef.current = options;

const getValidExpiryFromBackend = useCallback(async (symbol: string) => {
const expiries = await getValidExpiries(symbol);
return expiries.length > 0 ? expiries[0] : "";
}, []);

const connect = useCallback(async () => {
if (!mountedRef.current) return;

const state = (useWSStore as any).getState();

if (state.connected || state.isInitializing) {
  console.log("🔒 WS: Already connected or initializing");
  return;
}

// ================= INIT =================

if (!isWSInitialized()) {

  console.log("🔒 WS: Running init");

  setInitializing(true);

  const initResult = await initWebSocketOnce();

  if (!initResult || (initResult.status !== "success" && initResult.status !== "connected")) {

    setError(initResult?.message || "WS initialization failed");
    setInitializing(false);
    return;
  }

  markWSInitialized();

  setInitializing(false);

}

// ================= EXPIRY =================

const { symbol } = optionsRef.current;

let expiry = optionsRef.current.expiry;

try {

  expiry = await getValidExpiryFromBackend(symbol);

  console.log("🔒 Using expiry:", expiry);

} catch (err) {

  console.error("Failed to get expiry", err);
  setError("Failed to get expiry");
  return;
}

// ================= CONNECT =================

const socket = (useWSStore as any).getState().connect(symbol, expiry);

if (!socket) {
  setError("WS connection failed");
  return;
}

  setWS(socket);

  console.log("🔒 WS: Connection initiated");

}, [getValidExpiryFromBackend, setInitializing, setError, setWS]);

// ================= MOUNT =================

useEffect(() => {
if (initializedRef.current) {
  console.log("🔒 WS: Already initialized (StrictMode protection)");
  return;
}

initializedRef.current = true;
mountedRef.current = true;

connect();

return () => {

  mountedRef.current = false;

  if (reconnectTimeoutRef.current) {
    clearTimeout(reconnectTimeoutRef.current);
  }

};

}, [connect]);

// ================= MANUAL DISCONNECT =================

const disconnect = useCallback(() => {
const currentState = (useWSStore as any).getState();

if (currentState.ws) {
  currentState.ws.close(1000, "Manual disconnect");
}

}, []);

return {
ws,
connected,
isInitializing,
reconnect: connect,
disconnect
};
}
