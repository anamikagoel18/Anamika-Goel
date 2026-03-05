import React, { useState, useEffect } from "react";
import PreferenceForm from "./components/PreferenceForm";
import RecommendationList from "./components/RecommendationList";
import "./styles.css";

function App() {
  const [recommendations, setRecommendations] = useState([]);
  const [restaurantMap, setRestaurantMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cities, setCities] = useState([]);
  const [availableCuisines, setAvailableCuisines] = useState([]);

  useEffect(() => {
    async function loadMetadata() {
      try {
        const [cityRes, cuisineRes] = await Promise.all([
          fetch("http://127.0.0.1:8000/cities"),
          fetch("http://127.0.0.1:8000/cuisines")
        ]);

        if (cityRes.ok) {
          const cityData = await cityRes.json();
          setCities(cityData);
        }

        if (cuisineRes.ok) {
          const cuisineData = await cuisineRes.json();
          setAvailableCuisines(cuisineData);
        }
      } catch (err) {
        console.error("Failed to load metadata", err);
      }
    }
    loadMetadata();
  }, []);

  const handleSearch = async (preferences) => {
    setLoading(true);
    setError(null);
    setRecommendations([]);

    try {
      const response = await fetch("http://127.0.0.1:8000/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error("Failed to fetch recommendations");
      }

      const data = await response.json();
      setRecommendations(data.recommendations);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Laptop Header */}
      <header className="top-header">
        <div className="header-content">
          <div className="logo">zomato</div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="main-layout">
        {/* Left Sidebar: Filters */}
        <aside className="filters-sidebar">
          <h2>Filters</h2>
          <PreferenceForm
            onSubmit={handleSearch}
            cities={cities}
            availableCuisines={availableCuisines}
          />
        </aside>

        {/* Center: Recommendations */}
        <main className="results-area">
          <h1>Recommended Restaurants in Bangalore</h1>

          {error && <div className="error-msg">{error}</div>}

          {loading ? (
            <div style={{ textAlign: 'center', padding: '100px' }}>
              <p style={{ fontSize: '18px', color: '#666' }}>Looking for the best options...</p>
            </div>
          ) : recommendations.length > 0 ? (
            <div className="recommendation-grid">
              {recommendations.map((rec, index) => (
                <RecommendationList
                  key={index}
                  recommendation={rec}
                  restaurant={rec.restaurant}
                />
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '100px', background: 'white', borderRadius: '12px' }}>
              <p style={{ color: '#999' }}>No recommendations yet. Use the filters on the left to get started!</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
