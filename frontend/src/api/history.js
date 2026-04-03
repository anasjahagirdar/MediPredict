import apiClient from './client';


export async function getHistory() {
  const response = await apiClient.get('/history/');
  return response.data;
}
