import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_project.settings')
django.setup()

from core.models import Symptom

def seed_symptoms():
    symptoms_list = [
        'Fever', 'Cough', 'Fatigue', 'Headache', 'Chest Pain', 
        'Breathlessness', 'Sweating', 'Nausea'
    ]
    
    for name in symptoms_list:
        obj, created = Symptom.objects.get_or_create(symptom_name=name)
        if created:
            print(f"Added symptom: {name}")
        else:
            print(f"Symptom already exists: {name}")

if __name__ == "__main__":
    seed_symptoms()