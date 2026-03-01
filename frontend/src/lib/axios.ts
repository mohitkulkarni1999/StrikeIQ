import axios from "axios"

// Create axios instance with default config
const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 5000
})

api.interceptors.response.use(
  (response) => response,
  (error) => {

    if (error.code === "ERR_NETWORK") {
      console.warn("Backend offline")
      return Promise.resolve({ data: { status: "offline" } })
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
