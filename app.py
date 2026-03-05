import streamlit as st
import pandas as pd
from typing import List, Tuple

from src.data_access.repository import InMemoryRestaurantRepository
from src.data_ingestion.hf_client import load_restaurants_from_hf
from src.domain.models import UserPreference, Restaurant
from src.llm.llm_client import LlmClient
from src.services.recommendation_service import RecommendationService

# Page configuration
st.set_page_config(
    page_title="Zomato AI Recommender",
    page_icon="🍴",
    layout="wide",
)

# Custom CSS for Premium Zomato Aesthetic
st.markdown("""
<style>
    :root {
        --zomato-red: #ef4444;
    }
    .main {
        background-color: #f8f8f8;
    }
    .stButton>button {
        background-color: var(--zomato-red);
        color: white;
        border-radius: 8px;
        width: 100%;
        border: none;
        padding: 10px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #dc2626;
        color: white;
    }
    .res-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e8e8e8;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .res-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }
    .res-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .res-name {
        font-size: 20px;
        font-weight: 700;
        color: #1c1c1c;
    }
    .res-rating {
        color: #24963f;
        font-weight: 700;
        font-size: 16px;
    }
    .res-cuisines {
        font-size: 14px;
        color: #1c1c1c;
        margin-bottom: 6px;
    }
    .res-location-price {
        font-size: 14px;
        color: #696969;
        margin-bottom: 15px;
    }
    .res-explanation-label {
        font-weight: 700;
        color: #1c1c1c;
        margin-top: 15px;
        font-size: 14px;
    }
    .res-explanation-text {
        font-size: 14px;
        color: #444;
        line-height: 1.5;
        margin-top: 4px;
    }
    .logo-text {
        font-size: 40px;
        font-weight: 900;
        color: var(--zomato-red);
        font-style: italic;
        margin-bottom: 30px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# App State / Services Initiation
@st.cache_resource
def get_service():
    restaurants = load_restaurants_from_hf(limit=None)
    repo = InMemoryRestaurantRepository(restaurants)
    llm_client = LlmClient()
    return RecommendationService(repo, llm_client)

service = get_service()

# Header
st.markdown('<div class="logo-text">zomato <span style="font-size: 20px; font-weight: normal; font-style: normal; color: #696969;">AI Recommender</span></div>', unsafe_allow_html=True)

# Sidebar Filters
with st.sidebar:
    st.header("Filters")
    
    # Neighborhoods
    all_areas = sorted({(r.area or "").strip() for r in service.list_restaurants() if r.area})
    area = st.selectbox("Neighborhood", options=["All"] + all_areas, index=0)
    
    # Cuisines
    all_cuisines = set()
    for r in service.list_restaurants():
        for c in r.cuisines:
            if c.strip(): all_cuisines.add(c.strip())
    cuisine_options = sorted(list(all_cuisines))
    cuisine = st.selectbox("Cuisine", options=["All"] + cuisine_options, index=0)
    
    # Price
    price_max = st.slider("Max Budget (for two)", min_value=100, max_value=10000, value=2000, step=100)
    
    # Rating
    min_rating = st.slider("Min Rating", min_value=0.0, max_value=5.0, value=3.5, step=0.1)
    
    search_clicked = st.button("Find Recommendations")

# Main Content
if search_clicked or (area != "All" or cuisine != "All"):
    with st.spinner("Generating personalized recommendations..."):
        prefs = UserPreference(
            location="Bangalore",
            area=area if area != "All" else None,
            price_max=float(price_max),
            min_rating=float(min_rating),
            cuisines=[cuisine] if cuisine != "All" else [],
            limit=6
        )
        
        recs = service.get_recommendations(prefs)
        
        if not recs:
            if cuisine != "All":
                st.warning(f"No restaurants found for {cuisine} within the selected rating and price across Bangalore.")
            else:
                st.warning("No restaurants found matching your criteria. Try relaxing your filters!")
        else:
            st.subheader(f"Top Matches in {area if area != 'All' else 'Bangalore'}")
            
            # Display in columns (2 per row for more text room)
            cols = st.columns(2)
            restaurant_by_id = {r.id: r for r in service.list_restaurants()}
            
            for i, rec in enumerate(recs):
                restaurant = restaurant_by_id.get(rec.restaurant_id)
                if not restaurant: continue
                
                col = cols[i % 2]
                
                # Render Card
                with col:
                    cuisine_list = " &bull; ".join(restaurant.cuisines[:4])
                    st.markdown(f"""
                    <div class="res-card">
                        <div class="res-header">
                            <span class="res-name">{restaurant.name}</span>
                            <span class="res-rating">⭐ {restaurant.rating}</span>
                        </div>
                        <div class="res-cuisines">{cuisine_list}</div>
                        <div class="res-location-price">
                            📍 {restaurant.area}, {restaurant.city}<br>
                            ₹{int(restaurant.average_cost_for_two or 0)} for two
                        </div>
                        <div class="res-explanation-label">Explanation:</div>
                        <div class="res-explanation-text">
                            {rec.explanation}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
else:
    # Welcome View
    st.info("👋 Welcome! Use the sidebar filters to find the perfect restaurant in Bangalore.")
    
    # Show some trending local spots (Bangalore)
    st.markdown("### Trending in Bangalore")
    trending_prefs = UserPreference(location="Bangalore", area=None, limit=4)
    trending_recs = service.get_recommendations(trending_prefs)
    
    cols = st.columns(2)
    restaurant_by_id = {r.id: r for r in service.list_restaurants()}
    for i, rec in enumerate(trending_recs):
        restaurant = restaurant_by_id.get(rec.restaurant_id)
        if restaurant:
            with cols[i % 2]:
                cuisine_list = " &bull; ".join(restaurant.cuisines[:3])
                st.markdown(f"""
                <div class="res-card">
                    <div class="res-header">
                        <span class="res-name">{restaurant.name}</span>
                        <span class="res-rating">⭐ {restaurant.rating}</span>
                    </div>
                    <div class="res-cuisines">{cuisine_list}</div>
                    <div class="res-location-price">📍 {restaurant.area}</div>
                </div>
                """, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.caption("Built with ❤️ using Streamlit & Groq LLM")
