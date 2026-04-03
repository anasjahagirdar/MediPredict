import joblib # The scikit-learn standard
import sklearn
from sklearn.ensemble import RandomForestClassifier

# Path to your model
model_path = 'core/ml/model.pkl'

print(f"Attempting to load model from: {model_path}")

try:
    # Use joblib instead of pickle
    model = joblib.load(model_path)
    
    print("\n--- SUCCESS: MODEL LOADED ---")
    print("COPY THIS LIST EXACTLY:")
    
    if hasattr(model, 'feature_names_in_'):
        print(list(model.feature_names_in_))
    else:
        # If names aren't embedded, we will check the count
        print(f"Note: Names not found, but model expects {model.n_features_in_} features.")
        
    print("-----------------------------\n")

except ModuleNotFoundError:
    print("Error: 'joblib' is not installed in your venv.")
    print("Run: pip install joblib")
except Exception as e:
    print(f"Unexpected Error: {e}")