import axiosInstance from './axiosInstance';


export async function registerUser(payload) {
  const response = await axiosInstance.post('/api/auth/register/', payload);
  return response.data;
}

export async function loginUser(payload) {
  const response = await axiosInstance.post('/api/auth/login/', payload);
  return response.data;
}

export async function logoutUser(payload) {
  const response = await axiosInstance.post('/api/auth/logout/', payload);
  return response.data;
}
