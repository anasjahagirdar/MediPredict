"""
add_lab_features.py — Add HbA1c, LDL, HDL to MediPredict Dataset
=================================================================
Derives 3 new clinically grounded lab features from existing columns:

  hba1c  — Glycated Hemoglobin (%)
             Derived from sugar_level + disease_label
             Normal < 5.7 | Pre-diabetic 5.7–6.4 | Diabetic ≥ 6.5

  ldl    — Low-Density Lipoprotein (mg/dL)
             Derived from cholesterol + disease_label
             Optimal < 100 | Borderline 100–129 | High ≥ 130

  hdl    — High-Density Lipoprotein (mg/dL)
             Derived from cholesterol + disease_label (inverse relationship)
             Low < 40 | Normal 40–59 | High (protective) ≥ 60

Run from the backend/ folder:
    python add_lab_features.py

Input : medipredict_dataset_expanded.csv
Output: medipredict_dataset_v2.csv
"""

import numpy as np
import pandas as pd

np.random.seed(42)

INPUT_PATH  = 'medipredict_dataset_expanded.csv'
OUTPUT_PATH = 'medipredict_dataset_v2.csv'

print("\n[add_lab_features] Loading dataset...")
df = pd.read_csv(INPUT_PATH)
print(f"  Rows: {len(df):,}  |  Columns: {len(df.columns)}")
print(f"  Disease distribution:\n{df['disease_label'].value_counts().to_string()}")


# ── HbA1c Generation ─────────────────────────────────────────────────────────
# Clinical basis:
#   HbA1c ≈ (sugar_level / 28.7) - 46.7/28.7  (Nathan formula approximation)
#   But we also apply disease-label offsets to make it diagnostically meaningful:
#     Diabetes     → push into 6.5–11.0 range (confirmed diabetic)
#     Healthy      → keep in 4.5–5.6 range (normal)
#     Others       → 5.4–6.8 range (borderline / metabolic stress)

def generate_hba1c(row):
    sugar  = row['sugar_level']
    label  = row['disease_label']

    # Base estimate from sugar level (simplified Nathan formula)
    base = (sugar + 46.7) / 28.7

    if label == 'Diabetes':
        # Diabetic range: 6.5–11.0, correlated with sugar
        center = np.clip(base, 6.5, 11.0)
        noise  = np.random.normal(0, 0.4)
        return round(np.clip(center + noise, 6.5, 12.0), 1)

    elif label == 'Healthy':
        # Normal range: 4.5–5.6
        center = np.clip(base, 4.5, 5.6)
        noise  = np.random.normal(0, 0.2)
        return round(np.clip(center + noise, 4.0, 5.6), 1)

    elif label == 'Obesity':
        # Pre-diabetic / insulin resistant: 5.7–7.5
        center = np.clip(base, 5.7, 7.5)
        noise  = np.random.normal(0, 0.4)
        return round(np.clip(center + noise, 5.4, 8.0), 1)

    else:
        # Hypertension / Heart Disease: metabolic stress range 5.4–7.0
        center = np.clip(base, 5.4, 7.0)
        noise  = np.random.normal(0, 0.35)
        return round(np.clip(center + noise, 4.8, 8.0), 1)


# ── LDL Generation ───────────────────────────────────────────────────────────
# Clinical basis:
#   LDL is typically 60–70% of total cholesterol (Friedewald approximation)
#   Disease-label offsets:
#     Heart Disease → high LDL (130–200 mg/dL) — key cardiac risk marker
#     Healthy       → optimal LDL (< 100 mg/dL)
#     Others        → borderline range (100–160 mg/dL)

