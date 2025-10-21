import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.neighbors import NearestNeighbors
import folium
from streamlit_folium import st_folium
import os
import altair as alt

# --- App Configuration ---
st.set_page_config(
    page_title="Delhi Green Space Analysis",
    page_icon="🌳",
    layout="wide"
)

st.title("Urban Green Space & Park Accessibility in Delhi")

# --- Data Loading Functions ---
@st.cache_data
def load_cleaned_data(filepath):
    try:
        df = pd.read_csv(filepath)
        df = df[['name', 'category', 'lat', 'lon']].dropna(subset=['lat', 'lon']).copy()
        df.reset_index(drop=True, inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Error: Make sure '{filepath}' is available in the root folder.")
        return None

def create_nn_model(data):
    if data is None or data.empty:
        return None
    coords = np.radians(data[['lat', 'lon']].values)
    nn_model = NearestNeighbors(n_neighbors=5, algorithm='ball_tree', metric='haversine')
    nn_model.fit(coords)
    return nn_model

# --- Create Tabs for Different Analyses ---
tab1, tab2, tab3, tab4 = st.tabs(["🔍 Park Proximity Finder", "🗺️ LULC Analysis", "🌿 NDVI Analysis", "🦋 Biodiversity Analysis"])


# --- TAB 1: Park Proximity Finder ---
with tab1:
    st.header("🌳 Interactive Green Space Finder for Delhi")
    
    greenspaces_df = load_cleaned_data('Team_07_CleanedData.csv')
    
    if greenspaces_df is not None:
        st.sidebar.header("Search Options")
        search_option = st.sidebar.selectbox(
            "What do you want to find?",
            ("All Green Spaces", "Parks & Gardens Only")
        )
        st.markdown(f"Click anywhere on the map to find the 5 nearest **{search_option}**.")

        if search_option == "Parks & Gardens Only":
            filtered_df = greenspaces_df[greenspaces_df['category'] == 'Park/Garden'].reset_index(drop=True)
        else:
            filtered_df = greenspaces_df

        nn_model = create_nn_model(filtered_df)

        if nn_model is None:
            st.warning("No 'Parks & Gardens' found in the dataset to search.")
        else:
            map_center = [28.6139, 77.2090]
            m = folium.Map(location=map_center, zoom_start=11)
            st_data = st_folium(m, center=map_center, zoom=11, width=1200, height=600)

            if st_data and st_data.get('last_clicked'):
                clicked_lat, clicked_lon = st_data['last_clicked']['lat'], st_data['last_clicked']['lng']
                clicked_coords_rad = np.radians([[clicked_lat, clicked_lon]])
                distances, indices = nn_model.kneighbors(clicked_coords_rad)
                nearest_locations = filtered_df.iloc[indices[0]]

                st.subheader(f"🔍 Top 5 Nearest {search_option}")
                st.dataframe(nearest_locations)

                result_map = folium.Map(location=[clicked_lat, clicked_lon], zoom_start=14)
                folium.Marker([clicked_lat, clicked_lon], popup="Your Location", icon=folium.Icon(color='blue', icon='user')).add_to(result_map)

                for _, row in nearest_locations.iterrows():
                    loc = [row['lat'], row['lon']]
                    folium.Marker(loc, popup=f"<b>{row['name']}</b>", tooltip=row['name'], icon=folium.Icon(color='green', icon='tree-conifer', prefix='fa')).add_to(result_map)
                    folium.PolyLine(locations=[[clicked_lat, clicked_lon], loc], color='red').add_to(result_map)

                st.subheader("🗺️ Map of Nearest Locations")
                st_folium(result_map, width=1200, height=600)


# --- TAB 2: Land Use / Land Cover (LULC) Analysis (LAYOUT CORRECTED) ---
with tab2:
    st.header("Land Use Change Analysis")
    st.markdown("This tab explores the trend of urbanization using high-resolution ESA WorldCover and long-term MODIS satellite data.")

    st.subheader("High-Resolution Green Space Loss (2020-2021)")
    st.markdown("From high-resolution (10m) ESA WorldCover data, we see the most recent changes:")
    
    col1, col2 = st.columns(2)
    with col1:
        st.image("dump/LULC/better_but_shorter_green to urban.png", caption="ESA WorldCover shows significant conversion of cropland to built-up areas.")
    with col2:
        st.metric("Total Green Area Converted to Built-up", "33.23 km²")
        st.metric("Of which, Cropland Converted to Built-up", "11.99 km²")
        st.info("These figures represent the net change between 2020 and 2021.")

    st.divider()

    st.subheader("Interactive Long-Term Trend Analysis (2002-2021)")
    st.markdown("Explore the 20-year trend of various green land types being converted to urban areas using MODIS data.")

    @st.cache_data
    def load_lulc_data():
        df = pd.read_csv("dump/LULC/using MODIS/delhi_lulc_changes_2001_2021.csv")
        class_map = {
            9: "Savannas", 10: "Grasslands", 11: "Wetlands", 12: "Croplands", 14: "Cropland/Natural Vegetation Mosaic"
        }
        df['from_label'] = df['from_class'].map(class_map)
        df = df[df['from_label'] != 'Cropland/Natural Vegetation Mosaic']
        return df

    lulc_df = load_lulc_data()

    if lulc_df is not None:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("#### Filter Your View")
            year_range = st.select_slider(
                'Select a year range to analyze:',
                options=range(2002, 2022),
                value=(2002, 2021)
            )
            
            green_types = sorted(lulc_df[lulc_df['from_label'].notna()]['from_label'].unique())
            selected_types = st.multiselect(
                'Select green space types to include:',
                options=green_types,
                default=green_types
            )
        
        filtered_data = lulc_df[
            (lulc_df['to_class'] == 13) &
            (lulc_df['from_label'].isin(selected_types)) &
            (lulc_df['year_to'] >= year_range[0]) &
            (lulc_df['year_to'] <= year_range[1])
        ]
        
        annual_conversion = filtered_data.groupby('year_to')['area_km2'].sum().reset_index()

        with col2:
            st.markdown("#### Key Metrics for Your Selection")
            
            m_col1, m_col2, m_col3 = st.columns(3)
            total_loss = annual_conversion['area_km2'].sum()
            peak_year_row = annual_conversion.loc[annual_conversion['area_km2'].idxmax()] if not annual_conversion.empty else None

            m_col1.metric("Total Area Converted", f"{total_loss:.2f} km²")
            if peak_year_row is not None:
                m_col2.metric("Peak Conversion Year", f"{int(peak_year_row['year_to'])}")
                m_col3.metric("Area in Peak Year", f"{peak_year_row['area_km2']:.2f} km²")

            st.markdown("#### Annual Conversion to Urban Area (km²)")
            
            chart = alt.Chart(annual_conversion).mark_bar().encode(
                x=alt.X('year_to:O', title='Year', axis=alt.Axis(labelAngle=0)),
                y=alt.Y('area_km2:Q', title='Area Converted (km²)'),
                tooltip=['year_to', 'area_km2']
            ).properties(
                height=300
            )
            st.altair_chart(chart, use_container_width=True)

        with st.expander("Explore the Filtered Data Table"):
            st.dataframe(filtered_data)
            
    st.divider()

    # --- THIS IS THE CORRECTED ALIGNED LAYOUT ---
    st.subheader("Detailed Long-Term Conversion Patterns (MODIS Data)")
    
    # Create the first row of the 2x2 grid
    grid_row1_col1, grid_row1_col2 = st.columns(2)
    with grid_row1_col1:
        st.image("dump/LULC/using MODIS/greener_to_urban_lulc.png", 
                 caption="Overall green space loss to urban areas per year.")
    with grid_row1_col2:
        st.image("dump/LULC/using MODIS/cropland_to_urban_lulc.png", 
                 caption="A focused view on the conversion of only Croplands.")

    # Create the second row of the 2x2 grid
    grid_row2_col1, grid_row2_col2 = st.columns(2)
    with grid_row2_col1:
        st.image("dump/LULC/using MODIS/cumulative_lulc.png", 
                 caption="The compounding loss of all green space over two decades.")
    with grid_row2_col2:
        st.image("dump/LULC/using MODIS/linear_regression_lulc_new.png", 
                 caption="A predictive trend for future green space loss.")

    # Create a new set of columns to center the fifth image
    center_col1, center_col2, center_col3 = st.columns([1, 2, 1])
    with center_col2:
        st.image("dump/LULC/using MODIS/green_to_other.jpeg", 
                 caption="Analysis of green spaces converting to other non-urban classes.")
        

# --- TAB 3: NDVI (Vegetation Health) Analysis ---
with tab3:
    st.header("Seasonal Vegetation Health Analysis (NDVI)")
    
    st.subheader("Map Color Coding")
    st.markdown("""
    | Color | NDVI Range | Meaning | Typical Surface |
    | :--- | :--- | :--- | :--- |
    | <span style="color:red">■</span> Red | < 0.2 | Barren / built-up / dry soil | Urban, concrete, bare land |
    | <span style="color:gold">■</span> Yellow | 0.2–0.5 | Moderate vegetation | Grassland, cropland, shrubs |
    | <span style="color:green">■</span> Green | > 0.5 | Dense vegetation | Forest, parks, tree cover |
    """, unsafe_allow_html=True)
    
    st.divider()

    st.subheader("Yearly Trends in Vegetation Classes")
    st.markdown("These charts show the total area (in km²) for each vegetation class over the years, comparing Pre- and Post-Monsoon seasons.")
    
    try:
        col1, col2 = st.columns(2)
        with col1:
            st.image("dump/NDVI/ndvi_pre_monsoon.png", caption="Pre-Monsoon Area Trends (2018-2024)")
        with col2:
            st.image("dump/NDVI/ndvi_post_monsoon.png", caption="Post-Monsoon Area Trends (2018-2024)")
    except Exception:
        st.error("Could not load trend images. Make sure 'ndvi_pre_monsoon.png' and 'ndvi_post_monsoon.png' are in the 'dump/NDVI/' folder.")

    st.divider()

    st.subheader("Seasonal Map Comparison for a Specific Year")
    st.markdown("Select a year to visually compare the spatial distribution of vegetation health between the two seasons.")
    
    year = st.selectbox("Select a year:", options=list(range(2018, 2025)), index=6) 

    pre_monsoon_path = f"dump/NDVI/maps/pre/ndvi_class_{year}_Pre-Monsoon_vis.tif"
    post_monsoon_path = f"dump/NDVI/maps/post/ndvi_class_{year}_Post-Monsoon_vis.tif"

    col1, col2 = st.columns(2)
    
    with col1:
        if os.path.exists(pre_monsoon_path):
            st.image(pre_monsoon_path, caption=f"Pre-Monsoon {year}")
        else:
            st.warning(f"Pre-Monsoon map for {year} not available.")
            
    with col2:
        if os.path.exists(post_monsoon_path):
            st.image(post_monsoon_path, caption=f"Post-Monsoon {year}")
        else:
            st.warning(f"Post-Monsoon map for {year} not available.")
            
    st.divider()

    with st.expander("ℹ️ About This Analysis & Key Observations"):
        st.info("""
        **Methodology**: This analysis uses Sentinel-2 satellite imagery to quantify vegetation health via the Normalized Difference Vegetation Index (NDVI).
        
        **Observations**:
        - Data for Winter and Monsoon seasons were often unavailable, likely due to heavy cloud cover.
        - There are sometimes stark differences in vegetation between adjacent years, which could be due to dataset variations or significant environmental events.
        """)


# --- TAB 4: Biodiversity Analysis ---
with tab4:
    st.header("Biodiversity Proxy Analysis (2020 vs. 2021)")
    st.markdown(
        "This analysis uses land cover data as a proxy to estimate biodiversity potential. "
        "Different land types are assigned scores reflecting how much ecological richness they typically support "
        "(e.g., forests score higher than urban areas)."
    )

    st.subheader("Key Change in City-Wide Biodiversity Score")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Mean Score 2020", "3.166")
    col2.metric("Mean Score 2021", "3.676", delta="0.51 (16.1% increase)", delta_color="normal")
    
    st.divider()
    
    st.subheader("Spatial Comparison of Biodiversity Hotspots")

    st.markdown("""
    **Map Legend:** The maps below show the spatial distribution of the biodiversity score.
    - <span style="color:darkgreen">**Dark Green**</span>: High biodiversity potential (e.g., dense forests, wetlands).
    - <span style="color:khaki">**Light Green/Yellow**</span>: Moderate potential (e.g., grasslands, open green spaces).
    - <span style="color:tan">**Tan/Brown**</span>: Low potential (e.g., built-up urban areas, barren land).
    """, unsafe_allow_html=True)
    
    try:
        map_col1, map_col2 = st.columns(2)
        with map_col1:
            st.image("dump/Biodiversity/biodiversity_proxy_visual_2020.tif", caption="Biodiversity Proxy Map 2020")
        with map_col2:
            st.image("dump/Biodiversity/biodiversity_proxy_visual_2021.tif", caption="Biodiversity Proxy Map 2021")
    except FileNotFoundError:
        st.error("Biodiversity map images not found. Make sure they are in the 'dump/Biodiversity/' folder.")

    st.divider()

    st.subheader("Analysis & Interpretation")
    st.markdown("""
    - **Slight Improvement**: The data reveals a modest but positive increase of **16.1%** in the city-wide mean biodiversity score from 2020 to 2021. This suggests minor positive changes in land cover, such as the reclassification of some pixels from cropland or barren land to shrubland or grassland.
    
    - **Key Hotspots**: The most significant biodiversity hotspots (dark green areas) are concentrated along the **Delhi Ridge** (the central green spine) and in the floodplain of the **Yamuna River**. These core ecological zones appear largely stable between the two years.
    
    - **High Variance**: The analysis notes a high standard deviation in the scores. This indicates a landscape of extremes: large, low-scoring urbanized areas punctuated by small, high-scoring pockets of biodiversity. This highlights the fragmented nature of Delhi's ecosystems and the critical importance of preserving the existing green corridors.
    """)

