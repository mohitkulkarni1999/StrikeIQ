import axios from "axios"
import { isTokenExpired } from "@/utils/auth"

const api = axios.create({
  baseURL: "", // Use empty string to support relative URLs for Next.js rewrites
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // DISABLED: Auth checks are disabled per system memory
    // Allow requests to proceed without token validation
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
    // DISABLED: Auth checks are disabled per system memory
    // Do not redirect on 401 errors
    
    // Handle network errors
    if (!error.response) {
      console.error('🌐 Network error - please check your connection')
      return Promise.reject(error)
    }

    // Handle other HTTP errors
    console.error(`❌ API Error: ${error.response?.status} - ${error.response?.data?.detail || error.message}`)
    return Promise.reject(error)
  }
)

export default api
