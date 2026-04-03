import os
import joblib
from datetime import datetime
from io import BytesIO

from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.http import FileResponse

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from .models import Disease, HealthRecord
from .serializers import (
    HealthRecordSerializer, 
    MediPredictTokenObtainPairSerializer, 
    RegisterSerializer
)

# --- ML Model Initialization ---
_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ml', 'model.pkl')
ML_MODEL = joblib.load(_MODEL_PATH)

# 1. THE AUDITED FEATURE ORDER
FEATURE_ORDER = [
    'age', 'bmi', 'bp_systolic', 'bp_diastolic', 'sugar_level',
    'cholesterol', 'heart_rate', 'gender', 'symptom_fever',
    'symptom_cough', 'symptom_fatigue', 'symptom_headache',
    'symptom_chest_pain', 'symptom_breathlessness',
    'symptom_sweating', 'symptom_nausea',
]

SYMPTOM_LABELS = {
    'symptom_fever': 'Fever',
    'symptom_cough': 'Cough',
    'symptom_fatigue': 'Fatigue',
    'symptom_headache': 'Headache',
    'symptom_chest_pain': 'Chest Pain',
    'symptom_breathlessness': 'Breathlessness',
    'symptom_sweating': 'Sweating',
    'symptom_nausea': 'Nausea',
}

# --- Helper Functions ---

def derive_risk_level(probability):
    if probability >= 0.75:
        return 'High'
    if probability >= 0.50:
        return 'Medium'
    return 'Low'

def format_current_date(now):
    return f"{now.strftime('%A').upper()}, {now.strftime('%b').upper()} {now.day}, {now.year}"

def format_short_date(value):
    return f"{value.strftime('%b')} {value.day}"

def parse_prediction_payload(data):
    parsed = {}
    for field in FEATURE_ORDER:
        raw_value = data.get(field)
        if raw_value is None or raw_value == '':
            raise ValueError(f'{field} is required.')

        if field in ('sugar_level', 'cholesterol', 'bmi'):
            parsed[field] = float(raw_value)
        else:
            parsed[field] = int(raw_value)
    return parsed

def get_medication_names(diagnosis):
    disease = Disease.objects.filter(disease_name__iexact=diagnosis).prefetch_related('medications').first()
    if not disease:
        return []
    return [med.medicine_name for med in disease.medications.all()]

# --- Authentication Views ---

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'message': 'Account created successfully', 'username': user.username},
            status=status.HTTP_201_CREATED
        )

class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = MediPredictTokenObtainPairSerializer

class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'message': 'Refresh token required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'message': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

# --- Core ML & Dashboard Views ---

class PredictDiseaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            payload = parse_prediction_payload(request.data)
            feature_vector = [payload[field] for field in FEATURE_ORDER]
            
            prediction = str(ML_MODEL.predict([feature_vector])[0])
            probabilities = ML_MODEL.predict_proba([feature_vector])[0]
            
            class_probabilities = {
                str(label): round(float(prob), 4)
                for label, prob in zip(ML_MODEL.classes_, probabilities)
            }
            confidence = float(max(probabilities))
            confidence_percent = round(confidence * 100, 2)
            risk_level = derive_risk_level(confidence)

            record = HealthRecord.objects.create(
                user=request.user,
                predicted_disease=prediction,
                confidence=confidence_percent,
                risk_level=risk_level,
                **payload 
            )
            print(f"Record {record.id} saved successfully")

            return Response({
                'diagnosis': prediction,
                'confidence': confidence_percent,
                'risk_level': risk_level,
                'class_probabilities': class_probabilities,
                'medications': get_medication_names(prediction),
                'record_id': record.id,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': f"Prediction Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset = HealthRecord.objects.filter(user=request.user).order_by('-created_at')
            latest = queryset.first()
            full_name = request.user.get_full_name().strip() or request.user.username
            now = timezone.now()

            return Response({
                'patient_name': full_name,
                'total_scans': queryset.count(),
                'high_risk_count': queryset.filter(risk_level='High').count(),
                'latest_bmi': latest.bmi if latest else 0,
                'latest_sugar': latest.sugar_level if latest else 0,
                'latest_bp': f'{latest.bp_systolic}/{latest.bp_diastolic}' if latest else '--',
                'current_date': format_current_date(now),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f"Summary Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardRiskTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            latest_five = list(HealthRecord.objects.filter(user=request.user).order_by('-created_at')[:5])
            latest_five.reverse()

            scans = [{
                'scan_number': i + 1,
                'date': format_short_date(r.created_at),
                'raw_date': r.created_at,
                'risk_level': r.risk_level,
                'diagnosis': r.predicted_disease,
                'confidence': r.confidence,
                'bp_systolic': r.bp_systolic,
                'bmi': r.bmi
            } for i, r in enumerate(latest_five)]

            return Response({'scans': scans}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f"Trend Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardSymptomFrequencyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            aggregate = HealthRecord.objects.filter(user=request.user).aggregate(
                **{key: Sum(key) for key in SYMPTOM_LABELS}
            )
            symptoms = [{
                'name': label,
                'count': int(aggregate.get(field) or 0),
            } for field, label in SYMPTOM_LABELS.items()]

            return Response({'symptoms': symptoms}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f"Symptom Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardScanHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset = HealthRecord.objects.filter(user=request.user).order_by('-created_at')
            disease_names = queryset.values_list('predicted_disease', flat=True).distinct()
            disease_map = {
                d.disease_name: d for d in Disease.objects.filter(
                    disease_name__in=disease_names
                ).prefetch_related('medications')
            }

            records = []
            for record in queryset:
                record._disease_prefetch = disease_map.get(record.predicted_disease)
                records.append(HealthRecordSerializer(record).data)

            return Response({'scans': records}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': f"History Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DownloadReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            record = HealthRecord.objects.get(id=record_id, user=request.user)
        except HealthRecord.DoesNotExist:
            return Response({'message': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': f"Report Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            patient_name = request.user.get_full_name().strip() or request.user.username
            report_date = record.created_at.strftime('%B %d, %Y %I:%M %p')

            pdf.setTitle(f"MediPredict Report #{record.id}")

            pdf.setFillColor(colors.HexColor('#1E1E2E'))
            pdf.rect(0, height - 72, width, 72, stroke=0, fill=1)
            pdf.setFillColor(colors.white)
            pdf.setFont('Helvetica-Bold', 22)
            pdf.drawString(50, height - 42, 'MediPredict')
            pdf.setFont('Helvetica', 10)
            pdf.drawRightString(width - 50, height - 42, f'Report ID: {record.id}')

            y = height - 110
            pdf.setFillColor(colors.HexColor('#1A1A2E'))
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(50, y, 'Patient Overview')

            y -= 28
            pdf.setFont('Helvetica', 11)
            pdf.drawString(50, y, f'Patient Name: {patient_name}')
            y -= 18
            pdf.drawString(50, y, f'Report Date: {report_date}')
            y -= 18
            pdf.drawString(50, y, f'Age: {record.age}')
            y -= 18
            pdf.drawString(50, y, f'Gender Code: {record.gender}')

            y -= 36
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(50, y, 'Clinical Vitals')

            vitals = [
                ('Blood Pressure', f'{record.bp_systolic}/{record.bp_diastolic} mmHg'),
                ('BMI', f'{record.bmi:.1f}'),
                ('Blood Sugar', f'{record.sugar_level:.1f}'),
                ('Cholesterol', f'{record.cholesterol:.1f}'),
                ('Heart Rate', f'{record.heart_rate} bpm'),
            ]

            y -= 28
            pdf.setFont('Helvetica', 11)
            for label, value in vitals:
                pdf.drawString(50, y, f'{label}: {value}')
                y -= 18

            y -= 18
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(50, y, 'Diagnostic Result')

            y -= 28
            pdf.setFont('Helvetica', 11)
            pdf.drawString(50, y, f'Predicted Disease: {record.predicted_disease}')
            y -= 18
            pdf.drawString(50, y, f'Confidence: {record.confidence}%')
            y -= 18
            pdf.drawString(50, y, f'Risk Level: {record.risk_level}')

            pdf.setStrokeColor(colors.HexColor('#E8E2D9'))
            pdf.line(50, 90, width - 50, 90)
            pdf.setFillColor(colors.HexColor('#6B7280'))
            pdf.setFont('Helvetica-Oblique', 9)
            text = pdf.beginText(50, 72)
            text.setLeading(12)
            for line in (
                'This platform provides AI-generated health insights for informational purposes only',
                'and should not be considered a medical diagnosis. Please consult a qualified',
                'healthcare professional for medical advice.',
            ):
                text.textLine(line)
            pdf.drawText(text)

            pdf.showPage()
            pdf.save()
            buffer.seek(0)

            return FileResponse(
                buffer,
                as_attachment=True,
                filename=f'medipredict-report-{record.id}.pdf',
                content_type='application/pdf',
            )
        except Exception as e:
            return Response({'message': f"PDF Generation Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
