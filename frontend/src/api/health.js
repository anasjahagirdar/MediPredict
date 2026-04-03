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

export async function downloadReport(recordId) {
  const response = await axiosInstance.get(`/api/reports/download/${recordId}/`, {
    responseType: 'blob',
  });

  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `medipredict-report-${recordId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
