import React, { useState } from "react";

export default function PreferenceForm({ onSubmit, cities = [], availableCuisines = [] }) {
  const [location, setLocation] = useState("Indiranagar");
  const [cuisines, setCuisines] = useState("");
  const [minRating, setMinRating] = useState(3.5);
  const [priceMin, setPriceMin] = useState(100);
  const [priceMax, setPriceMax] = useState(600);

  const handleSubmit = (event) => {
    event.preventDefault();

    const payload = {
      location,
      cuisines: cuisines
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean),
      min_rating: Number(minRating) || null,
      price_min: Number(priceMin) || null,
      price_max: Number(priceMax) || null,
      limit: 5
    };

    onSubmit(payload);
  };

  return (
    <form className="preference-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Neighborhood / Area</span>
        <select value={location} onChange={(e) => setLocation(e.target.value)}>
          {cities.map((city) => (
            <option key={city} value={city}>
              {city}
            </option>
          ))}
        </select>
      </label>

      <label className="field">
        <span>Cuisines</span>
        <input
          type="text"
          list="cuisine-options"
          value={cuisines}
          onChange={(e) => setCuisines(e.target.value)}
          placeholder="e.g. North Indian, Chinese"
        />
        <datalist id="cuisine-options">
          {availableCuisines.map((cuisine) => (
            <option key={cuisine} value={cuisine} />
          ))}
        </datalist>
        <small style={{ fontSize: '11px', color: '#999' }}>Separate multiple with commas</small>
      </label>

      <label className="field">
        <span>Minimum Rating ({minRating})</span>
        <input
          type="range"
          min="0"
          max="5"
          step="0.1"
          value={minRating}
          onChange={(e) => setMinRating(e.target.value)}
          style={{ accentColor: '#ef4444' }}
        />
      </label>

      <div className="field">
        <span>Price Range (₹)</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="number"
            placeholder="Min"
            value={priceMin}
            onChange={(e) => setPriceMin(e.target.value)}
          />
          <input
            type="number"
            placeholder="Max"
            value={priceMax}
            onChange={(e) => setPriceMax(e.target.value)}
          />
        </div>
      </div>

      <button type="submit" className="submit-btn" disabled={!location}>
        Apply Filters
      </button>
    </form>
  );
}
