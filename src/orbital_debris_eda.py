"""
Orbital Debris Population Structure from Public GP Catalog Data

Plain-Python export of the accompanying Jupyter notebook.
The notebook is the primary project artifact.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm, probplot
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# ------------------------------------------------------------------------
urls = {
    "FENGYUN 1C ASAT Debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=fengyun-1c-debris&FORMAT=csv",
    "IRIDIUM 33 Debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-33-debris&FORMAT=csv",
    "COSMOS 2251 Debris": "https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=csv"
}

frames = []

for event_name, url in urls.items():
    df_event = pd.read_csv(url)
    df_event["debris_event"] = event_name
    frames.append(df_event)

debris_raw = pd.concat(frames, ignore_index=True)

print(debris_raw.shape)
debris_raw.head()

# ------------------------------------------------------------------------
# Constants
MU_EARTH = 398600.4418      # km^3/s^2
R_EARTH = 6378.137          # km

debris = debris_raw.copy()

# Standardize useful columns
debris["mean_motion_rev_per_day"] = pd.to_numeric(debris["MEAN_MOTION"], errors="coerce")
debris["inclination_deg"] = pd.to_numeric(debris["INCLINATION"], errors="coerce")
debris["eccentricity"] = pd.to_numeric(debris["ECCENTRICITY"], errors="coerce")

# Orbital period from mean motion
debris["period_min"] = 1440 / debris["mean_motion_rev_per_day"]

# Convert mean motion to semi-major axis
# mean motion n in rad/s
debris["mean_motion_rad_s"] = debris["mean_motion_rev_per_day"] * 2 * np.pi / 86400
debris["semi_major_axis_km"] = (MU_EARTH / debris["mean_motion_rad_s"]**2)**(1/3)

# Approximate mean altitude
debris["altitude_km"] = debris["semi_major_axis_km"] - R_EARTH

# Clean physically usable rows
debris = debris.dropna(subset=["altitude_km", "inclination_deg", "period_min", "eccentricity"])

# Optional: focus on Earth-orbit values that are plausible for this quick EDA
debris = debris[(debris["altitude_km"] > 100) & (debris["altitude_km"] < 40000)]

print(debris.shape)
debris[["OBJECT_NAME", "debris_event", "inclination_deg", "altitude_km", "period_min", "eccentricity"]].head()

# ------------------------------------------------------------------------
summary = debris[["inclination_deg", "altitude_km", "period_min", "eccentricity"]].describe()
summary

# ------------------------------------------------------------------------
def coefficient_of_variation(x):
    return x.std() / x.mean()

stats_table = pd.DataFrame({
    "mean": debris[["inclination_deg", "altitude_km"]].mean(),
    "median": debris[["inclination_deg", "altitude_km"]].median(),
    "std": debris[["inclination_deg", "altitude_km"]].std(),
    "iqr": debris[["inclination_deg", "altitude_km"]].quantile(0.75) - debris[["inclination_deg", "altitude_km"]].quantile(0.25),
    "cv": debris[["inclination_deg", "altitude_km"]].apply(coefficient_of_variation)
})

stats_table

# ------------------------------------------------------------------------
covariance = debris["inclination_deg"].cov(debris["altitude_km"])
correlation = debris["inclination_deg"].corr(debris["altitude_km"])

print(f"Covariance: {covariance:.3f} deg*km")
print(f"Correlation coefficient: {correlation:.3f}")

# ------------------------------------------------------------------------
plt.figure(figsize=(8, 5))
plt.hist(debris["altitude_km"], bins=40, edgecolor="black", alpha=0.7)
plt.xlabel("Approximate Mean Altitude (km)")
plt.ylabel("Frequency")
plt.title("Distribution of Approximate Mean Altitude for Cataloged Debris")
plt.grid(alpha=0.3)
plt.show()

# ------------------------------------------------------------------------
plt.figure(figsize=(10, 5))
debris.boxplot(column="altitude_km", by="debris_event", rot=20)
plt.title("Approximate Mean Altitude by Debris Event")
plt.suptitle("")
plt.xlabel("Debris Event")
plt.ylabel("Approximate Mean Altitude (km)")
plt.grid(alpha=0.3)
plt.show()

# ------------------------------------------------------------------------
plt.figure(figsize=(8, 5))

for event_name in debris["debris_event"].unique():
    subset = debris[debris["debris_event"] == event_name]
    plt.scatter(
        subset["inclination_deg"],
        subset["altitude_km"],
        alpha=0.5,
        s=20,
        label=event_name
    )

plt.xlabel("Inclination (degrees)")
plt.ylabel("Approximate Mean Altitude (km)")
plt.title("Debris Altitude vs. Inclination by Event")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# ------------------------------------------------------------------------
plt.figure(figsize=(8, 5))
plt.scatter(debris["altitude_km"], debris["period_min"], alpha=0.5, s=20)
plt.xlabel("Approximate Mean Altitude (km)")
plt.ylabel("Orbital Period (minutes)")
plt.title("Orbital Period vs. Approximate Mean Altitude")
plt.grid(alpha=0.3)
plt.show()

# ------------------------------------------------------------------------
altitude = debris["altitude_km"]

mu_alt = altitude.mean()
sigma_alt = altitude.std()

x = np.linspace(altitude.min(), altitude.max(), 500)
normal_pdf = norm.pdf(x, mu_alt, sigma_alt)

plt.figure(figsize=(8, 5))
plt.hist(altitude, bins=40, density=True, edgecolor="black", alpha=0.7, label="Altitude Data")
plt.plot(x, normal_pdf, linewidth=2, label=f"Normal fit ($\\mu$={mu_alt:.1f}, $\\sigma$={sigma_alt:.1f})")
plt.xlabel("Approximate Mean Altitude (km)")
plt.ylabel("Density")
plt.title("Density Histogram of Debris Altitude with Fitted Normal Distribution")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# ------------------------------------------------------------------------
plt.figure(figsize=(6, 6))
probplot(altitude, dist="norm", plot=plt)
plt.title("Q-Q Plot of Debris Altitude vs. Normal Distribution")
plt.grid(alpha=0.3)
plt.show()

# ------------------------------------------------------------------------
np.random.seed(93)

sample = altitude.sample(n=10, random_state=93)
bootstrap_means = []

for _ in range(5000):
    boot_sample = sample.sample(n=10, replace=True)
    bootstrap_means.append(boot_sample.mean())

bootstrap_means = np.array(bootstrap_means)

ci_lower = np.percentile(bootstrap_means, 2.5)
ci_upper = np.percentile(bootstrap_means, 97.5)

print("Sample values:")
print(sample.values)

print(f"Population mean altitude: {altitude.mean():.2f} km")
print(f"Sample mean altitude: {sample.mean():.2f} km")
print(f"95% bootstrap CI: ({ci_lower:.2f}, {ci_upper:.2f}) km")

# ------------------------------------------------------------------------
X = debris[["inclination_deg"]]
y = debris["altitude_km"]

model = LinearRegression()
model.fit(X, y)

predicted_altitude = model.predict(X)
residuals = y - predicted_altitude

r_squared = r2_score(y, predicted_altitude)

print(f"Intercept: {model.intercept_:.3f} km")
print(f"Slope: {model.coef_[0]:.3f} km per degree")
print(f"R-squared: {r_squared:.4f}")

# ------------------------------------------------------------------------
plt.figure(figsize=(8, 5))
plt.scatter(debris["inclination_deg"], debris["altitude_km"], alpha=0.5, s=20)
plt.plot(debris["inclination_deg"], predicted_altitude, linewidth=2)
plt.xlabel("Inclination (degrees)")
plt.ylabel("Approximate Mean Altitude (km)")
plt.title("Linear Regression: Debris Altitude Predicted by Inclination")
plt.grid(alpha=0.3)
plt.show()

# ------------------------------------------------------------------------
plt.figure(figsize=(8, 5))
plt.scatter(predicted_altitude, residuals, alpha=0.5, s=20)
plt.axhline(0, linestyle="--", linewidth=2)
plt.xlabel("Predicted Altitude (km)")
plt.ylabel("Residuals (km)")
plt.title("Residual Plot for Linear Regression Model")
plt.grid(alpha=0.3)
plt.show()

# ------------------------------------------------------------------------
event_encoded = pd.get_dummies(debris["debris_event"], drop_first=True)

X_event = pd.concat([debris[["inclination_deg"]], event_encoded], axis=1)
y = debris["altitude_km"]

event_model = LinearRegression()
event_model.fit(X_event, y)

event_predictions = event_model.predict(X_event)
event_r_squared = r2_score(y, event_predictions)

print(f"Raw inclination-only model R-squared: {r_squared:.4f}")
print(f"Inclination + debris event model R-squared: {event_r_squared:.4f}")