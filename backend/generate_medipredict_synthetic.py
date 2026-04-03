"""
MediPredict Synthetic Data Generator
=====================================
Generates 1,000 clinically-grounded synthetic rows to augment training data
and teach the model hard medical emergency thresholds.

Segment breakdown:
  - 300 rows  → Extreme Emergencies   (→ High Risk / critical disease labels)
  - 300 rows  → Perfectly Healthy     (→ Low Risk / Healthy label)
  - 400 rows  → Borderline Realistic  (→ Medium/High Risk mix with correlated vitals)

Clinical thresholds used:
  • Hypertensive Crisis     : SBP > 180 mmHg, DBP > 120 mmHg
  • Diabetic Emergency      : Blood Sugar > 300 mg/dL (hyperglycemic crisis)
  • Dangerously High Chol   : > 300 mg/dL (severe hypercholesterolemia)
  • Tachycardia Emergency   : Heart Rate > 140 bpm at rest
  • Morbid Obesity          : BMI > 40
  • Ideal BP                : SBP 100–119 mmHg, DBP 65–79 mmHg
  • Normal fasting sugar    : 70–99 mg/dL
  • Optimal cholesterol     : < 150 mg/dL
  • Healthy resting HR      : 55–75 bpm
  • Healthy BMI             : 18.5–24.9
  • Borderline correlation  : High BMI statistically correlated with
                              elevated BP, cholesterol, and blood sugar.

Author : MediPredict Data Pipeline
"""

import numpy as np
import pandas as pd

# ── Reproducibility ─────────────────────────────────────────────────────────
SEED = 42
rng  = np.random.default_rng(SEED)

INPUT_CSV  = "training_data_augmented.csv"
OUTPUT_CSV = "medipredict_dataset_expanded.csv"

DISEASE_LABELS = ["Healthy", "Hypertension", "Heart Disease", "Diabetes", "Obesity"]


# ════════════════════════════════════════════════════════════════════════════
# HELPER – random binary symptoms
# ════════════════════════════════════════════════════════════════════════════
def rand_symptoms(n: int, probs: dict) -> pd.DataFrame:
    """
    Generate binary symptom columns for n rows.
    probs: {col_name: probability_of_1}
    """
    cols = [
        "symptom_fever", "symptom_cough", "symptom_fatigue",
        "symptom_headache", "symptom_chest_pain", "symptom_breathlessness",
        "symptom_sweating", "symptom_nausea",
    ]
    data = {}
    for col in cols:
        p = probs.get(col, 0.05)
        data[col] = rng.binomial(1, p, n)
    return pd.DataFrame(data)


