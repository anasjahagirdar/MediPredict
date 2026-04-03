import os
import json
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

# ── ML Artifact Initialization ───────────────────────────────────────────────
# FIX 3: Wrapped in try/except so Django gives a clear startup error
# instead of crashing silently if artifacts are missing.

_ML_DIR       = os.path.join(os.path.dirname(__file__), 'ml')
_MODEL_PATH   = os.path.join(_ML_DIR, 'model.pkl')
_ENCODER_PATH = os.path.join(_ML_DIR, 'label_encoder.pkl')
_FEATURES_PATH = os.path.join(_ML_DIR, 'feature_list.json')

try:
    ML_MODEL      = joblib.load(_MODEL_PATH)
    LABEL_ENCODER = joblib.load(_ENCODER_PATH)
    with open(_FEATURES_PATH, 'r') as f:
        FEATURE_ORDER = json.load(f)

    # FIX 1: Pre-compute decoded class names once at startup.
    # This avoids calling ML_MODEL.classes_ at request time,
    # which crashes on StackingClassifier (no .classes_ attribute).
    # LABEL_ENCODER.classes_ is always safe — it's a plain numpy array.
    DECODED_CLASSES = list(LABEL_ENCODER.classes_)

    print(f"[MediPredict] ✔ ML artifacts loaded successfully.")
    print(f"[MediPredict] ✔ Classes : {DECODED_CLASSES}")
    print(f"[MediPredict] ✔ Features: {FEATURE_ORDER}")

except FileNotFoundError as e:
    raise RuntimeError(
        f"\n[MediPredict] ✘ ML artifact not found: {e}\n"
        f"  → Run 'python retrain.py' from the backend folder first.\n"
    )
except Exception as e:
    raise RuntimeError(
        f"\n[MediPredict] ✘ Failed to load ML artifacts: {e}\n"
    )

# ── Symptom Display Labels ────────────────────────────────────────────────────

SYMPTOM_LABELS = {
    'symptom_fever':           'Fever',
    'symptom_cough':           'Cough',
    'symptom_fatigue':         'Fatigue',
    'symptom_headache':        'Headache',
    'symptom_chest_pain':      'Chest Pain',
    'symptom_breathlessness':  'Breathlessness',
    'symptom_sweating':        'Sweating',
    'symptom_nausea':          'Nausea',
}

# ── FIX 2: Clinical Risk Level Mapping ───────────────────────────────────────
# OLD logic mapped confidence % → risk level, which meant a high-confidence
# "Healthy" prediction would wrongly show as "High Risk".
#
# NEW logic: risk level is derived from the DIAGNOSIS first,
# then refined by confidence. This matches real clinical triage logic.
#
# Rule:
#   Healthy           → always Low  (regardless of confidence)
#   Hypertension      → Medium baseline, High if confidence ≥ 0.75
#   Diabetes          → Medium baseline, High if confidence ≥ 0.75
#   Heart Disease     → always High (cardiac events are always urgent)
#   Obesity           → Medium baseline, High if confidence ≥ 0.80

DISEASE_BASE_RISK = {
    'Healthy':       'Low',
    'Hypertension':  'Medium',
    'Diabetes':      'Medium',
    'Heart Disease': 'High',
    'Obesity':       'Medium',
}

def derive_risk_level(diagnosis: str, confidence: float) -> str:
    """
    Derive clinical risk level from diagnosis name and confidence score.
    Falls back to confidence-only logic for any unknown future labels.
    """
    base_risk = DISEASE_BASE_RISK.get(diagnosis)

    if base_risk is None:
        # Fallback for any label not in the map
        if confidence >= 0.75:
            return 'High'
        if confidence >= 0.50:
            return 'Medium'
        return 'Low'

    if base_risk == 'Low':
        return 'Low'

    if base_risk == 'High':
        return 'High'

    # Medium baseline — escalate to High if model is very confident
    escalate_threshold = 0.80 if diagnosis == 'Obesity' else 0.75
    if confidence >= escalate_threshold:
        return 'High'

    return 'Medium'


# ── Helper Functions ──────────────────────────────────────────────────────────

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
    disease = Disease.objects.filter(
        disease_name__iexact=diagnosis
    ).prefetch_related('medications').first()
    if not disease:
        return []
    return [med.medicine_name for med in disease.medications.all()]


