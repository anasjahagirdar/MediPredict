from django.conf import settings
from django.db import models

class Symptom(models.Model):
    """Master lookup table for all possible symptoms (e.g., Fever, Cough)."""
    symptom_name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.symptom_name

class PatientSymptom(models.Model):
    """Links patients to their reported symptoms for specific records."""
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='symptoms')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
    reported_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('patient', 'symptom')

    def __str__(self):
        return f"{self.patient.name} - {self.symptom.symptom_name}"

class Patient(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=20) # We'll handle Male/Female/Other in React
    city = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Disease(models.Model):
    disease_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.disease_name

class Medication(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='medications')
    medicine_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.medicine_name} for {self.disease.disease_name}"

class HealthRecord(models.Model):
    RISK_CHOICES = (
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_records'
    )
    bp_systolic = models.IntegerField()
    bp_diastolic = models.IntegerField()
    sugar_level = models.FloatField()
    cholesterol = models.FloatField()
    heart_rate = models.IntegerField()
    bmi = models.FloatField()
    age = models.IntegerField()
    gender = models.IntegerField()
    symptom_fever = models.IntegerField(default=0)
    symptom_cough = models.IntegerField(default=0)
    symptom_fatigue = models.IntegerField(default=0)
    symptom_headache = models.IntegerField(default=0)
    symptom_chest_pain = models.IntegerField(default=0)
    symptom_breathlessness = models.IntegerField(default=0)
    symptom_sweating = models.IntegerField(default=0)
    symptom_nausea = models.IntegerField(default=0)
    predicted_disease = models.CharField(max_length=100)
    confidence = models.FloatField()
    risk_level = models.CharField(max_length=10, choices=RISK_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_record'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.predicted_disease} - {self.created_at:%Y-%m-%d}"
