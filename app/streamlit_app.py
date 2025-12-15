import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# ----------------- PAGE CONFIG (MUST BE FIRST) -----------------
st.set_page_config(page_title="Kitchen Compass", layout="centered")

# ----------------- PATH SETUP -----------------
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

sys.path.append(str(SRC_DIR))

from recommender import recommend_recipes
from ingestion import ingest_recipe

DATA_DIR.mkdir(exist_ok=True)

# ----------------- SAFE CSV LOADER -----------------
def load_or_init_csv(path, columns):
    if path.exists():
        return pd.read_csv(path)
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

def ensure_columns(df: pd.DataFrame, required_columns: list) -> pd.DataFrame:
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
    return df

# ----------------- LOAD DATA (ONCE) -----------------
ingredients = load_or_init_csv(
    DATA_DIR / "ingredients.csv",
    ["ingredient_id", "name"]
)

recipes = load_or_init_csv(
    DATA_DIR / "recipes.csv",
    [
        "recipe_id", "name", "dish_type",
        "cuisine", "diet_type", "dish_category",
        "requires_airfryer", "requires_soaking",
        "meal_prep_friendly", "video_url",
        "created_at", "created_by", "is_active"
    ]
)

recipes = ensure_columns(
    recipes,
    [
        "dish_category",
        "cuisine",
        "diet_type",
        "requires_airfryer",
        "requires_soaking",
        "meal_prep_friendly"
    ]
)

recipe_ingredients = load_or_init_csv(
    DATA_DIR / "recipe_ingredients.csv",
    ["recipe_id", "ingredient_id", "quantity", "is_optional"]
)

pantry = load_or_init_csv(
    DATA_DIR / "pantry.csv",
    ["ingredient_id", "quantity", "updated_at", "updated_by"]
)

recipe_feedback = load_or_init_csv(
    DATA_DIR / "recipe_feedback.csv",
    [
        "feedback_id", "recipe_id", "rating",
        "liked", "comments", "cooked_on",
        "would_make_again"
    ]
)

# ----------------- UI TABS -----------------
tab_cook, tab_ingest = st.tabs(["🍽️ Cook", "➕ Ingest"])

# ===================== COOK TAB =====================
with tab_cook:
    st.title("🧭 Kitchen Compass")
    st.subheader("What can I cook right now?")

    meal_type = st.selectbox(
        "Meal type",
        ["breakfast", "meal", "snack", "dessert", "beverage"]
    )

    available_categories = (
        sorted(recipes["dish_category"].dropna().unique().tolist())
        if "dish_category" in recipes.columns
        else []
    )

    dish_category = st.selectbox(
        "What kind of food?",
        ["Any"] + available_categories
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
            "dish_category": None if dish_category == "Any" else dish_category,
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
                st.write(
                    f"**Missing ingredients:** {', '.join(row['missing_ingredients']) or 'None'}"
                )
                st.markdown(f"[📺 Watch Recipe]({row['video_url']})")
                st.divider()

# ===================== INGEST TAB =====================
with tab_ingest:
    st.header("➕ Add a New Recipe")

    # -------- BASIC INFO --------
    with st.expander("📝 Basic details", expanded=True):
        user = st.selectbox("Added by", ["Tanvi", "Anyushka"])
        recipe_name = st.text_input("Recipe name")

        dish_type = st.selectbox(
            "Dish type",
            ["breakfast", "meal", "snack", "dessert", "beverage"]
        )

        video_url = st.text_input("Recipe video link")

    # -------- CLASSIFICATION --------
    with st.expander("🍽️ Classification", expanded=True):
        cuisine = st.text_input("Cuisine (e.g. Indian, Italian)")
        diet_type = st.selectbox("Diet type", ["veg", "non-veg"])

        existing_categories = sorted(
            recipes["dish_category"].dropna().unique().tolist()
        )

        selected_category = st.selectbox(
            "Select dish category",
            [""] + existing_categories
        )

        new_category = st.text_input("Or add a new dish category")

        dish_category = (
            new_category.strip().lower().replace(" ", "_")
            if new_category
            else selected_category
        )

    # -------- COOKING CONSTRAINTS --------
    with st.expander("🔥 Cooking constraints"):
        requires_airfryer = st.checkbox("Requires airfryer")
        requires_soaking = st.checkbox("Requires soaking overnight")
        meal_prep_friendly = st.checkbox("Meal prep friendly")

    # -------- INGREDIENTS --------
    with st.expander("🥬 Ingredients", expanded=True):
        ingredient_rows = []

        existing_ingredients = ingredients["name"].tolist()

        selected_existing = st.multiselect(
            "Select existing ingredients",
            existing_ingredients
        )

        for ing in selected_existing:
            qty = st.number_input(
                f"{ing} quantity",
                min_value=0.0,
                step=0.1,
                key=f"qty_{ing}"
            )
            optional = st.checkbox(
                f"{ing} is optional",
                key=f"opt_{ing}"
            )

            ingredient_rows.append({
                "name": ing,
                "quantity": qty,
                "is_optional": optional
            })

        st.markdown("**Add new ingredient**")
        new_ing = st.text_input("Ingredient name")
        new_qty = st.number_input("Quantity", min_value=0.0, step=0.1)
        new_opt = st.checkbox("Optional ingredient")

        if st.button("Add ingredient"):
            if new_ing:
                ingredient_rows.append({
                    "name": new_ing.strip(),
                    "quantity": new_qty,
                    "is_optional": new_opt
                })
                st.success(f"Added {new_ing}")

    # -------- SAVE --------
    if st.button("💾 Save Recipe"):
        if not recipe_name or not ingredient_rows:
            st.error("Recipe name and ingredients are required.")
        else:
            recipe_payload = {
                "name": recipe_name,
                "dish_type": dish_type,
                "dish_category": dish_category,
                "cuisine": cuisine,
                "diet_type": diet_type,
                "requires_airfryer": requires_airfryer,
                "requires_soaking": requires_soaking,
                "meal_prep_friendly": meal_prep_friendly,
                "video_url": video_url
            }

            paths = {
                "recipes": DATA_DIR / "recipes.csv",
                "ingredients": DATA_DIR / "ingredients.csv",
                "recipe_ingredients": DATA_DIR / "recipe_ingredients.csv"
            }

            new_recipe_id = ingest_recipe(
                recipes_df=recipes,
                ingredients_df=ingredients,
                recipe_ingredients_df=recipe_ingredients,
                recipe_payload=recipe_payload,
                ingredients_payload=ingredient_rows,
                user=user,
                paths=paths
            )

            st.success(f"Recipe added! (ID: {new_recipe_id})")