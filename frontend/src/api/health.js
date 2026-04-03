import axiosInstance from './axiosInstance';


export async function predictHealth(payload) {
  const response = await axiosInstance.post('/api/predict/', payload);
  return response.data;
}

export async function getDashboardSummary() {
  const response = await axiosInstance.get('/api/dashboard/summary/');
  return response.data;
}

export async function getRiskTrend() {
  const response = await axiosInstance.get('/api/dashboard/risk-trend/');
  return response.data;
}

export async function getSymptomFrequency() {
  const response = await axiosInstance.get('/api/dashboard/symptom-frequency/');
  return response.data;
}

export async function getScanHistory() {
  const response = await axiosInstance.get('/api/dashboard/scan-history/');
  return response.data;
}
