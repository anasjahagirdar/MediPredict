import axios from 'axios';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const ACCESS_KEY = 'medipredict_access';
const REFRESH_KEY = 'medipredict_refresh';

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

let isRefreshing = false;
let pendingQueue = [];

function flushQueue(error, token = null) {
  pendingQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
      return;
    }

    resolve(token);
  });
  pendingQueue = [];
}

function clearAuthAndRedirect() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  window.location.href = '/login';
}

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const refreshToken = localStorage.getItem(REFRESH_KEY);

    if (!error.response) {
      return Promise.reject(error);
    }

    if (
      error.response.status !== 401 ||
      originalRequest?._retry ||
      originalRequest?.url?.includes('/api/auth/login/') ||
      originalRequest?.url?.includes('/api/auth/register/') ||
      originalRequest?.url?.includes('/api/auth/token/refresh/') ||
      !refreshToken
    ) {
      if (error.response.status === 401 && !refreshToken) {
        clearAuthAndRedirect();
      }
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      }).then((newToken) => {
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return axiosInstance(originalRequest);
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/auth/token/refresh/`,
        { refresh: refreshToken },
        { withCredentials: true }
      );

      const nextAccess = response.data.access;
      const nextRefresh = response.data.refresh;

      localStorage.setItem(ACCESS_KEY, nextAccess);
      if (nextRefresh) {
        localStorage.setItem(REFRESH_KEY, nextRefresh);
      }

      flushQueue(null, nextAccess);
      originalRequest.headers.Authorization = `Bearer ${nextAccess}`;
      return axiosInstance(originalRequest);
    } catch (refreshError) {
      flushQueue(refreshError, null);
      clearAuthAndRedirect();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);


export default axiosInstance;
