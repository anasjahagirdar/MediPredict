from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import HealthRecord


class MockModel:
    classes_ = ['Condition A', 'Condition B']

    def predict(self, features):
        return ['Condition A']

    def predict_proba(self, features):
        return [[0.82, 0.18]]


class PredictDiseaseViewTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='meditest',
            password='strong-pass-123',
        )
        self.predict_url = reverse('predict')
        self.payload = {
            'age': 45,
            'bmi': 24.5,
            'bp_systolic': 120,
            'bp_diastolic': 80,
            'sugar_level': 110,
            'cholesterol': 190,
            'heart_rate': 74,
            'gender': 1,
            'symptom_fever': 1,
            'symptom_cough': 0,
            'symptom_fatigue': 1,
            'symptom_headache': 0,
            'symptom_chest_pain': 0,
            'symptom_breathlessness': 0,
            'symptom_sweating': 0,
            'symptom_nausea': 0,
            'hba1c': 5.5,
            'ldl': 100.0,
            'hdl': 60.0
        }

    def test_predict_requires_authentication(self):
        response = self.client.post(self.predict_url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('core.views.ML_MODEL', new=MockModel())
    def test_predict_returns_200_and_saves_health_record(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.predict_url, self.payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(HealthRecord.objects.filter(user=self.user).count(), 1)

        record = HealthRecord.objects.get(user=self.user)
        self.assertEqual(record.predicted_disease, 'Healthy')
        self.assertEqual(record.age, self.payload['age'])
        self.assertEqual(record.bmi, self.payload['bmi'])
        self.assertEqual(record.bp_systolic, self.payload['bp_systolic'])
        self.assertEqual(response.data['record_id'], record.id)
        self.assertEqual(response.data['risk_level'], 'Low')
        self.assertEqual(response.data['confidence'], 82.0)
        self.assertIn('Healthy', response.data['class_probabilities'])
        self.assertEqual(response.data['class_probabilities']['Healthy'], 0.82)


class DashboardSummaryViewTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='summaryuser',
            password='strong-pass-123',
            first_name='Medi',
            last_name='Predict',
        )
        self.summary_url = reverse('dashboard-summary')

    def test_summary_requires_authentication(self):
        response = self.client.get(self.summary_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summary_returns_200_for_user_with_no_records(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.summary_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['patient_name'], 'Medi Predict')
        self.assertEqual(response.data['total_scans'], 0)
        self.assertEqual(response.data['high_risk_count'], 0)
        self.assertEqual(response.data['latest_bmi'], 0)
        self.assertEqual(response.data['latest_sugar'], 0)
        self.assertEqual(response.data['latest_bp'], '--')

    def test_summary_returns_latest_record_metrics(self):
        self.client.force_authenticate(user=self.user)

        HealthRecord.objects.create(
            user=self.user,
            bp_systolic=118,
            bp_diastolic=78,
            sugar_level=105,
            cholesterol=185,
            heart_rate=72,
            bmi=23.1,
            age=45,
            gender=1,
            symptom_fever=0,
            symptom_cough=0,
            symptom_fatigue=0,
            symptom_headache=0,
            symptom_chest_pain=0,
            symptom_breathlessness=0,
            symptom_sweating=0,
            symptom_nausea=0,
            predicted_disease='Condition A',
            confidence=60.0,
            risk_level='Medium',
        )
        HealthRecord.objects.create(
            user=self.user,
            bp_systolic=140,
            bp_diastolic=90,
            sugar_level=130,
            cholesterol=220,
            heart_rate=88,
            bmi=29.4,
            age=45,
            gender=1,
            symptom_fever=1,
            symptom_cough=1,
            symptom_fatigue=1,
            symptom_headache=0,
            symptom_chest_pain=0,
            symptom_breathlessness=0,
            symptom_sweating=0,
            symptom_nausea=0,
            predicted_disease='Condition B',
            confidence=84.0,
            risk_level='High',
        )

        response = self.client.get(self.summary_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_scans'], 2)
        self.assertEqual(response.data['high_risk_count'], 1)
        self.assertEqual(response.data['latest_bmi'], 29.4)
        self.assertEqual(response.data['latest_sugar'], 130.0)
        self.assertEqual(response.data['latest_bp'], '140/90')
