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

# ── ML Artifact Initialization ────────────────────────────────────────────────

_ML_DIR             = os.path.join(os.path.dirname(__file__), 'ml')
_RISK_MODEL_PATH    = os.path.join(_ML_DIR, 'risk_model.pkl')
_RISK_ENCODER_PATH  = os.path.join(_ML_DIR, 'risk_label_encoder.pkl')
_MODEL_PATH         = os.path.join(_ML_DIR, 'model.pkl')
_ENCODER_PATH       = os.path.join(_ML_DIR, 'label_encoder.pkl')
_FEATURES_PATH      = os.path.join(_ML_DIR, 'feature_list.json')

try:
    RISK_MODEL         = joblib.load(_RISK_MODEL_PATH)
    RISK_LABEL_ENCODER = joblib.load(_RISK_ENCODER_PATH)
    ML_MODEL           = joblib.load(_MODEL_PATH)
    LABEL_ENCODER      = joblib.load(_ENCODER_PATH)

    with open(_FEATURES_PATH, 'r') as f:
        FEATURE_ORDER = json.load(f)

    DECODED_RISK_CLASSES    = list(RISK_LABEL_ENCODER.classes_)
    DECODED_DISEASE_CLASSES = list(LABEL_ENCODER.classes_)

    print(f"[MediPredict] ✔ ML artifacts loaded successfully.")
    print(f"[MediPredict] ✔ Risk classes    : {DECODED_RISK_CLASSES}")
    print(f"[MediPredict] ✔ Disease classes : {DECODED_DISEASE_CLASSES}")
    print(f"[MediPredict] ✔ Features ({len(FEATURE_ORDER)}): {FEATURE_ORDER}")

except FileNotFoundError as e:
    raise RuntimeError(
        f"\n[MediPredict] ✘ ML artifact not found: {e}\n"
        f"  → Run 'python retrain_v2.py' from the backend folder first.\n"
    )
except Exception as e:
    raise RuntimeError(f"\n[MediPredict] ✘ Failed to load ML artifacts: {e}\n")

# ── Symptom Display Labels ────────────────────────────────────────────────────

SYMPTOM_LABELS = {
    'symptom_fever':          'Fever',
    'symptom_cough':          'Cough',
    'symptom_fatigue':        'Fatigue',
    'symptom_headache':       'Headache',
    'symptom_chest_pain':     'Chest Pain',
    'symptom_breathlessness': 'Breathlessness',
    'symptom_sweating':       'Sweating',
    'symptom_nausea':         'Nausea',
}

# ── Medication Fallback Map ───────────────────────────────────────────────────

MEDICATION_FALLBACK = {
    'Heart Disease': ['Aspirin', 'Atorvastatin', 'Metoprolol', 'Lisinopril'],
    'Hypertension':  ['Amlodipine', 'Losartan', 'Hydrochlorothiazide', 'Enalapril'],
    'Diabetes':      ['Metformin', 'Glipizide', 'Insulin Glargine', 'Sitagliptin'],
    'Obesity':       ['Orlistat', 'Phentermine', 'Naltrexone/Bupropion'],
    'Healthy':       [],
}

# ── Confidence Threshold ──────────────────────────────────────────────────────

LOW_CONFIDENCE_THRESHOLD = 0.55

# ── Input Validation Ranges ───────────────────────────────────────────────────
# Updated to include the 3 new lab features: hba1c, ldl, hdl
# Lab fields are optional on the frontend — if not provided, population-average
# defaults are used so the prediction always runs.

VITAL_RANGES = {
    'bp_systolic':  (60,   250),
    'bp_diastolic': (40,   150),
    'sugar_level':  (50,   700),
    'cholesterol':  (50,   500),
    'heart_rate':   (30,   220),
    'bmi':          (10,   80),
    'age':          (0,    120),
    'gender':       (0,    1),
    'hba1c':        (3.0,  14.0),
    'ldl':          (30.0, 250.0),
    'hdl':          (15.0, 100.0),
}

