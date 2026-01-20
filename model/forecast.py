import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor

# Generate synthetic energy data
np.random.seed(42)
days = np.arange(1, 366)
energy = 200 + days * 0.5 + np.random.normal(0, 10, size=len(days))

# Inject anomalies (simulating power theft / faults)
anomaly_days = np.random.choice(days, size=8, replace=False)
energy[anomaly_days - 1] += np.random.choice([80, -60], size=8)

data = pd.DataFrame({
    "day": days,
    "energy": energy
})

# Train model
X = data[["day"]]
y = data["energy"]
model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X, y)

# Predict
data["predicted"] = model.predict(X)
data["error"] = abs(data["energy"] - data["predicted"])

# Detect anomalies
threshold = data["error"].mean() + 2 * data["error"].std()
anomalies = data[data["error"] > threshold]

# Plot
plt.figure()
plt.plot(data["day"], data["energy"], label="Energy Usage")
plt.plot(data["day"], data["predicted"], label="Predicted")
plt.scatter(anomalies["day"], anomalies["energy"], label="Anomaly")
plt.xlabel("Day")
plt.ylabel("Energy Consumption")
plt.legend()
plt.show()
