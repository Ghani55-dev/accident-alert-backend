import joblib
import numpy as np
import os

# Load model (ensure path is correct)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "accident_model.pkl")
model = joblib.load(MODEL_PATH)

def predict_accident(sensor_data):
    """
    sensor_data: dict with keys acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z
    """
    features = np.array([[sensor_data['acc_x'], sensor_data['acc_y'], sensor_data['acc_z'],
                          sensor_data['gyro_x'], sensor_data['gyro_y'], sensor_data['gyro_z']]])
    pred = model.predict(features)[0]
    severity = "high" if pred == 1 else "low"
    return severity