# Population-average defaults for lab fields when user skips Step 3
LAB_DEFAULTS = {
    'hba1c': 5.5,   # Normal/pre-diabetic boundary
    'ldl':   110.0, # Borderline-optimal
    'hdl':   52.0,  # Normal protective range
}

LAB_FIELDS = {'hba1c', 'ldl', 'hdl'}

# ── Two-Stage Prediction ──────────────────────────────────────────────────────

def run_two_stage_prediction(feature_vector: list) -> dict:
    """
    Stage 1: Predict risk level (Low/Medium/High) — always runs.
    Stage 2: Predict disease — only runs for Medium/High.
    Low Risk → returns Healthy immediately, skips Stage 2.
    """
    # Stage 1
    risk_probs_raw  = RISK_MODEL.predict_proba([feature_vector])[0]
    risk_pred_int   = RISK_MODEL.predict([feature_vector])[0]
    risk_level      = RISK_LABEL_ENCODER.inverse_transform([risk_pred_int])[0]
    risk_confidence = float(max(risk_probs_raw))

    risk_probabilities = {
        str(label): round(float(prob), 4)
        for label, prob in zip(DECODED_RISK_CLASSES, risk_probs_raw)
    }

    if risk_level == 'Low':
        return {
            'diagnosis':            'Healthy',
            'confidence':           round(risk_confidence * 100, 2),
            'risk_level':           'Low',
            'low_confidence':       risk_confidence < LOW_CONFIDENCE_THRESHOLD,
            'stage1_risk_probs':    risk_probabilities,
            'sorted_probabilities': [{'label': 'Healthy', 'probability': round(risk_confidence * 100, 2)}],
            'class_probabilities':  {'Healthy': round(risk_confidence, 4)},
            'skipped_stage2':       True,
        }

    # Stage 2
    disease_probs_raw  = ML_MODEL.predict_proba([feature_vector])[0]
    disease_pred_int   = ML_MODEL.predict([feature_vector])[0]
    prediction_name    = LABEL_ENCODER.inverse_transform([disease_pred_int])[0]
    disease_confidence = float(max(disease_probs_raw))

    class_probabilities = {
        str(label): round(float(prob), 4)
        for label, prob in zip(DECODED_DISEASE_CLASSES, disease_probs_raw)
    }

    sorted_probs = sorted(
        [{'label': label, 'probability': round(prob * 100, 2)}
         for label, prob in class_probabilities.items()],
        key=lambda x: x['probability'],
        reverse=True
    )

    return {
        'diagnosis':            prediction_name,
        'confidence':           round(disease_confidence * 100, 2),
        'risk_level':           risk_level,
        'low_confidence':       disease_confidence < LOW_CONFIDENCE_THRESHOLD,
        'stage1_risk_probs':    risk_probabilities,
        'sorted_probabilities': sorted_probs,
        'class_probabilities':  class_probabilities,
        'skipped_stage2':       False,
    }


# ── Helper Functions ──────────────────────────────────────────────────────────

def format_current_date(now):
    return f"{now.strftime('%A').upper()}, {now.strftime('%b').upper()} {now.day}, {now.year}"

def format_short_date(value):
    return f"{value.strftime('%b')} {value.day}"

def parse_prediction_payload(data):
    """
    Parse, type-cast, and validate all 19 features.
    Lab fields (hba1c, ldl, hdl) are optional — fall back to LAB_DEFAULTS if absent.
    """
    parsed = {}
    for field in FEATURE_ORDER:
        raw_value = data.get(field)

        # Lab fields are optional — use defaults if not provided
        if raw_value is None or raw_value == '':
            if field in LAB_FIELDS:
                parsed[field] = LAB_DEFAULTS[field]
                continue
            raise ValueError(f'{field} is required.')

        # Type casting
        if field in ('sugar_level', 'cholesterol', 'bmi', 'hba1c', 'ldl', 'hdl'):
            parsed[field] = float(raw_value)
        else:
            parsed[field] = int(raw_value)

        # Range validation
        if field in VITAL_RANGES:
            lo, hi = VITAL_RANGES[field]
            if not (lo <= parsed[field] <= hi):
                raise ValueError(
                    f'{field} value {parsed[field]} is outside the valid range ({lo}–{hi}).'
                )

    return parsed

