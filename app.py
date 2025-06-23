import streamlit as st
import pandas as pd
import folium
import json
from folium.plugins import LocateControl
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

# Page settings and light CSS
st.set_page_config(page_title="🌿 Nursery Locator-KHARIAR FOREST DIVISION", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f4f9f4; }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🌳 KHARIAR Forest Division – Public Nursery Locator")
st.markdown("Use this map to find public nurseries, check available species, and get in touch with incharges.")

# Session state for user location
if "user_location" not in st.session_state:
    st.session_state.user_location = None

# Load Excel data
excel_path = "NURSARYDETAILS_CLEANED.xlsx"
try:
    df = pd.read_excel(excel_path)
except FileNotFoundError:
    st.error(f"❌ File not found: {excel_path}")
    st.stop()

# Clean and standardize column names
df.rename(columns={"Latitide": "Latitude"}, inplace=True)
df.columns = df.columns.str.strip()
required_cols = ['Nursery Name', 'Latitude', 'Longitude', 'Name of the Incharge', 'Contact', 'NAME OF SPECIES']
if not all(col in df.columns for col in required_cols):
    st.error("❌ Excel must include: " + ", ".join(required_cols))
    st.stop()

df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude'])

# Detect location only once
if st.session_state.user_location is None:
    loc = streamlit_js_eval(
        js_expressions="navigator.geolocation.getCurrentPosition((pos) => pos.coords)",
        key="get_user_location"
    )
    if loc and "latitude" in loc and "longitude" in loc:
        st.session_state.user_location = (loc["latitude"], loc["longitude"])
        st.success("📍 Your location has been detected.")
    else:
        st.session_state.user_location = ( 20.302500,  82.755278)
        st.warning("⚠️ Using default location: Khariar Forest Division.")

# Sidebar controls
st.sidebar.header("🧭 Map Controls")
zoom_level = st.sidebar.slider("Zoom Level", min_value=6, max_value=18, value=11)

# Create map
m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=zoom_level)
LocateControl(auto_start=True).add_to(m)

# Optional GeoJSON
try:
    with open("khariar_boundary.geojson", "r") as f:
        khariar_boundary = json.load(f)
    folium.GeoJson(
        khariar_boundary,
        name="Khariar Forest Boundary",
        style_function=lambda x: {
            "fillColor": "#228B22",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.1,
        },
    ).add_to(m)
except:
    pass

# Show user marker
folium.Marker(
    location=st.session_state.user_location,
    tooltip="📍 You are here",
    icon=folium.Icon(color="blue", icon="user")
).add_to(m)

# Add nursery markers
for _, row in df.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        tooltip=row['Nursery Name'],
        popup=f"""
        <b>{row['Nursery Name']}</b><br>
        👤 <b>Incharge:</b> {row['Name of the Incharge']}<br>
        📞 <b>Contact:</b> {row['Contact']}<br>
        🌱 <b>Species:</b> {row['NAME OF SPECIES']}
        """,
        icon=folium.Icon(color="green", icon="leaf")
    ).add_to(m)

# Display map
st.subheader("🗺️ Interactive Nursery Map")
with st.container():
    map_data = st_folium(m, width=1000, height=600)

# Display clicked nursery
if map_data and map_data.get("last_object_clicked_tooltip"):
    name = map_data["last_object_clicked_tooltip"]
    row = df[df["Nursery Name"] == name].iloc[0]
    st.markdown(f"## 🏡 {name} – Nursery Details")
    st.markdown(f"""
    **👤 Incharge:** {row['Name of the Incharge']}  
    **📞 Contact:** {row['Contact']}  
    """)
    st.markdown("### 🌿 Available Species")
    species = [s.strip() for s in str(row['NAME OF SPECIES']).split(",")]
    st.success(", ".join(species))
else:
    st.info("🔍 Click on a nursery marker on the map to view its details.")
