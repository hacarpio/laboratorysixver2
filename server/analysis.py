import geopandas as gpd

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

