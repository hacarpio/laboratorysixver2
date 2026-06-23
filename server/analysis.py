import geopandas as gpd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

# =========================
# LOAD DATA
# =========================
parcels = gpd.read_file("data/parcel.geojson")
roads = gpd.read_file("data/roads.geojson")
water = gpd.read_file("data/water_network.geojson")
landuse = gpd.read_file("data/landuse.geojson")
schools = gpd.read_file("data/schools.geojson")
tourism = gpd.read_file("data/tourism.geojson")

# =========================
# CRS ALIGNMENT
# =========================
parcels = parcels.to_crs(epsg=32651)
roads = roads.to_crs(parcels.crs)
water = water.to_crs(parcels.crs)
landuse = landuse.to_crs(parcels.crs)
schools = schools.to_crs(parcels.crs)
tourism = tourism.to_crs(parcels.crs)

# =========================
# GEOMETRY FEATURES
# =========================
parcels["area"] = parcels.geometry.area
parcels["perimeter"] = parcels.geometry.length
parcels["compactness"] = parcels["area"] / (parcels["perimeter"] ** 2)

parcels["centroid"] = parcels.geometry.centroid

# =========================
# DISTANCE FEATURES
# =========================
parcels["dist_to_road"] = parcels.centroid.apply(lambda p: roads.distance(p).min())
parcels["dist_to_water"] = parcels.centroid.apply(lambda p: water.distance(p).min())
parcels["dist_to_school"] = parcels.centroid.apply(lambda p: schools.distance(p).min())
parcels["dist_to_tourism"] = parcels.centroid.apply(lambda p: tourism.distance(p).min())

# =========================
# NEW SPATIAL FEATURES
# =========================

# neighbor density
parcels["neighbor_density"] = parcels.geometry.apply(
    lambda x: parcels.geometry.intersects(x.buffer(100)).sum()
)

# schools within 500m
parcels["schools_500m"] = parcels.centroid.apply(
    lambda p: (schools.distance(p) <= 500).sum()
)

# tourism within 500m
parcels["tourism_500m"] = parcels.centroid.apply(
    lambda p: (tourism.distance(p) <= 500).sum()
)

# =========================
# LAND USE JOIN
# =========================
parcels_landuse = gpd.sjoin(
    parcels,
    landuse[["Name", "geometry"]],
    how="left",
    predicate="intersects"
)

parcels_landuse["landuse_code"] = parcels_landuse["Name"].astype("category").cat.codes
parcels_landuse["target_code"] = parcels_landuse["ASS_CLASSI"].astype("category").cat.codes

# =========================
# FEATURES LIST
# =========================
features = [
    "area",
    "perimeter",
    "compactness",
    "dist_to_road",
    "dist_to_water",
    "dist_to_school",
    "dist_to_tourism",
    "landuse_code",
    "neighbor_density",
    "schools_500m",
    "tourism_500m"
]

data = parcels_landuse.dropna(subset=features + ["target_code"])

X = data[features]
y = data["target_code"]

# =========================
# TRAIN TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# =========================
# MODEL 1: RANDOM FOREST
# =========================
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_pred = rf.predict(X_test)
rf_acc = accuracy_score(y_test, rf_pred)

# =========================
# MODEL 2: KNN
# =========================
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train, y_train)
knn_pred = knn.predict(X_test)
knn_acc = accuracy_score(y_test, knn_pred)

# =========================
# RESULTS
# =========================
print("\nMODEL PERFORMANCE")
print("Random Forest Accuracy:", rf_acc)
print("KNN Accuracy:", knn_acc)

print("\nBest Model:",
      "Random Forest" if rf_acc > knn_acc else "KNN")