def get_medication_names(diagnosis):
    disease = Disease.objects.filter(
        disease_name__iexact=diagnosis
    ).prefetch_related('medications').first()

    if disease:
        meds = [med.medicine_name for med in disease.medications.all()]
        if meds:
            return meds

    return MEDICATION_FALLBACK.get(diagnosis, [])


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
            payload        = parse_prediction_payload(request.data)
            feature_vector = [payload[field] for field in FEATURE_ORDER]
            prediction     = run_two_stage_prediction(feature_vector)

            record = HealthRecord.objects.create(
                user=request.user,
                predicted_disease=prediction['diagnosis'],
                confidence=prediction['confidence'],
                risk_level=prediction['risk_level'],
                **{k: v for k, v in payload.items() if k not in LAB_FIELDS}
            )

            stage_note = '(Stage 1 only)' if prediction['skipped_stage2'] else '(Stage 1+2)'
            print(
                f"[MediPredict] Record {record.id} — "
                f"{prediction['diagnosis']} | {prediction['risk_level']} | "
                f"{prediction['confidence']}% {stage_note}"
                f"{' ⚠ LOW CONF' if prediction['low_confidence'] else ''}"
            )

            return Response({
                'diagnosis':            prediction['diagnosis'],
                'confidence':           prediction['confidence'],
                'risk_level':           prediction['risk_level'],
                'low_confidence':       prediction['low_confidence'],
                'sorted_probabilities': prediction['sorted_probabilities'],
                'class_probabilities':  prediction['class_probabilities'],
                'stage1_risk_probs':    prediction['stage1_risk_probs'],
                'medications':          get_medication_names(prediction['diagnosis']),
                'record_id':            record.id,
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'message': f"Prediction Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset  = HealthRecord.objects.filter(user=request.user).order_by('-created_at')
            latest    = queryset.first()
            full_name = request.user.get_full_name().strip() or request.user.username
            now       = timezone.now()

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
            return Response({'message': f"Trend Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            return Response({'message': f"Symptom Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DashboardScanHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            queryset      = HealthRecord.objects.filter(user=request.user).order_by('-created_at')
            disease_names = queryset.values_list('predicted_disease', flat=True).distinct()
            disease_map   = {
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
            for line in [
                f'Patient Name: {patient_name}',
                f'Report Date: {report_date}',
                f'Age: {record.age}',
                f'Gender Code: {record.gender}',
            ]:
                pdf.drawString(50, y, line)
                y -= 18

            # Clinical Vitals
            y -= 18
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(50, y, 'Clinical Vitals')
            y -= 28
            pdf.setFont('Helvetica', 11)
            for label, value in [
                ('Blood Pressure', f'{record.bp_systolic}/{record.bp_diastolic} mmHg'),
                ('BMI',            f'{record.bmi:.1f}'),
                ('Blood Sugar',    f'{record.sugar_level:.1f}'),
                ('Cholesterol',    f'{record.cholesterol:.1f}'),
                ('Heart Rate',     f'{record.heart_rate} bpm'),
            ]:
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

            risk_color = {'High': '#DC2626', 'Medium': '#D97706', 'Low': '#16A34A'}.get(record.risk_level, '#374151')
            pdf.setFillColor(colors.HexColor(risk_color))
            pdf.drawString(50, y, f'Risk Level        : {record.risk_level}')
            pdf.setFillColor(colors.HexColor('#1A1A2E'))
            y -= 28

            # Medications
            pdf.setFont('Helvetica-Bold', 14)
            pdf.drawString(50, y, 'Suggested Medications')
            y -= 24
            pdf.setFont('Helvetica', 11)
            medications = get_medication_names(record.predicted_disease)
            if medications:
                for med in medications:
                    pdf.drawString(60, y, f'• {med}')
                    y -= 16
            else:
                pdf.drawString(60, y, 'No specific medications mapped.')
                y -= 16

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