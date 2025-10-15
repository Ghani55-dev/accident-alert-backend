import pandas as pd
import numpy as np

# Number of samples
normal_samples = 150
accident_samples = 50

# Simulate normal driving data
normal_data = {
    "acc_x": np.random.uniform(-2, 2, normal_samples),
    "acc_y": np.random.uniform(-2, 2, normal_samples),
    "acc_z": np.random.uniform(-2, 2, normal_samples),
    "gyro_x": np.random.uniform(-10, 10, normal_samples),
    "gyro_y": np.random.uniform(-10, 10, normal_samples),
    "gyro_z": np.random.uniform(-10, 10, normal_samples),
    "label": [0] * normal_samples
}

# Simulate accident data (high sudden spikes)
accident_data = {
    "acc_x": np.random.uniform(-25, 25, accident_samples),
    "acc_y": np.random.uniform(-25, 25, accident_samples),
    "acc_z": np.random.uniform(-25, 25, accident_samples),
    "gyro_x": np.random.uniform(-200, 200, accident_samples),
    "gyro_y": np.random.uniform(-200, 200, accident_samples),
    "gyro_z": np.random.uniform(-200, 200, accident_samples),
    "label": [1] * accident_samples
}

# Combine both
df = pd.concat([pd.DataFrame(normal_data), pd.DataFrame(accident_data)], ignore_index=True)

# Shuffle the data
df = df.sample(frac=1).reset_index(drop=True)

# Save CSV
df.to_csv("sensor_data.csv", index=False)
print("✅ Dataset created successfully: sensor_data.csv")
print(df.head())
