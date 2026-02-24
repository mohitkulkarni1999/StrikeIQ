import axios from "axios";

const api = axios.create({
  baseURL: "", // Support Next.js relative paths to proxy
  withCredentials: true
});

export default api;
