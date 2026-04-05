"""
retrain_v2.py — MediPredict Two-Stage Model Training (19 Features)
==================================================================
Stage 1: Risk Level classifier (Low / Medium / High)
Stage 2: Disease classifier (Medium + High rows only)

New features added vs v1:
  hba1c  — Glycated Hemoglobin (%) → separates Diabetes from Obesity
  ldl    — LDL Cholesterol (mg/dL) → separates Heart Disease from Hypertension
  hdl    — HDL Cholesterol (mg/dL) → cardiac protective factor

Run from the backend/ folder:
    python retrain_v2.py

Artifacts saved to core/ml/:
    risk_model.pkl          Stage 1 — Risk Level classifier
    risk_label_encoder.pkl  Stage 1 — LabelEncoder for risk levels
    model.pkl               Stage 2 — Disease classifier (Medium/High only)
    label_encoder.pkl       Stage 2 — LabelEncoder for disease names
    feature_list.json       Shared — 19-feature ordered list
    best_params.json        Stage 2 — best XGBoost hyperparameters
"""

import json
import os
import warnings

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import (
    RandomizedSearchCV, StratifiedKFold,
    cross_val_score, train_test_split
)
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────

DATA_PATH   = 'medipredict_dataset_v2.csv'
ML_DIR      = os.path.join('core', 'ml')
RANDOM_SEED = 42

# 19 features — original 16 + hba1c, ldl, hdl
FEATURES = [
    'bp_systolic', 'bp_diastolic', 'sugar_level', 'cholesterol',
    'heart_rate', 'bmi', 'age', 'gender',
    'symptom_fever', 'symptom_cough', 'symptom_fatigue', 'symptom_headache',
    'symptom_chest_pain', 'symptom_breathlessness', 'symptom_sweating', 'symptom_nausea',
    'hba1c', 'ldl', 'hdl',
]

DISEASE_TO_RISK = {
    'Healthy':       'Low',
    'Hypertension':  'Medium',
    'Diabetes':      'Medium',
    'Obesity':       'Medium',
    'Heart Disease': 'High',
}

os.makedirs(ML_DIR, exist_ok=True)


# ── Load & Validate ───────────────────────────────────────────────────────────

print("\n[Stage 0] Loading dataset...")
df = pd.read_csv(DATA_PATH)
print(f"  Rows: {len(df):,}  |  Columns: {len(df.columns)}")

missing = [f for f in FEATURES if f not in df.columns]
if missing:
    raise ValueError(
        f"Missing columns: {missing}\n"
        f"  → Run 'python add_lab_features.py' first to generate hba1c, ldl, hdl."
    )

df = df.dropna(subset=FEATURES + ['disease_label'])
print(f"  After dropna: {len(df):,} rows")
print(f"  Disease distribution:\n{df['disease_label'].value_counts().to_string()}")

# Save feature list — shared by both stages and views.py
feature_list_path = os.path.join(ML_DIR, 'feature_list.json')
with open(feature_list_path, 'w') as f:
    json.dump(FEATURES, f)
print(f"\n  ✔ Feature list saved ({len(FEATURES)} features) → {feature_list_path}")


# ── Stage 1: Risk Level Classifier ───────────────────────────────────────────

print("\n" + "="*60)
print("[Stage 1] Training Risk Level Classifier (Low / Medium / High)")
print("="*60)

df['risk_label'] = df['disease_label'].map(DISEASE_TO_RISK)
unmapped = df['risk_label'].isna().sum()
if unmapped > 0:
    print(f"  ⚠ {unmapped} rows unmapped — dropping.")
    df = df.dropna(subset=['risk_label'])

print(f"\n  Risk label distribution:\n{df['risk_label'].value_counts().to_string()}")

risk_encoder = LabelEncoder()
y_risk = risk_encoder.fit_transform(df['risk_label'])
X_risk = df[FEATURES].copy()
print(f"\n  Risk classes: {list(risk_encoder.classes_)}")

X_risk_train, X_risk_test, y_risk_train, y_risk_test = train_test_split(
    X_risk, y_risk, test_size=0.2, random_state=RANDOM_SEED, stratify=y_risk
)

# Use class_weight='balanced' + higher n_estimators for better High recall
risk_model = RandomForestClassifier(
    n_estimators=500,
    max_depth=25,
    min_samples_leaf=1,
    class_weight='balanced',
    random_state=RANDOM_SEED,
    n_jobs=-1,
)

print("\n  Fitting Stage 1 model...")
risk_model.fit(X_risk_train, y_risk_train)

y_risk_pred = risk_model.predict(X_risk_test)
risk_accuracy = (y_risk_pred == y_risk_test).mean() * 100

