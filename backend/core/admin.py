from django.contrib import admin
from .models import Patient, Disease, Medication, HealthRecord

admin.site.register(Patient)
admin.site.register(Disease)
admin.site.register(Medication)
admin.site.register(HealthRecord)