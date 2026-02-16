import axios from "axios"

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any request modifications here if needed
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for handling 401 errors
api.interceptors.response.use(
  (response) => {
    // Any status code that lies within the range of 2xx causes this function to trigger
    return response
  },
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response?.status === 401) {
      console.warn("🔐 Authentication required - redirecting to auth screen")
      
      // Clear any stored auth data
      localStorage.removeItem("upstox_auth")
      sessionStorage.removeItem("upstox_auth")
      
      // Redirect to auth screen
      window.location.href = "/auth"
    }
    
    // Handle network errors
    if (!error.response) {
      console.error("🌐 Network error - please check your connection")
      return Promise.reject(error)
    }
    
    // Handle other HTTP errors
    console.error(`❌ API Error: ${error.response?.status} - ${error.response?.data?.detail || error.message}`)
    return Promise.reject(error)
  }
)

export default api
