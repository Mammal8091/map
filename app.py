import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import folium_static

# Title
st.title("Property Radius Search Tool")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv("property_data.csv")

df = load_data()

# User selects a property
selected_address = st.selectbox("Select a Subject Property", df['address'].unique())

# Radius input
radius = st.slider("Radius (in miles)", min_value=0, max_value=50, value=5)

# Get subject property coordinates
subject = df[df['address'] == selected_address].iloc[0]
subject_coords = (subject['latitude'], subject['longitude'])

# Find properties within radius
def is_within_radius(row):
    coords = (row['latitude'], row['longitude'])
    return geodesic(subject_coords, coords).miles <= radius

filtered_df = df[df.apply(is_within_radius, axis=1)].copy()

# Map display
m = folium.Map(location=subject_coords, zoom_start=13)
folium.Marker(subject_coords, tooltip="Subject Property", icon=folium.Icon(color="red")).add_to(m)

for _, row in filtered_df.iterrows():
    if row['address'] != selected_address:
        folium.Marker([row['latitude'], row['longitude']], tooltip=row['address']).add_to(m)

folium_static(m)

# Property selection
selected_props = st.multiselect("Select Properties from List Below", filtered_df['address'].tolist())

# Display selected
if selected_props:
    selected_df = filtered_df[filtered_df['address'].isin(selected_props)]
    st.dataframe(selected_df)
    st.download_button("Download Selected Properties", selected_df.to_csv(index=False), file_name="selected_properties.csv")
