import React from "react";

export default function RecommendationList({ recommendation, restaurant }) {
  // Use a fallback image if none provided
  const imageUrl = restaurant.image_url || "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=400&q=80";

  return (
    <div className="res-card">
      <div className="res-image-box">
        <img src={imageUrl} alt={restaurant.name} />
      </div>

      <div className="res-details">
        <div className="res-name-row">
          <h3 className="res-name">{restaurant.name}</h3>
          <div className="res-rating-tag">
            {restaurant.rating || "N/A"} ★
          </div>
        </div>

        <div className="res-info-row">
          <span>{restaurant.cuisines.slice(0, 2).join(", ")}</span>
          <span>₹{restaurant.average_cost_for_two || "??? "} for two</span>
        </div>

        <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>
          {restaurant.area}, {restaurant.city}
        </div>

        <div className="explanation-box">
          {recommendation.explanation}
        </div>
      </div>
    </div>
  );
}
