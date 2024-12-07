import streamlit as st
import folium
import json
from streamlit_folium import st_folium
from folium import Marker, Popup, Icon
from pathlib import Path

# Tag-to-color mapping
color_dict = {'nick': 'red','urciuoli':'gray','finazzo':'lightblue','morgan':'pink', 'history': 'green', 'food': 'orange', 'trips': 'purple'}


# Set up the Streamlit app
st.set_page_config(page_title="Interactive World Map", layout="wide")
st.title("🌎")

# Define file path for JSON storage
DATA_FILE = Path("data/pins_data.json")

# Load existing data from file into session state
if "map_data" not in st.session_state:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            st.session_state["map_data"] = json.load(f)
    else:
        st.session_state["map_data"] = []

# Save data to file function
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state["map_data"], f, indent=4)

# Sidebar for pin management
st.sidebar.title("📌")
# Tag filter
all_tags = sorted({tag for pin in st.session_state["map_data"] for tag in pin.get("tags", [])})
selected_tags = st.sidebar.multiselect(
    "Filter by Tags", options=all_tags, default=all_tags, help="Select tags to filter displayed pins"
)

# Filtered map data based on selected tags
filtered_map_data = [
    pin for pin in st.session_state["map_data"]
    if not selected_tags or any(tag in selected_tags for tag in pin.get("tags", []))
]

# Edit Pin Dialog
@st.dialog("Edit Pin", width="large")
def edit_pin_dialog(idx):
    pin = st.session_state["map_data"][idx]
    title = st.text_input("Edit Title", value=pin["title"])
    note = st.text_area("Edit Note", value=pin["note"])
    updated_tags = st.multiselect(
        "Edit Tags", options=color_dict.keys(), default=pin["tags"]
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes", key=f"save_{idx}"):
            # Update pin in session state
            pin["title"] = title
            pin["note"] = note
            pin["tags"] = updated_tags
            pin["color"] = color_dict[updated_tags[0]] if updated_tags else "blue"
            save_data()
            st.rerun()
    with col2:
        if st.button("Cancel", key=f"cancel_{idx}"):
            st.rerun()

# Sidebar pin display with Edit and Delete
for idx, pin in enumerate(filtered_map_data):
    with st.sidebar.container():
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write(f"**{pin['title']}**: {pin['location'][0]:.5f}, {pin['location'][1]:.5f}")
        with col2:
            if st.button("✏️", key=f"edit_btn_{idx}"):  # Edit button
                edit_pin_dialog(idx)
        with col3:
            if st.button("🗑️", key=f"delete_btn_{idx}"):  # Delete button
                st.session_state["map_data"].remove(pin)
                save_data()
                st.rerun()

# Define the map
m = folium.Map(location=[0, 0], zoom_start=2, tiles="cartodbdark_matter", height="80vh",attr='🗺️',min_zoom=2)

# Add filtered pins to the map
for data in filtered_map_data:
    Marker(
        location=data["location"],
        popup=Popup(f"{data['title']}", max_width=300),
        icon=Icon(color=data.get("color", "blue")),
    ).add_to(m)

# Render the map in Streamlit
map_output = st_folium(m, width=1800, height=800)

# Add Pin Dialog
@st.dialog("Add Pin", width="large")
def add_pin_dialog(location):
    lat, lon = location
    st.write(f"**Selected Location:** {lat:.5f}, {lon:.5f}")
    title = st.text_input("Title:", placeholder="Enter a title for this pin")
    note = st.text_area("Note:", placeholder="Enter a note for this pin")
    tags = st.multiselect("Tags:", options=color_dict.keys(), placeholder="Select tags")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Pin"):
            if title.strip():
                # Save pin data to session state
                st.session_state["map_data"].append(
                    {
                        "title": title.strip(),
                        "location": [lat, lon],
                        "note": note.strip(),
                        "tags": tags,
                        "color": color_dict[tags[0]] if tags else "blue",
                    }
                )
                save_data()
                st.rerun()
            else:
                st.warning("Please enter a title before adding the pin.")
    with col2:
        if st.button("Cancel"):
            st.rerun()

# Handle map clicks to open the dialog
if map_output and "last_clicked" in map_output and map_output["last_clicked"]:
    lat, lon = map_output["last_clicked"]["lat"], map_output["last_clicked"]["lng"]
    add_pin_dialog((lat, lon))
