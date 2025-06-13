import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import folium_static

# Load full dataset
@st.cache_data
def load_data():
    df = pd.read_csv("property_data.csv")
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()

# Input property_id
property_id = st.number_input("Enter Property ID", step=1)

# Radius selection
radius_miles = st.slider("Radius (in miles)", min_value=1, max_value=25, value=5)

# Filter by property_id
subject = df[df["property_id"] == property_id]
if subject.empty:
    st.warning("Property ID not found.")
    st.stop()

subject = subject.iloc[0]
subject_coords = (subject["latitude"], subject["longitude"])

# Bounding box filter for faster performance
lat_min = subject["latitude"] - 0.075
lat_max = subject["latitude"] + 0.075
lon_min = subject["longitude"] - 0.075
lon_max = subject["longitude"] + 0.075

subset_df = df[
    (df["latitude"].between(lat_min, lat_max)) &
    (df["longitude"].between(lon_min, lon_max))
].copy()

# Geodesic filter
def is_within_radius(row):
    return geodesic(subject_coords, (row["latitude"], row["longitude"])).miles <= radius_miles

comps = subset_df[subset_df.apply(is_within_radius, axis=1)]
comps = comps[comps["property_id"] != property_id]

# Map display
m = folium.Map(location=subject_coords, zoom_start=12)
# Subject marker in red
folium.Marker(
    subject_coords,
    tooltip=f"Subject: {subject['property_name_text']}",
    icon=folium.Icon(color="red")
).add_to(m)

# Comp markers in blue
for _, row in comps.iterrows():
    folium.Marker(
        [row["latitude"], row["longitude"]],
        tooltip=row["property_name_text"],
        icon=folium.Icon(color="blue")
    ).add_to(m)

folium_static(m)

# Multiselect output
select_addresses = st.multiselect("Select Properties", comps["property_name_text"].tolist())
selected = comps[comps["property_name_text"].isin(select_addresses)]

# Display + Download
if not selected.empty:
    st.dataframe(selected)
    st.download_button("Download Selected as CSV", selected.to_csv(index=False), file_name="selected_properties.csv")
