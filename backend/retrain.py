import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# 1. Load the augmented dataset
df = pd.read_csv('training_data_augmented.csv')

# 2. Match the exact FEATURE_ORDER from views.py
FEATURES = [
    'age', 'bmi', 'bp_systolic', 'bp_diastolic', 'sugar_level', 
    'cholesterol', 'heart_rate', 'gender', 'symptom_fever', 
    'symptom_cough', 'symptom_fatigue', 'symptom_headache', 
    'symptom_chest_pain', 'symptom_breathlessness', 
    'symptom_sweating', 'symptom_nausea'
]

X = df[FEATURES]
# Using the exact target column name from your uploaded CSV
y = df['disease_label'] 

# 3. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Train the "Forest"
print("Planting the Random Forest... Please wait...")
model = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)
model.fit(X_train, y_train)

# 5. Evaluate
y_pred = model.predict(X_test)
print("\n--- Training Complete ---")
print(f"New Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%\n")
print(classification_report(y_test, y_pred))

# 6. Save the new model to your Django ML folder
import os

# Since you are running this from the 'backend' folder, the path is just 'core/ml/...'
model_dir = os.path.join('core', 'ml')
model_path = os.path.join(model_dir, 'model.pkl')

# This guarantees the folder exists before trying to save!
os.makedirs(model_dir, exist_ok=True)

joblib.dump(model, model_path)
print(f"Success! New AI Brain saved to: {model_path}")