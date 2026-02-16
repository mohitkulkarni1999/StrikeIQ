// WebSocket Debug Script
// Run this in browser console to debug WebSocket connection issues

console.log("🔍 WEBSOCKET DEBUG STARTED");

// Check environment variables
console.log("🌍 Environment Variables:");
console.log("  NEXT_PUBLIC_WS_URL:", process.env.NEXT_PUBLIC_WS_URL);
console.log("  NEXT_PUBLIC_API_URL:", process.env.NEXT_PUBLIC_API_URL);
console.log("  Window location:", window.location.href);

// Test WebSocket connection directly
async function testWebSocketConnection() {
  const wsBaseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
  const wsUrl = `${wsBaseUrl}/ws/live-options/NIFTY`;
  
  console.log("🔌 Testing WebSocket connection to:", wsUrl);
  
  try {
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log("✅ WebSocket connection opened successfully");
      
      // Send a test message
      ws.send(JSON.stringify({test: "hello"}));
    };
    
    ws.onmessage = (event) => {
      console.log("📡 WebSocket message received:", event.data);
      
      try {
        const data = JSON.parse(event.data);
        console.log("📊 Parsed message:", data);
        
        if (data.source) {
          console.log("🔍 Data source:", data.source);
        }
        
        if (data.status === 'success') {
          console.log("✅ Message status: success");
          if (data.mode) {
            console.log("🎯 Message mode:", data.mode);
          }
        }
      } catch (e) {
        console.error("❌ JSON parse error:", e);
      }
    };
    
    ws.onerror = (error) => {
      console.error("❌ WebSocket error:", error);
    };
    
    ws.onclose = (event) => {
      console.log("🔌 WebSocket closed:", {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean
      });
    };
    
    // Timeout after 10 seconds
    setTimeout(() => {
      if (ws.readyState === WebSocket.CONNECTING) {
        console.error("❌ WebSocket connection timeout");
        ws.close();
      }
    }, 10000);
    
  } catch (error) {
    console.error("❌ WebSocket creation error:", error);
  }
}

// Test HTTP health check
async function testHttpHealth() {
  try {
    const response = await fetch('http://localhost:8000/health');
    const data = await response.json();
    console.log("✅ HTTP health check passed:", data);
  } catch (error) {
    console.error("❌ HTTP health check failed:", error);
  }
}

// Test WebSocket route availability
async function testWebSocketRoute() {
  try {
    const response = await fetch('http://localhost:8000/ws/live-options/NIFTY', {
      method: 'GET',
      headers: {
        'Connection': 'Upgrade',
        'Upgrade': 'websocket',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13'
      }
    });
    
    console.log("🔍 WebSocket route response status:", response.status);
    console.log("🔍 WebSocket route headers:", Object.fromEntries(response.headers.entries()));
    
  } catch (error) {
    console.error("❌ WebSocket route test failed:", error);
  }
}

// Run all tests
async function runAllTests() {
  console.log("\n🧪 RUNNING WEBSOCKET TESTS");
  console.log("================================");
  
  await testHttpHealth();
  await testWebSocketRoute();
  await testWebSocketConnection();
  
  console.log("\n📊 TEST SUMMARY");
  console.log("================================");
  console.log("Check the logs above for any errors");
  console.log("If you see '✅ WebSocket connection opened successfully', the connection works");
  console.log("If you see errors, check:");
  console.log("1. Backend server is running on port 8000");
  console.log("2. No firewall blocking WebSocket connections");
  console.log("3. WebSocket URL is correct");
}

runAllTests();
