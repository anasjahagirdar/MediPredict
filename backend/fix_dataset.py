"""
fix_dataset.py — Regenerate MediPredict dataset with proper clinical boundaries
Run from backend/ folder: python fix_dataset.py
"""
import pandas as pd
import numpy as np

np.random.seed(42)
N = 800  # samples per disease

def make_healthy(n):
    return pd.DataFrame({
        'bp_systolic':          np.random.randint(90, 120, n),
        'bp_diastolic':         np.random.randint(60, 80, n),
        'sugar_level':          np.random.uniform(70, 100, n),
        'cholesterol':          np.random.uniform(150, 200, n),
        'heart_rate':           np.random.randint(60, 80, n),
        'bmi':                  np.random.uniform(18, 25, n),
        'age':                  np.random.randint(18, 45, n),
        'gender':               np.random.randint(0, 2, n),
        'symptom_fever':        np.zeros(n, int),
        'symptom_cough':        np.zeros(n, int),
        'symptom_fatigue':      np.zeros(n, int),
        'symptom_headache':     np.zeros(n, int),
        'symptom_chest_pain':   np.zeros(n, int),
        'symptom_breathlessness': np.zeros(n, int),
        'symptom_sweating':     np.zeros(n, int),
        'symptom_nausea':       np.zeros(n, int),
        'hba1c':                np.random.uniform(4.0, 5.6, n),
        'ldl':                  np.random.uniform(50, 100, n),
        'hdl':                  np.random.uniform(50, 80, n),
        'disease_label':        'Healthy',
        'risk_level':           'Low',
    })

def make_hypertension(n):
    return pd.DataFrame({
        'bp_systolic':          np.random.randint(140, 200, n),
        'bp_diastolic':         np.random.randint(90, 120, n),
        'sugar_level':          np.random.uniform(70, 110, n),
        'cholesterol':          np.random.uniform(180, 280, n),
        'heart_rate':           np.random.randint(70, 100, n),
        'bmi':                  np.random.uniform(25, 40, n),
        'age':                  np.random.randint(40, 75, n),
        'gender':               np.random.randint(0, 2, n),
        'symptom_fever':        np.zeros(n, int),
        'symptom_cough':        np.zeros(n, int),
        'symptom_fatigue':      np.random.randint(0, 2, n),
        'symptom_headache':     np.random.randint(0, 2, n),
        'symptom_chest_pain':   np.zeros(n, int),
        'symptom_breathlessness': np.random.randint(0, 2, n),
        'symptom_sweating':     np.random.randint(0, 2, n),
        'symptom_nausea':       np.zeros(n, int),
        'hba1c':                np.random.uniform(5.0, 6.4, n),
        'ldl':                  np.random.uniform(120, 180, n),
        'hdl':                  np.random.uniform(30, 50, n),
        'disease_label':        'Hypertension',
        'risk_level':           'Medium',
    })

def make_diabetes(n):
    return pd.DataFrame({
        'bp_systolic':          np.random.randint(110, 160, n),
        'bp_diastolic':         np.random.randint(70, 100, n),
        'sugar_level':          np.random.uniform(180, 500, n),
        'cholesterol':          np.random.uniform(180, 280, n),
        'heart_rate':           np.random.randint(65, 95, n),
        'bmi':                  np.random.uniform(27, 50, n),
        'age':                  np.random.randint(30, 70, n),
        'gender':               np.random.randint(0, 2, n),
        'symptom_fever':        np.zeros(n, int),
        'symptom_cough':        np.zeros(n, int),
        'symptom_fatigue':      np.random.randint(0, 2, n),
        'symptom_headache':     np.random.randint(0, 2, n),
        'symptom_chest_pain':   np.zeros(n, int),
        'symptom_breathlessness': np.zeros(n, int),
        'symptom_sweating':     np.random.randint(0, 2, n),
        'symptom_nausea':       np.random.randint(0, 2, n),
        'hba1c':                np.random.uniform(6.5, 12.0, n),
        'ldl':                  np.random.uniform(100, 190, n),
        'hdl':                  np.random.uniform(25, 50, n),
        'disease_label':        'Diabetes',
        'risk_level':           'High',
    })

def make_heart_disease(n):
    return pd.DataFrame({
        'bp_systolic':          np.random.randint(130, 200, n),
        'bp_diastolic':         np.random.randint(85, 120, n),
        'sugar_level':          np.random.uniform(70, 150, n),
        'cholesterol':          np.random.uniform(220, 400, n),
        'heart_rate':           np.random.randint(80, 120, n),
        'bmi':                  np.random.uniform(22, 40, n),
        'age':                  np.random.randint(45, 80, n),
        'gender':               np.random.randint(0, 2, n),
        'symptom_fever':        np.zeros(n, int),
        'symptom_cough':        np.zeros(n, int),
        'symptom_fatigue':      np.random.randint(0, 2, n),
        'symptom_headache':     np.zeros(n, int),
        'symptom_chest_pain':   np.ones(n, int),
        'symptom_breathlessness': np.random.randint(0, 2, n),
        'symptom_sweating':     np.random.randint(0, 2, n),
        'symptom_nausea':       np.random.randint(0, 2, n),
        'hba1c':                np.random.uniform(5.0, 7.0, n),
        'ldl':                  np.random.uniform(160, 220, n),
        'hdl':                  np.random.uniform(20, 40, n),
        'disease_label':        'Heart Disease',
        'risk_level':           'High',
    })

def make_obesity(n):
    return pd.DataFrame({
        'bp_systolic':          np.random.randint(110, 150, n),
        'bp_diastolic':         np.random.randint(70, 95, n),
        'sugar_level':          np.random.uniform(90, 160, n),
        'cholesterol':          np.random.uniform(180, 260, n),
        'heart_rate':           np.random.randint(75, 105, n),
        'bmi':                  np.random.uniform(30, 60, n),
        'age':                  np.random.randint(25, 65, n),
        'gender':               np.random.randint(0, 2, n),
        'symptom_fever':        np.zeros(n, int),
        'symptom_cough':        np.zeros(n, int),
        'symptom_fatigue':      np.random.randint(0, 2, n),
        'symptom_headache':     np.zeros(n, int),
        'symptom_chest_pain':   np.zeros(n, int),
        'symptom_breathlessness': np.random.randint(0, 2, n),
        'symptom_sweating':     np.random.randint(0, 2, n),
        'symptom_nausea':       np.zeros(n, int),
        'hba1c':                np.random.uniform(5.5, 8.0, n),
        'ldl':                  np.random.uniform(110, 190, n),
        'hdl':                  np.random.uniform(25, 45, n),
        'disease_label':        'Obesity',
        'risk_level':           'Medium',
    })

# Generate all
df = pd.concat([
    make_healthy(N),
    make_hypertension(N),
    make_diabetes(N),
    make_heart_disease(N),
    make_obesity(N),
], ignore_index=True)

# Shuffle
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save
df.to_csv('medipredict_dataset_v2.csv', index=False)
print(f"Dataset saved: {len(df)} rows")
print(df['disease_label'].value_counts())
print("\nHealthy ranges check:")
h = df[df['disease_label']=='Healthy']
print(h[['bp_systolic','sugar_level','bmi','hba1c','ldl','hdl']].describe().loc[['mean','min','max']])