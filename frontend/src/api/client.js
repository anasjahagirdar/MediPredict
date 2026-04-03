import axios from 'axios';


const SESSION_KEY = 'medipredict_session';


const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
});


apiClient.interceptors.request.use((config) => {
  try {
    const rawSession = localStorage.getItem(SESSION_KEY);
    const session = rawSession ? JSON.parse(rawSession) : null;

    if (session?.access) {
      config.headers.Authorization = `Bearer ${session.access}`;
    }
  } catch {
    // Ignore invalid session payloads and continue without auth headers.
  }

  return config;
});


export default apiClient;
