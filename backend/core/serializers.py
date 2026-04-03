from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import HealthRecord, Symptom


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = '__all__'


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Username is already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Email is already registered.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MediPredictTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['id'] = user.id
        token['username'] = user.username
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSummarySerializer(self.user).data
        return data


class HealthRecordSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    diagnosis = serializers.CharField(source='predicted_disease', read_only=True)
    medications = serializers.SerializerMethodField()

    class Meta:
        model = HealthRecord
        fields = (
            'id',
            'date',
            'created_at',
            'diagnosis',
            'predicted_disease',
            'risk_level',
            'confidence',
            'bp_systolic',
            'bp_diastolic',
            'sugar_level',
            'cholesterol',
            'heart_rate',
            'bmi',
            'age',
            'gender',
            'symptom_fever',
            'symptom_cough',
            'symptom_fatigue',
            'symptom_headache',
            'symptom_chest_pain',
            'symptom_breathlessness',
            'symptom_sweating',
            'symptom_nausea',
            'medications',
        )

    def get_date(self, obj):
        return obj.created_at.strftime('%Y-%m-%d')

    def get_medications(self, obj):
        disease = getattr(obj, '_disease_prefetch', None)
        if disease is None:
            return []
        return [med.medicine_name for med in disease.medications.all()]
