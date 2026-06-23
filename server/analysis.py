import geopandas as gpd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score 

# Load layers
parcels = gpd.read_file("data/parcel.geojson")
roads = gpd.read_file("data/roads.geojson")
water = gpd.read_file("data/water_network.geojson")
landuse = gpd.read_file("data/landuse.geojson")
schools = gpd.read_file("data/schools.geojson")
tourism = gpd.read_file("data/tourism.geojson")

# Reproject all layers to the parcels CRS
roads = roads.to_crs(parcels.crs)
water = water.to_crs(parcels.crs)
landuse = landuse.to_crs(parcels.crs)
schools = schools.to_crs(parcels.crs)
tourism = tourism.to_crs(parcels.crs)

print(parcels.crs)

parcels["area"] = parcels.geometry.area 
parcels["perimeter"] = parcels.geometry.length 
    parcels["compactness"] = ( 
    parcels["area"] / 
    (parcels["perimeter"] ** 2) 
) 

parcels["centroid"] = parcels.geometry.centroid 

# distance to roads 
parcels["dist_to_road"] = parcels["centroid"].apply( 
    lambda p: roads.distance(p).min() 
)

# distance to water 
parcels["dist_to_water"] = parcels["centroid"].apply( 
    lambda p: water.distance(p).min() 
) 

# distance to schools 
parcels["dist_to_school"] = parcels["centroid"].apply( 
    lambda p: schools.distance(p).min() 
) 

# distance to tourism 
parcels["dist_to_tourism"] = parcels["centroid"].apply( 
    lambda p: tourism.distance(p).min() 
) 

# spatial join with land use 
parcels_landuse = gpd.sjoin( 
    parcels, 
    landuse[["Name", "geometry"]], 
    how="left", 
    predicate="intersects" 
) 

# encode land use categories 
parcels_landuse["landuse_code"] = ( 
    parcels_landuse["Name"] 
    .astype("category") 
    .cat.codes 
) 

# print unique land use categories and their codes 
print( 
    parcels_landuse[ 
        ["Name", "landuse_code"] 
] 
    .drop_duplicates() 
    .sort_values("landuse_code") 
)   

# encode target variable (land use class) 
parcels_landuse["target_code"] = ( 
    parcels_landuse["ASS_CLASSI"] 
    .astype("category") 
    .cat.codes 
) 

features = [ 
    "area", 
    "perimeter", 
    "compactness", 
    "dist_to_road", 
    "dist_to_water", 
    "dist_to_school", 
    "dist_to_tourism", 
    "landuse_code" 
] 

data = parcels_landuse.dropna( 
    subset=features + ["target_code"] 
) 

X = data[features] 
y = data["target_code"]

X_train, X_test, y_train, y_test = train_test_split( 
    X, 
    y, 
    test_size=0.30, 
    random_state=42 
) 

model = RandomForestClassifier( 
    n_estimators=100, 
    random_state=42 
) 
model.fit(X_train, y_train)

# generate predictions 
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("Accuracy:", accuracy) 