# ════════════════════════════════════════════════════════════════════════════
# SEGMENT 1 – EXTREME EMERGENCIES  (300 rows)
# ════════════════════════════════════════════════════════════════════════════
def generate_extreme_emergencies(n: int = 300) -> pd.DataFrame:
    """
    Simulate patients in acute medical crises.
    Vitals are pushed past clinical danger thresholds.
    disease_label is heavily skewed toward critical conditions.
    """
    records = []

    # --- Sub-group A: Hypertensive Crisis (≈90 rows) -----------------------
    n_htn = n // 3
    sbp  = rng.integers(181, 240, n_htn)
    dbp  = rng.integers(121, 150, n_htn)
    sugar = rng.uniform(90, 200, n_htn)          # may or may not be diabetic
    chol  = rng.uniform(220, 340, n_htn)
    hr    = rng.integers(95, 150, n_htn)
    bmi   = rng.uniform(27, 45, n_htn)
    age   = rng.integers(45, 90, n_htn)
    gender = rng.integers(0, 2, n_htn)
    symp  = rand_symptoms(n_htn, {
        "symptom_headache": 0.85, "symptom_chest_pain": 0.70,
        "symptom_breathlessness": 0.65, "symptom_nausea": 0.55,
        "symptom_sweating": 0.60, "symptom_fatigue": 0.55,
    })
    label = rng.choice(
        ["Hypertension", "Heart Disease"],
        size=n_htn, p=[0.60, 0.40]
    )
    df_a = pd.DataFrame({
        "bp_systolic": sbp, "bp_diastolic": dbp,
        "sugar_level": np.round(sugar, 1), "cholesterol": np.round(chol, 1),
        "heart_rate": hr, "bmi": np.round(bmi, 1),
        "age": age, "gender": gender,
    })
    df_a = pd.concat([df_a.reset_index(drop=True), symp.reset_index(drop=True)], axis=1)
    df_a["disease_label"] = label

    # --- Sub-group B: Diabetic / Hyperglycemic Crisis (≈90 rows) -----------
    n_dia = n // 3
    sbp   = rng.integers(130, 190, n_dia)
    dbp   = rng.integers(85, 130, n_dia)
    sugar = rng.uniform(301, 600, n_dia)         # hyperglycemic crisis threshold
    chol  = rng.uniform(200, 320, n_dia)
    hr    = rng.integers(100, 160, n_dia)        # tachycardia from metabolic stress
    bmi   = rng.uniform(28, 50, n_dia)
    age   = rng.integers(30, 85, n_dia)
    gender = rng.integers(0, 2, n_dia)
    symp  = rand_symptoms(n_dia, {
        "symptom_fatigue": 0.90, "symptom_nausea": 0.75,
        "symptom_sweating": 0.70, "symptom_headache": 0.60,
        "symptom_breathlessness": 0.50, "symptom_fever": 0.30,
    })
    label = rng.choice(
        ["Diabetes", "Heart Disease"],
        size=n_dia, p=[0.70, 0.30]
    )
    df_b = pd.DataFrame({
        "bp_systolic": sbp, "bp_diastolic": dbp,
        "sugar_level": np.round(sugar, 1), "cholesterol": np.round(chol, 1),
        "heart_rate": hr, "bmi": np.round(bmi, 1),
        "age": age, "gender": gender,
    })
    df_b = pd.concat([df_b.reset_index(drop=True), symp.reset_index(drop=True)], axis=1)
    df_b["disease_label"] = label

    # --- Sub-group C: Morbid Obesity + Multi-system Failure (≈120 rows) ----
    n_obs = n - n_htn - n_dia
    sbp   = rng.integers(160, 230, n_obs)
    dbp   = rng.integers(100, 145, n_obs)
    sugar = rng.uniform(150, 450, n_obs)
    chol  = rng.uniform(260, 400, n_obs)         # severe hypercholesterolemia
    hr    = rng.integers(110, 180, n_obs)        # extreme tachycardia
    bmi   = rng.uniform(40.1, 65, n_obs)         # morbid obesity (BMI > 40)
    age   = rng.integers(35, 90, n_obs)
    gender = rng.integers(0, 2, n_obs)
    symp  = rand_symptoms(n_obs, {
        "symptom_chest_pain": 0.75, "symptom_breathlessness": 0.85,
        "symptom_fatigue": 0.90, "symptom_sweating": 0.65,
        "symptom_headache": 0.50, "symptom_nausea": 0.60,
    })
    label = rng.choice(
        ["Obesity", "Heart Disease", "Hypertension", "Diabetes"],
        size=n_obs, p=[0.40, 0.30, 0.20, 0.10]
    )
    df_c = pd.DataFrame({
        "bp_systolic": sbp, "bp_diastolic": dbp,
        "sugar_level": np.round(sugar, 1), "cholesterol": np.round(chol, 1),
        "heart_rate": hr, "bmi": np.round(bmi, 1),
        "age": age, "gender": gender,
    })
    df_c = pd.concat([df_c.reset_index(drop=True), symp.reset_index(drop=True)], axis=1)
    df_c["disease_label"] = label

    return pd.concat([df_a, df_b, df_c], ignore_index=True)


# ════════════════════════════════════════════════════════════════════════════
# SEGMENT 2 – PERFECTLY HEALTHY  (300 rows)
# ════════════════════════════════════════════════════════════════════════════
def generate_perfectly_healthy(n: int = 300) -> pd.DataFrame:
    """
    Simulate patients with ideal vitals.
    Ranges conform to AHA / WHO ideal health guidelines.
    disease_label is exclusively 'Healthy'.
    """
    sbp    = rng.integers(100, 120, n)           # normal SBP (AHA: < 120 ideal)
    dbp    = rng.integers(65, 80, n)             # normal DBP
    sugar  = rng.uniform(72, 99, n)              # normal fasting glucose
    chol   = rng.uniform(120, 179, n)            # optimal cholesterol (< 200)
    hr     = rng.integers(55, 75, n)             # healthy resting heart rate
    bmi    = rng.uniform(18.5, 24.9, n)          # healthy BMI
    age    = rng.integers(18, 65, n)
    gender = rng.integers(0, 2, n)
    symp   = rand_symptoms(n, {
        # Very low symptom probability – essentially asymptomatic
        "symptom_fever": 0.03, "symptom_cough": 0.04,
        "symptom_fatigue": 0.05, "symptom_headache": 0.04,
        "symptom_chest_pain": 0.01, "symptom_breathlessness": 0.02,
        "symptom_sweating": 0.03, "symptom_nausea": 0.02,
    })

    df = pd.DataFrame({
        "bp_systolic": sbp, "bp_diastolic": dbp,
        "sugar_level": np.round(sugar, 1), "cholesterol": np.round(chol, 1),
        "heart_rate": hr, "bmi": np.round(bmi, 1),
        "age": age, "gender": gender,
    })
    df = pd.concat([df.reset_index(drop=True), symp.reset_index(drop=True)], axis=1)
    df["disease_label"] = "Healthy"
    return df


