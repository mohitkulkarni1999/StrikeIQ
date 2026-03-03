import axios from "axios"

// Create axios instance with default config
const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 5000
})

// 401 AUTH FALLBACK ONLY
api.interceptors.response.use(
  (response) => response,
  async (error) => {

    if (error.code === "ERR_NETWORK") {
      console.warn("Backend offline")
      return Promise.resolve({ data: { status: "offline" } })
    }

    // 401 FALLBACK: Only log error - NO automatic redirects
    if (error.response?.status === 401) {
      console.warn("🔐 401 received - authentication expired")
      // Removed automatic redirect - auth is now manual only
      return Promise.reject(error)
    }

    if (error.response?.status >= 500) {
      console.warn("Server error:", error.response.status)
      return Promise.resolve({ data: { status: "error" } })
    }

    return Promise.reject(error)
  }
)

export async function getValidExpiries(symbol: string): Promise<string[]> {
  try {
    const response = await api.get(`/api/v1/market/expiries?symbol=${symbol}`)
    return response.data?.data || []
  } catch (error) {
    console.error("Failed to fetch expiries:", error)
    return []
  }
}

export default api
