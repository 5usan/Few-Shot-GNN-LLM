import os
import pandas as pd
import geopandas as gpd
from io import StringIO

US_regions = {
    "Northeast": ["Maine", "New Hampshire", "Vermont", "Massachusetts", "Rhode Island", "Connecticut", "New York", "New Jersey", "Pennsylvania"],
    "Midwest": ["Ohio", "Indiana", "Illinois", "Michigan", "Wisconsin", "Missouri", "North Dakota", "South Dakota", "Nebraska", "Kansas"],
    "South": ["Delaware", "Maryland", "Virginia", "West Virginia", "North Carolina", "South Carolina", "Georgia", "Florida", "Kentucky", "Tennessee", "Alabama", "Mississippi", "Arkansas", "Louisiana", "Oklahoma", "Texas"],
    "West": ["Montana", "Wyoming", "Colorado", "New Mexico", "Arizona", "Utah", "Idaho", "Nevada", "Washington", "Oregon", "California", "Alaska", "Hawaii"]
}

GEOTEXTDATA_PATH = os.path.join(os.getcwd(), 'data-related', 'GeoText.csv')

class GeoTextDataExtractor:
    def __init__(self):
        try:
            print("Instance Created")
            us_states = gpd.read_file(os.path.join('data-related', 'ne_110m_admin_1_states_provinces', 'ne_110m_admin_1_states_provinces.shp'))
            self.us_states = us_states[us_states['admin'] == "United States of America"]
            self.df = ''
            self.region_bounds_range = {
                "Northeast": self.get_region_lat_long_range("Northeast"),
                "Midwest": self.get_region_lat_long_range("Midwest"),
                "South": self.get_region_lat_long_range("South"),
                "West": self.get_region_lat_long_range("West"),
            }
            self.feature = []
            self.label = []
        except Exception as e:
            print("error", e)
    
    def get_region_lat_long_range(self, region_name):
        try:
            if region_name not in US_regions:
                print(f"Region '{region_name}' not found")
                return

            region_states = US_regions[region_name]
            region_bounds = {"lat_min": float('inf'), "lat_max": float('-inf'), "lon_min": float('inf'), "lon_max": float('-inf')}

            for state_name in region_states:
                state = self.us_states[self.us_states['name'] == state_name]

                if state.empty:
                    return

                minx, miny, maxx, maxy = state.geometry.bounds.iloc[0]

                # Update the region bounding box
                region_bounds["lat_min"] = min(region_bounds["lat_min"], miny)
                region_bounds["lat_max"] = max(region_bounds["lat_max"], maxy)
                region_bounds["lon_min"] = min(region_bounds["lon_min"], minx)
                region_bounds["lon_max"] = max(region_bounds["lon_max"], maxx)

            return region_bounds
        except Exception as e:
            print("error", e)

    def compute_region(self, coord):
        try:
            for region_name, bounding_range in self.region_bounds_range.items():
                latitude, longitude = coord
                lat_min = bounding_range['lat_min']
                lat_max = bounding_range['lat_max']
                lon_min = bounding_range['lon_min']
                lon_max = bounding_range['lon_max']

                if lat_min<=latitude<=lat_max and lon_min<=longitude<=lon_max:
                    return region_name
            return "Unknown"
        except Exception as e:
            print("error", e)
    
    def geo_text_data_extractor(self):
        try:
            with open(os.path.join(os.getcwd(), 'data-related', 'get-text-raw-data.txt'), "r", encoding="ISO-8859-1") as data_source:
                first_raw_data = data_source.readline()
                self.df = pd.read_csv(StringIO(first_raw_data), sep="\t", header=None, names=["User ID", "Timestamp","Location", "Latitude", "Longitude", "Tweet Content"])
                self.compute_region((self.df["Latitude"][0], self.df["Longitude"][0]))
                raw_data = data_source.read()
                self.df = pd.read_csv(StringIO(raw_data), sep="\t", header=None, names=["User ID", "Timestamp","Location", "Latitude", "Longitude", "Tweet Content"])
                self.df["Location"] = self.df.apply(lambda row: self.compute_region((row["Latitude"], row["Longitude"])), axis = 1)
                self.df.to_csv(GEOTEXTDATA_PATH, index=False)
        except Exception as e:
            self.df.to_csv('output.csv', index=False)
            print("error", e)

    def preprocess_data(self):
        geotext_data = pd.read_csv(GEOTEXTDATA_PATH)
        geotext_data = geotext_data.dropna()
        geotext_data = geotext_data[geotext_data['Location'] != "Unknown"]
        geotext_data = geotext_data
        self.feature = geotext_data["Tweet Content"]
        self.label = geotext_data['Location']
        return {
            "feature": self.feature,
            "label": self.label
        }

GeoTextDataExtractorInstance = GeoTextDataExtractor()
GeoTextDataExtractorInstance.preprocess_data()