# ════════════════════════════════════════════════════════════════════════════
# SEGMENT 3 – REALISTIC BORDERLINE CASES  (400 rows)
# ════════════════════════════════════════════════════════════════════════════
def generate_borderline_cases(n: int = 400) -> pd.DataFrame:
    """
    Simulate realistic patients with correlated risk factors.
    Key correlation: higher BMI → higher BP, cholesterol, blood sugar.
    This represents the metabolic syndrome phenotype.
    disease_label is a mix of Medium/High risk conditions.
    """
    # Step 1: Draw BMI as the root causal variable
    bmi = rng.uniform(22, 42, n)

    # Step 2: Derive correlated vitals from BMI with added noise
    # Clinical basis: each BMI unit above 25 adds ~1 mmHg SBP (approx. linear)
    bmi_excess = np.maximum(bmi - 25, 0)

    sbp_base = 115 + (bmi_excess * 1.2)
    sbp       = np.clip(
        sbp_base + rng.normal(0, 10, n), 105, 185
    ).astype(int)

    dbp_base = 72 + (bmi_excess * 0.7)
    dbp       = np.clip(
        dbp_base + rng.normal(0, 8, n), 60, 130
    ).astype(int)

    # Blood sugar: rises with BMI (insulin resistance) + noise
    sugar_base = 85 + (bmi_excess * 2.5)
    sugar       = np.clip(
        sugar_base + rng.normal(0, 25, n), 70, 310
    )

    # Cholesterol: rises with BMI + noise
    chol_base = 170 + (bmi_excess * 3.0)
    chol       = np.clip(
        chol_base + rng.normal(0, 30, n), 150, 320
    )

    # Heart rate: slight elevation with obesity
    hr  = np.clip(
        75 + (bmi_excess * 0.8) + rng.normal(0, 12, n), 55, 145
    ).astype(int)

    age    = rng.integers(25, 80, n)
    gender = rng.integers(0, 2, n)

    # Step 3: Symptom probability also scales with severity of vitals
    bp_severity    = np.clip((sbp - 115) / 70, 0, 1)   # 0→1 as SBP goes 115→185
    sugar_severity = np.clip((sugar - 85) / 225, 0, 1)

    symp_cols = [
        "symptom_fever", "symptom_cough", "symptom_fatigue",
        "symptom_headache", "symptom_chest_pain", "symptom_breathlessness",
        "symptom_sweating", "symptom_nausea",
    ]
    symp_data = {}
    base_probs = {
        "symptom_fever": 0.08,    "symptom_cough": 0.10,
        "symptom_fatigue": 0.35,  "symptom_headache": 0.30,
        "symptom_chest_pain": 0.25, "symptom_breathlessness": 0.30,
        "symptom_sweating": 0.25, "symptom_nausea": 0.20,
    }
    # Scale symptoms by BP + sugar severity
    scale_map = {
        "symptom_headache": bp_severity,
        "symptom_chest_pain": bp_severity,
        "symptom_breathlessness": (bp_severity + sugar_severity) / 2,
        "symptom_fatigue": sugar_severity,
        "symptom_sweating": sugar_severity,
        "symptom_nausea": sugar_severity,
    }
    for col in symp_cols:
        scale      = scale_map.get(col, np.zeros(n))
        p_col      = np.clip(base_probs[col] + 0.4 * scale, 0.0, 0.95)
        symp_data[col] = rng.binomial(1, p_col)

    # Step 4: Assign disease label using clinical rules
    def assign_label(i):
        s  = sugar[i]
        b  = sbp[i]
        bm = bmi[i]
        c  = chol[i]
        if s > 250:
            return "Diabetes"
        if b > 160:
            return rng.choice(["Hypertension", "Heart Disease"], p=[0.55, 0.45])
        if bm > 35:
            return rng.choice(["Obesity", "Hypertension", "Diabetes"], p=[0.50, 0.30, 0.20])
        if c > 260:
            return rng.choice(["Heart Disease", "Hypertension"], p=[0.60, 0.40])
        if s > 180:
            return rng.choice(["Diabetes", "Obesity"], p=[0.65, 0.35])
        if b > 140 or c > 230:
            return rng.choice(["Hypertension", "Heart Disease", "Healthy"], p=[0.50, 0.35, 0.15])
        return rng.choice(["Healthy", "Hypertension"], p=[0.50, 0.50])

    labels = [assign_label(i) for i in range(n)]

    df = pd.DataFrame({
        "bp_systolic": sbp, "bp_diastolic": dbp,
        "sugar_level": np.round(sugar, 1), "cholesterol": np.round(chol, 1),
        "heart_rate": hr, "bmi": np.round(bmi, 1),
        "age": age, "gender": gender,
    })
    df = pd.concat([df.reset_index(drop=True), pd.DataFrame(symp_data).reset_index(drop=True)], axis=1)
    df["disease_label"] = labels
    return df