def generate_ldl(row):
    chol  = row['cholesterol']
    label = row['disease_label']

    # Base: LDL ≈ 60–70% of total cholesterol
    base = chol * np.random.uniform(0.60, 0.70)

    if label == 'Heart Disease':
        # High LDL — primary cardiac risk factor
        offset = np.random.normal(25, 10)
        return round(np.clip(base + offset, 100, 220), 1)

    elif label == 'Healthy':
        # Optimal LDL
        offset = np.random.normal(-20, 8)
        return round(np.clip(base + offset, 50, 100), 1)

    elif label == 'Hypertension':
        # Mildly elevated
        offset = np.random.normal(10, 8)
        return round(np.clip(base + offset, 90, 180), 1)

    elif label == 'Diabetes':
        # Often elevated due to insulin resistance
        offset = np.random.normal(15, 10)
        return round(np.clip(base + offset, 90, 190), 1)

    else:  # Obesity
        # Often elevated, especially with metabolic syndrome
        offset = np.random.normal(20, 10)
        return round(np.clip(base + offset, 100, 200), 1)


# ── HDL Generation ───────────────────────────────────────────────────────────
# Clinical basis:
#   HDL is inversely related to cardiovascular risk
#   Low HDL (< 40) is itself a cardiac risk factor
#   Disease-label offsets:
#     Heart Disease → low HDL (25–45 mg/dL)
#     Healthy       → high HDL (50–80 mg/dL) — protective
#     Obesity       → low HDL (30–50 mg/dL) — fat tissue suppresses HDL
#     Others        → moderate range (35–60 mg/dL)

def generate_hdl(row):
    label = row['disease_label']
    bmi   = row['bmi']

    # BMI penalty — higher BMI suppresses HDL
    bmi_penalty = max(0, (bmi - 25) * 0.5)

    if label == 'Healthy':
        base  = np.random.normal(62, 8)
        return round(np.clip(base - bmi_penalty, 45, 90), 1)

    elif label == 'Heart Disease':
        base  = np.random.normal(38, 7)
        return round(np.clip(base - bmi_penalty, 20, 55), 1)

    elif label == 'Obesity':
        base  = np.random.normal(40, 7)
        return round(np.clip(base - bmi_penalty, 25, 55), 1)

    elif label == 'Hypertension':
        base  = np.random.normal(48, 8)
        return round(np.clip(base - bmi_penalty, 30, 65), 1)

    else:  # Diabetes
        base  = np.random.normal(44, 8)
        return round(np.clip(base - bmi_penalty, 28, 60), 1)


# ── Apply to Dataset ──────────────────────────────────────────────────────────

print("\n[add_lab_features] Generating HbA1c...")
df['hba1c'] = df.apply(generate_hba1c, axis=1)

print("[add_lab_features] Generating LDL...")
df['ldl'] = df.apply(generate_ldl, axis=1)

print("[add_lab_features] Generating HDL...")
df['hdl'] = df.apply(generate_hdl, axis=1)


# ── Validation ────────────────────────────────────────────────────────────────

print("\n[add_lab_features] Validation — Per-disease averages:")
summary = df.groupby('disease_label')[['hba1c', 'ldl', 'hdl']].mean().round(2)
print(summary.to_string())

print("\n[add_lab_features] Overall ranges:")
for col in ['hba1c', 'ldl', 'hdl']:
    print(f"  {col}: min={df[col].min():.1f}  max={df[col].max():.1f}  mean={df[col].mean():.1f}")

# Sanity checks
assert df['hba1c'].between(3.0, 14.0).all(),  "HbA1c out of range"
assert df['ldl'].between(30.0, 250.0).all(),  "LDL out of range"
assert df['hdl'].between(15.0, 100.0).all(),  "HDL out of range"
print("\n  ✔ All range assertions passed.")


# ── Save ──────────────────────────────────────────────────────────────────────

df.to_csv(OUTPUT_PATH, index=False)
print(f"\n[add_lab_features] ✔ Saved → {OUTPUT_PATH}")
print(f"  Rows: {len(df):,}  |  Columns: {len(df.columns)}")
print(f"  New columns added: hba1c, ldl, hdl")
print(f"\n  → Next: run 'python retrain_v2.py' to retrain with 19 features\n")
