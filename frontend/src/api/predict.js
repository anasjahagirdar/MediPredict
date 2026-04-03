import apiClient from './client';


export async function getPrediction(formData) {
  const response = await apiClient.post('/predict/', {
    ...formData,
    age: Number(formData.age),
    bmi: Number(formData.bmi),
    bp_systolic: Number(formData.bp_systolic),
    bp_diastolic: Number(formData.bp_diastolic),
    sugar_level: Number(formData.sugar_level),
    cholesterol: Number(formData.cholesterol),
    heart_rate: Number(formData.heart_rate),
  });

  return response.data;
}