print(f"\n  Stage 1 Test Accuracy: {risk_accuracy:.2f}%")
print(f"\n  Classification Report:\n")
print(classification_report(y_risk_test, y_risk_pred, target_names=risk_encoder.classes_))

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
cv_scores = cross_val_score(risk_model, X_risk, y_risk, cv=cv, scoring='accuracy', n_jobs=-1)
print(f"  5-Fold CV: {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

# Feature importance for Stage 1
feat_imp = pd.Series(risk_model.feature_importances_, index=FEATURES).sort_values(ascending=False)
print(f"\n  Top 5 features for risk classification:")
print(feat_imp.head(5).to_string())

joblib.dump(risk_model,   os.path.join(ML_DIR, 'risk_model.pkl'))
joblib.dump(risk_encoder, os.path.join(ML_DIR, 'risk_label_encoder.pkl'))
print(f"\n  ✔ risk_model.pkl saved")
print(f"  ✔ risk_label_encoder.pkl saved")


# ── Stage 2: Disease Classifier (Medium + High only) ─────────────────────────

print("\n" + "="*60)
print("[Stage 2] Training Disease Classifier (Medium + High rows only)")
print("="*60)

df_s2 = df[df['risk_label'].isin(['Medium', 'High'])].copy()
print(f"\n  Rows: {len(df_s2):,}")
print(f"  Distribution:\n{df_s2['disease_label'].value_counts().to_string()}")

X_s2 = df_s2[FEATURES].copy()
disease_encoder = LabelEncoder()
y_s2 = disease_encoder.fit_transform(df_s2['disease_label'])
print(f"\n  Disease classes: {list(disease_encoder.classes_)}")

X_s2_train, X_s2_test, y_s2_train, y_s2_test = train_test_split(
    X_s2, y_s2, test_size=0.2, random_state=RANDOM_SEED, stratify=y_s2
)

sample_weights = compute_sample_weight('balanced', y_s2_train)

print("\n  Running RandomizedSearchCV for XGBoost (30 iterations)...")
xgb_param_grid = {
    'n_estimators':     [200, 300, 400, 500],
    'max_depth':        [4, 6, 8, 10],
    'learning_rate':    [0.02, 0.05, 0.08, 0.1],
    'subsample':        [0.7, 0.8, 0.9],
    'colsample_bytree': [0.7, 0.8, 1.0],
    'reg_alpha':        [0, 0.01, 0.1],
    'reg_lambda':       [1.0, 1.5, 2.0],
    'min_child_weight': [1, 3, 5],
}

xgb_base = XGBClassifier(
    objective='multi:softprob',
    eval_metric='mlogloss',
    use_label_encoder=False,
    random_state=RANDOM_SEED,
    n_jobs=-1,
    verbosity=0,
)

search = RandomizedSearchCV(
    xgb_base,
    xgb_param_grid,
    n_iter=30,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED),
    scoring='accuracy',
    random_state=RANDOM_SEED,
    n_jobs=-1,
    verbose=1,
)
search.fit(X_s2_train, y_s2_train, sample_weight=sample_weights)

best_params = search.best_params_
print(f"\n  Best params: {best_params}")
print(f"  Best CV accuracy: {search.best_score_*100:.2f}%")

with open(os.path.join(ML_DIR, 'best_params.json'), 'w') as f:
    json.dump(best_params, f, indent=2)
print(f"  ✔ best_params.json saved")

# Build stacking ensemble
xgb_tuned = XGBClassifier(
    **best_params,
    objective='multi:softprob',
    eval_metric='mlogloss',
    use_label_encoder=False,
    random_state=RANDOM_SEED,
    n_jobs=-1,
    verbosity=0,
)

rf_estimator = RandomForestClassifier(
    n_estimators=300,
    max_depth=20,
    class_weight='balanced',
    random_state=RANDOM_SEED,
    n_jobs=-1,
)

meta_learner = LogisticRegression(
    max_iter=1000,
    solver='lbfgs',
    random_state=RANDOM_SEED,
)

stage2_model = StackingClassifier(
    estimators=[('xgb', xgb_tuned), ('rf', rf_estimator)],
    final_estimator=meta_learner,
    cv=5,
    n_jobs=-1,
)

print("\n  Fitting Stage 2 StackingClassifier...")
stage2_model.fit(X_s2_train, y_s2_train, sample_weight=sample_weights)

y_s2_pred    = stage2_model.predict(X_s2_test)
s2_accuracy  = (y_s2_pred == y_s2_test).mean() * 100

print(f"\n  Stage 2 Test Accuracy: {s2_accuracy:.2f}%")
print(f"\n  Classification Report:\n")
print(classification_report(y_s2_test, y_s2_pred, target_names=disease_encoder.classes_))

print(f"\n  Confusion Matrix:")
cm    = confusion_matrix(y_s2_test, y_s2_pred)
cm_df = pd.DataFrame(cm, index=disease_encoder.classes_, columns=disease_encoder.classes_)
print(cm_df.to_string())

# Feature importance from RF component
rf_in_stack = stage2_model.named_estimators_['rf']
feat_imp_s2 = pd.Series(rf_in_stack.feature_importances_, index=FEATURES).sort_values(ascending=False)
print(f"\n  Top 8 features for disease classification:")
print(feat_imp_s2.head(8).to_string())

joblib.dump(stage2_model,    os.path.join(ML_DIR, 'model.pkl'))
joblib.dump(disease_encoder, os.path.join(ML_DIR, 'label_encoder.pkl'))
print(f"\n  ✔ model.pkl saved")
print(f"  ✔ label_encoder.pkl saved")


# ── Summary ───────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print("TRAINING COMPLETE — Summary")
print("="*60)
print(f"  Features used        : {len(FEATURES)} (added hba1c, ldl, hdl)")
print(f"  Stage 1 accuracy     : {risk_accuracy:.2f}%")
print(f"  Stage 2 accuracy     : {s2_accuracy:.2f}%")
print(f"  Stage 2 trained on   : {len(df_s2):,} rows (Medium + High only)")
print(f"\n  Artifacts in {ML_DIR}/:")
for fname in ['risk_model.pkl', 'risk_label_encoder.pkl', 'model.pkl',
              'label_encoder.pkl', 'feature_list.json', 'best_params.json']:
    path   = os.path.join(ML_DIR, fname)
    exists = '✔' if os.path.exists(path) else '✘ MISSING'
    print(f"    {exists}  {fname}")
print("\n  → Restart Django: python manage.py runserver")
print("="*60 + "\n")