# ════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("  MediPredict – Synthetic Data Generator")
    print("=" * 60)

    # 1. Load original data
    print(f"\n[1/4] Loading original dataset: '{INPUT_CSV}' ...")
    df_original = pd.read_csv(INPUT_CSV)
    print(f"      → {len(df_original):,} rows, {len(df_original.columns)} columns loaded.")

    # 2. Generate synthetic segments
    print("\n[2/4] Generating synthetic rows ...")

    print("      → Segment 1: Extreme Emergencies (300 rows) ...")
    df_emergencies = generate_extreme_emergencies(300)

    print("      → Segment 2: Perfectly Healthy   (300 rows) ...")
    df_healthy     = generate_perfectly_healthy(300)

    print("      → Segment 3: Borderline Cases     (400 rows) ...")
    df_borderline  = generate_borderline_cases(400)

    df_synthetic = pd.concat([df_emergencies, df_healthy, df_borderline], ignore_index=True)
    print(f"      → {len(df_synthetic):,} synthetic rows generated.")

    # 3. Validate column alignment before concat
    print("\n[3/4] Validating column alignment ...")
    original_cols   = list(df_original.columns)
    synthetic_cols  = list(df_synthetic.columns)

    missing_in_synth = [c for c in original_cols if c not in synthetic_cols]
    extra_in_synth   = [c for c in synthetic_cols if c not in original_cols]

    if missing_in_synth:
        print(f"      ⚠  Columns in original but missing in synthetic: {missing_in_synth}")
        for col in missing_in_synth:
            df_synthetic[col] = np.nan
    if extra_in_synth:
        print(f"      ⚠  Extra columns in synthetic (will be dropped): {extra_in_synth}")
        df_synthetic = df_synthetic[original_cols]

    # Re-order synthetic to match original column order exactly
    df_synthetic = df_synthetic[original_cols]
    print("      ✔  Columns aligned.")

    # 4. Concatenate and export
    print("\n[4/4] Concatenating and exporting ...")
    df_expanded = pd.concat([df_original, df_synthetic], ignore_index=True)
    df_expanded.to_csv(OUTPUT_CSV, index=False)
    print(f"      ✔  Saved '{OUTPUT_CSV}'")

    # ── Summary Report ──────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Original rows       : {len(df_original):>6,}")
    print(f"  Synthetic rows added: {len(df_synthetic):>6,}")
    print(f"  Total rows exported : {len(df_expanded):>6,}")
    print()
    print("  Synthetic label distribution:")
    counts = df_synthetic["disease_label"].value_counts()
    for label, count in counts.items():
        bar = "█" * (count // 10)
        print(f"    {label:<18} {count:>4}  {bar}")
    print()
    print("  Synthetic vital ranges (min → max):")
    for col in ["bp_systolic", "bp_diastolic", "sugar_level", "cholesterol", "heart_rate", "bmi", "age"]:
        mn = df_synthetic[col].min()
        mx = df_synthetic[col].max()
        print(f"    {col:<22} {mn:>7.1f}  →  {mx:.1f}")
    print("\n  Done. ✔")


if __name__ == "__main__":
    main()
