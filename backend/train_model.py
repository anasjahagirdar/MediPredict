import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

def train_health_model():
    # 1. Load the dataset
    data_path = 'training_data.csv' # Ensure this file is in your backend folder
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found!")
        return

    df = pd.read_csv(data_path)

    # 2. Define Features (X) and Target (y)
    # These must match the columns in your CSV exactly
    feature_cols = [
        'bp_systolic', 'bp_diastolic', 'sugar_level', 'cholesterol', 
        'heart_rate', 'bmi', 'age', 'gender', 'symptom_fever', 
        'symptom_cough', 'symptom_fatigue', 'symptom_headache', 
        'symptom_chest_pain', 'symptom_breathlessness', 
        'symptom_sweating', 'symptom_nausea'
    ]
    
    X = df[feature_cols]
    y = df['disease_label']

    # 3. Split into Training and Testing sets (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Initialize and Train the Random Forest
    print("Training the Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate the model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nModel Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 6. Save the model for Django to use
    model_filename = 'core/ml/model.pkl'
    os.makedirs('core/ml', exist_ok=True)
    joblib.dump(model, model_filename)
    print(f"\nSuccess! Model saved to {model_filename}")

if __name__ == "__main__":
    train_health_model()