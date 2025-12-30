import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

def train_maternal_risk_model():
    # Dummy training data
    X = np.random.rand(100, 5)  # age, bmi, bp, hb, sugar
    y = np.random.randint(0, 2, 100)  # 0: low risk, 1: high risk
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = RandomForestClassifier()
    model.fit(X_scaled, y)
    
    # Save model and scaler
    with open('models/maternal_risk_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    with open('models/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    return model, scaler

def load_models():
    try:
        with open('models/maternal_risk_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('models/scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        return model, scaler
    except FileNotFoundError:
        return None, None
