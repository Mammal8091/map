import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import folium_static

@st.cache_data
def load_data():
    df = pd.read_csv("property_data_geocoded.csv")
    df.columns = df.columns.str.strip().str.lower()
    return df

df = load_data()

property_id = st.number_input("Enter Property ID", step=1)
radius_miles = st.slider("Radius (in miles)", min_value=1, max_value=25, value=5)

subject = df[df["property_id"] == property_id]
if subject.empty:
    st.warning("Property ID not found.")
    st.stop()

subject = subject.iloc[0]
subject_coords = (subject["latitude"], subject["longitude"])

# Bounding box filter
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

# Map
m = folium.Map(location=subject_coords, zoom_start=12)

# Subject marker
folium.Marker(subject_coords,
              tooltip=f"Subject: {subject['property_name_text']}",
              popup=subject["address_line1_text"],
              icon=folium.Icon(color="red")).add_to(m)

# Comp markers with detailed popup
for _, row in comps.iterrows():
    popup_content = f"""
    <b>{row['property_name_text']}</b><br>
    {row['address_line1_text']}<br>
    {row['city_name_text']}, {row['state_code']} {row['zip_code']}<br>
    Units: {row['property_total_unit_count']}<br>
    Owner: {row['owner_contact_email_text']}<br>
    Manager: {row['mgmt_contact_email_text']}<br>
    Lat/Lon: ({row['latitude']}, {row['longitude']})
    """
    folium.Marker(
        [row["latitude"], row["longitude"]],
        tooltip=row["property_name_text"],
        popup=folium.Popup(popup_content, max_width=300),
        icon=folium.Icon(color="blue")
    ).add_to(m)

folium_static(m)

# Dropdown (sorted)
select_addresses = st.multiselect(
    "Select Properties",
    sorted(comps["property_name_text"].tolist())
)
selected = comps[comps["property_name_text"].isin(select_addresses)]

# Display + CSV + Clipboard
if not selected.empty:
    st.dataframe(selected)

    # Clipboard-friendly output
    property_ids = selected["property_id"].astype(str).tolist()
    clipboard_string = ", ".join(property_ids)
    st.code(clipboard_string, language="text")
    st.caption("⬆️ Copy above Property IDs (automatically selectable)")

    st.download_button(
        "Download Selected as CSV",
        selected.to_csv(index=False),
        file_name="selected_properties.csv"
    )
