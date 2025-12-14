# 🧭 Kitchen Compass

Kitchen Compass is a **pantry-aware, taste-adaptive recipe recommendation system** that helps you decide *what to cook right now* using ingredients you already have — with minimal extra buying.

Designed as a **mobile-first personal app**, Kitchen Compass learns from your cooking history and preferences over time and works entirely using free, open-source tools.

---

## ✨ Features

- 🥕 Pantry-aware recipe recommendations
- 🍳 Ingredient-based matching logic
- ⭐ Personal ratings & feedback system
- 🚫 Filters for appliances (airfryer, soaking, etc.)
- 📱 Mobile-friendly UI (Streamlit PWA)
- 🧠 Explainable recommendations (“Why this recipe?”)

---

## 🏗️ Architecture Overview

```text
UI (Streamlit)
   ↓
Recommender Engine (Python)
   ↓
CSV-based Data Store