# Zomato AI Recommender 🍴

A premium restaurant recommendation engine for Bangalore, powered by Streamlit and Groq LLM (Llama 3).

## 🚀 Deployment on Streamlit Cloud

To deploy this project on Streamlit Cloud, follow these steps:

1.  **Push to GitHub**: Connect your repository (ensure `.streamlit/config.toml` and `app.py` are included).
2.  **Connect Streamlit Cloud**: Point it to your `app.py`.
3.  **Set Secrets**:
    - Go to your app's **Settings** on the Streamlit Cloud dashboard.
    - Navigate to **Secrets**.
    - Add your **GROQ_API_KEY** as shown below:

```toml
GROQ_API_KEY = "your-actual-groq-api-key-here"
```

The application will automatically use this secret to power the AI recommendations.

## 🛠️ Features
- **Strict Matching**: Priority tiers from Local Strict to City-wide Expansion.
- **AI-Driven Insights**: Personalized explanations for every restaurant.
- **Premium UI**: Modern Zomato-inspired aesthetic with dynamic results.