# ── Authentication Views ──────────────────────────────────────────────────────

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
            return Response(
                {'message': 'Refresh token required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {'message': 'Logged out successfully'},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {'message': 'Invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


# ── Core ML & Dashboard Views ─────────────────────────────────────────────────

class PredictDiseaseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 1. Parse and validate incoming vitals
            payload = parse_prediction_payload(request.data)
            feature_vector = [payload[field] for field in FEATURE_ORDER]

            # 2. Run prediction
            raw_prediction   = ML_MODEL.predict([feature_vector])[0]
            prediction_name  = LABEL_ENCODER.inverse_transform([raw_prediction])[0]

            # 3. Get probabilities using pre-computed DECODED_CLASSES
            # FIX 1: No longer calls ML_MODEL.classes_ (crashes on StackingClassifier)
            probabilities = ML_MODEL.predict_proba([feature_vector])[0]
            class_probabilities = {
                str(label): round(float(prob), 4)
                for label, prob in zip(DECODED_CLASSES, probabilities)
            }

            # 4. Derive confidence and risk level
            confidence         = float(max(probabilities))
            confidence_percent = round(confidence * 100, 2)

            # FIX 2: Risk level now uses diagnosis-aware clinical logic
            risk_level = derive_risk_level(prediction_name, confidence)

            # 5. Save to database
            record = HealthRecord.objects.create(
                user=request.user,
                predicted_disease=prediction_name,
                confidence=confidence_percent,
                risk_level=risk_level,
                **payload
            )
            print(f"[MediPredict] Record {record.id} saved — "
                  f"{prediction_name} | {risk_level} | {confidence_percent}%")

            return Response({
                'diagnosis':           prediction_name,
                'confidence':          confidence_percent,
                'risk_level':          risk_level,
                'class_probabilities': class_probabilities,
                'medications':         get_medication_names(prediction_name),
                'record_id':           record.id,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'message': f"Prediction Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset   = HealthRecord.objects.filter(user=request.user).order_by('-created_at')
            latest     = queryset.first()
            full_name  = request.user.get_full_name().strip() or request.user.username
            now        = timezone.now()

            return Response({
                'patient_name':    full_name,
                'total_scans':     queryset.count(),
                'high_risk_count': queryset.filter(risk_level='High').count(),
                'latest_bmi':      latest.bmi if latest else 0,
                'latest_sugar':    latest.sugar_level if latest else 0,
                'latest_bp':       f'{latest.bp_systolic}/{latest.bp_diastolic}' if latest else '--',
                'current_date':    format_current_date(now),
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'message': f"Summary Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardRiskTrendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            latest_five = list(
                HealthRecord.objects.filter(user=request.user).order_by('-created_at')[:5]
            )
            latest_five.reverse()

            scans = [{
                'scan_number': i + 1,
                'date':        format_short_date(r.created_at),
                'raw_date':    r.created_at,
                'risk_level':  r.risk_level,
                'diagnosis':   r.predicted_disease,
                'confidence':  r.confidence,
                'bp_systolic': r.bp_systolic,
                'bmi':         r.bmi,
            } for i, r in enumerate(latest_five)]

            return Response({'scans': scans}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'message': f"Trend Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardSymptomFrequencyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            aggregate = HealthRecord.objects.filter(user=request.user).aggregate(
                **{key: Sum(key) for key in SYMPTOM_LABELS}
            )
            symptoms = [{
                'name':  label,
                'count': int(aggregate.get(field) or 0),
            } for field, label in SYMPTOM_LABELS.items()]

            return Response({'symptoms': symptoms}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'message': f"Symptom Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardScanHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset     = HealthRecord.objects.filter(user=request.user).order_by('-created_at')
            disease_names = queryset.values_list('predicted_disease', flat=True).distinct()
            disease_map  = {
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
            return Response(
                {'message': f"History Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DownloadReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, record_id):
        try:
            record = HealthRecord.objects.get(id=record_id, user=request.user)
        except HealthRecord.DoesNotExist:
            return Response(
                {'message': 'Report not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'message': f"Report Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            buffer = BytesIO()
            pdf    = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4

            patient_name = request.user.get_full_name().strip() or request.user.username
            report_date  = record.created_at.strftime('%B %d, %Y %I:%M %p')

            pdf.setTitle(f"MediPredict Report #{record.id}")

            # Header
            pdf.setFillColor(colors.HexColor('#1E1E2E'))
            pdf.rect(0, height - 72, width, 72, stroke=0, fill=1)
            pdf.setFillColor(colors.white)
            pdf.setFont('Helvetica-Bold', 22)
            pdf.drawString(50, height - 42, 'MediPredict')
            pdf.setFont('Helvetica', 10)
            pdf.drawRightString(width - 50, height - 42, f'Report ID: {record.id}')

            # Patient Overview
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

            # Clinical Vitals
            y -= 36
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(50, y, 'Clinical Vitals')
            vitals = [
                ('Blood Pressure', f'{record.bp_systolic}/{record.bp_diastolic} mmHg'),
                ('BMI',            f'{record.bmi:.1f}'),
                ('Blood Sugar',    f'{record.sugar_level:.1f}'),
                ('Cholesterol',    f'{record.cholesterol:.1f}'),
                ('Heart Rate',     f'{record.heart_rate} bpm'),
            ]
            y -= 28
            pdf.setFont('Helvetica', 11)
            for label, value in vitals:
                pdf.drawString(50, y, f'{label}: {value}')
                y -= 18

            # Diagnostic Result
            y -= 18
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(50, y, 'Diagnostic Result')
            y -= 28
            pdf.setFont('Helvetica', 11)
            pdf.drawString(50, y, f'Predicted Disease : {record.predicted_disease}')
            y -= 18
            pdf.drawString(50, y, f'Confidence        : {record.confidence}%')
            y -= 18
            pdf.drawString(50, y, f'Risk Level        : {record.risk_level}')

            # Footer
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
            return Response(
                {'message': f"PDF Generation Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )