import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# Path setup
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_DIR))

from recommender import recommend_recipes

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Load data
ingredients = pd.read_csv(DATA_DIR / "ingredients.csv")
recipes = pd.read_csv(DATA_DIR / "recipes.csv")
recipe_ingredients = pd.read_csv(DATA_DIR / "recipe_ingredients.csv")
pantry = pd.read_csv(DATA_DIR / "pantry.csv")
recipe_feedback = pd.read_csv(DATA_DIR / "recipe_feedback.csv")

# ---------- UI ----------
st.set_page_config(page_title="Kitchen Compass", layout="centered")

st.title("🧭 Kitchen Compass")
st.subheader("What can I cook right now?")

# Preferences
meal_type = st.selectbox(
    "Meal type",
    ["breakfast", "meal", "snack", "dessert", "beverage"]
)

allow_airfryer = st.checkbox("I can use an airfryer", value=True)
allow_soaking = st.checkbox("I can soak ingredients overnight", value=False)

min_pantry_match = st.slider(
    "Minimum pantry match (%)",
    0, 100, 60
)

if st.button("Find Recipes 🍳"):
    prefs = {
        "meal_type": meal_type,
        "allow_airfryer": allow_airfryer,
        "allow_soaking": allow_soaking,
        "min_pantry_match_pct": min_pantry_match
    }

    results = recommend_recipes(
        recipes=recipes,
        ingredients=ingredients,
        recipe_ingredients=recipe_ingredients,
        pantry=pantry,
        recipe_feedback=recipe_feedback,
        preferences=prefs,
        top_n=5
    )

    if results.empty:
        st.warning("No recipes match your current pantry and preferences.")
    else:
        for _, row in results.iterrows():
            st.markdown(f"### 🍽️ {row['name']}")
            st.write(f"**Pantry match:** {row['pantry_match_pct']:.0f}%")
            st.write(f"**Rating:** ⭐ {row['avg_rating']:.1f}")
            st.write(f"**Missing ingredients:** {', '.join(row['missing_ingredients']) or 'None'}")
            st.markdown(f"[📺 Watch Recipe]({row['video_url']})")
            st.divider()
