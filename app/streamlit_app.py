import sys
from pathlib import Path
import pandas as pd
import streamlit as st

# ----------------- PAGE CONFIG -----------------
st.set_page_config(page_title="Kitchen Compass", layout="centered")

# ----------------- PATH SETUP -----------------
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

sys.path.append(str(SRC_DIR))

from recommender import recommend_recipes
from ingestion import ingest_recipe

DATA_DIR.mkdir(exist_ok=True)

# ----------------- SESSION STATE -----------------
if "ingredient_rows" not in st.session_state:
    st.session_state.ingredient_rows = []

if "all_results" not in st.session_state:
    st.session_state.all_results = None

if "visible_count" not in st.session_state:
    st.session_state.visible_count = 10

# ----------------- SAFE CSV HANDLING -----------------
def load_or_init_csv(path, columns):
    if path.exists():
        return pd.read_csv(path)
    df = pd.DataFrame(columns=columns)
    df.to_csv(path, index=False)
    return df

def ensure_columns(df, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df

# ----------------- LOAD DATA -----------------
ingredients = load_or_init_csv(
    DATA_DIR / "ingredients.csv",
    ["ingredient_id", "name"]
)

recipes = load_or_init_csv(
    DATA_DIR / "recipes.csv",
    [
        "recipe_id", "name", "dish_type",
        "cuisine", "diet_type", "dish_category",
        "cooking_time_minutes",
        "requires_airfryer", "requires_soaking",
        "meal_prep_friendly", "video_link",
        "created_at", "created_by", "is_active"
    ]
)

recipes = ensure_columns(recipes, ["cuisine", "diet_type", "dish_category"])

recipe_ingredients = load_or_init_csv(
    DATA_DIR / "recipe_ingredients.csv",
    ["recipe_id", "ingredient_id", "quantity", "unit", "is_optional"]
)

pantry = load_or_init_csv(
    DATA_DIR / "pantry.csv",
    ["ingredient_id", "quantity", "updated_at", "updated_by"]
)

recipe_feedback = load_or_init_csv(
    DATA_DIR / "recipe_feedback.csv",
    ["feedback_id", "recipe_id", "rating", "liked", "comments", "cooked_on", "would_make_again"]
)

# ----------------- TABS -----------------
tab_cook, tab_ingest = st.tabs(["🍽️ Cook", "➕ Ingest"])

# ===================== COOK TAB =====================
with tab_cook:
    st.title("🧭 Kitchen Compass")
    st.subheader("What can I cook right now?")

    meal_type = st.selectbox(
        "Meal type",
        ["breakfast", "meal", "snack", "dessert", "beverage"]
    )

    dish_category = st.selectbox(
        "Type of food",
        ["Any"] + sorted(recipes["dish_category"].dropna().unique().tolist())
    )

    preferred_cuisine = st.selectbox(
        "Preferred cuisine (optional)",
        ["Any"] + sorted(recipes["cuisine"].dropna().unique().tolist())
    )

    diet_type = st.selectbox(
        "Diet preference",
        ["Any", "veg", "non-veg"]
    )

    st.markdown("### 🍅 Ingredients you want to cook with (optional)")
    preferred_ingredients = st.multiselect(
        "Choose ingredients (boosts recipes using these)",
        ingredients["name"].tolist()
    )

    allow_airfryer = st.checkbox("I can use an airfryer", value=True)
    allow_soaking = st.checkbox("I can soak ingredients overnight", value=False)

    if st.button("Find Recipes 🍳"):
        prefs = {
            "meal_type": meal_type,
            "dish_category": None if dish_category == "Any" else dish_category,
            "diet_type": None if diet_type == "Any" else diet_type,
            "preferred_cuisine": None if preferred_cuisine == "Any" else preferred_cuisine,
            "preferred_ingredients": preferred_ingredients,
            "allow_airfryer": allow_airfryer,
            "allow_soaking": allow_soaking,
            "min_pantry_match_pct": 0
        }

        results = recommend_recipes(
            recipes=recipes,
            ingredients=ingredients,
            recipe_ingredients=recipe_ingredients,
            pantry=pantry,
            recipe_feedback=recipe_feedback,
            preferences=prefs,
            top_n=len(recipes)
        )

        st.session_state.all_results = results
        st.session_state.visible_count = 10

# ---------- DISPLAY RESULTS ----------
results = st.session_state.all_results

if results is not None:
    if results.empty:
        st.warning("No recipes match your preferences.")
    else:
        visible = results.head(st.session_state.visible_count)

        for _, row in visible.iterrows():
            st.markdown(f"### 🍽️ {row['name']}")

            st.write(f"**Cuisine:** {row.get('cuisine', '-')}")
            st.write(f"**Diet:** {row.get('diet_type', '-')}")
            st.write(f"**Pantry match:** {row['pantry_match_pct']:.0f}%")
            st.write(f"**Cooking time:** {row.get('cooking_time_minutes', '-')} mins")

            # ---- Missing ingredients ----
            missing = row["missing_ingredients"]
            if missing:
                st.write("🛒 **To buy:**")
                for m in missing:
                    st.write(f"- {m}")
            else:
                st.write("✅ Everything available")

            # ---- Video ----
            if row.get("video_link"):
                st.markdown(f"[📺 Watch Recipe]({row['video_link']})")

            # ---- WHY THIS RECIPE ----
            with st.expander("🤔 Why this recipe?"):
                breakdown = row["score_breakdown"]

                st.markdown(
                    f"""
                    **Scoring breakdown**
                    - 🥬 Pantry match: **{breakdown['pantry_match_pct']}%**
                    - ⭐ Average rating: **{breakdown['avg_rating']} / 5**
                    - 🔁 Would make again: **{int(breakdown['would_make_again'] * 100)}%**
                    - 🌍 Cuisine match: **{"Yes" if breakdown['cuisine_match'] else "No"}**
                    - ⏱️ Cooking time: **{breakdown['cooking_time_minutes']} minutes**
                    """
                )

            st.divider()

        # ---- LOAD MORE ----
        if st.session_state.visible_count < len(results):
            if st.button("🔄 Recommend more"):
                st.session_state.visible_count += 5
        else:
            st.success("🎉 You’ve reached the end of the recommendations!")

# ===================== INGEST TAB =====================
with tab_ingest:
    st.header("➕ Add a New Recipe")

    # ---------- BASIC INFO ----------
    with st.expander("📝 Basic details", expanded=True):
        user = st.selectbox("Added by", ["Tanvi", "Anyushka"])
        recipe_name = st.text_input("Recipe name")
        dish_type = st.selectbox(
            "Dish type",
            ["breakfast", "meal", "snack", "dessert", "beverage"]
        )
        video_link = st.text_input("Recipe video link")

    # ---------- CLASSIFICATION ----------
    with st.expander("🍽️ Classification", expanded=True):
        cuisine = st.text_input("Cuisine")
        diet_type_ingest = st.selectbox("Diet type", ["veg", "non-veg"])

        existing_categories = sorted(recipes["dish_category"].dropna().unique().tolist())
        selected_category = st.selectbox("Select dish category", [""] + existing_categories)
        new_category = st.text_input("Or add a new dish category")

        dish_category = (
            new_category.strip().lower().replace(" ", "_")
            if new_category else selected_category
        )

    cooking_time_minutes = st.number_input(
    "Cooking time (minutes)",
    min_value=5,
    max_value=300,
    step=5
    )


    # ---------- CONSTRAINTS ----------
    with st.expander("🔥 Cooking constraints"):
        requires_airfryer = st.checkbox("Requires airfryer")
        requires_soaking = st.checkbox("Requires soaking overnight")
        meal_prep_friendly = st.checkbox("Meal prep friendly")

    # ---------- INGREDIENTS ----------
    with st.expander("🥬 Ingredients", expanded=True):
        existing_ingredients = ingredients["name"].tolist()

        st.markdown("### Select existing ingredients")
        selected_existing = st.multiselect("Existing ingredients", existing_ingredients)

        temp_existing = []
        for ing in selected_existing:
            cols = st.columns(4)
            qty = cols[1].number_input("Qty", 0.0, step=0.1, key=f"qty_{ing}")
            unit = cols[2].selectbox("Unit", ["g", "ml", "cups", "tbsp", "tsp", "pieces"], key=f"unit_{ing}")
            opt = cols[3].checkbox("Optional", key=f"opt_{ing}")

            temp_existing.append({
                "name": ing,
                "quantity": qty,
                "unit": unit,
                "is_optional": opt
            })

        if st.button("➕ Add selected ingredients"):
            for row in temp_existing:
                if row not in st.session_state.ingredient_rows:
                    st.session_state.ingredient_rows.append(row)

        st.divider()

        with st.form("add_new_ing", clear_on_submit=True):
            new_ing = st.text_input("Ingredient name")
            new_qty = st.number_input("Quantity", 0.0, step=0.1)
            new_unit = st.selectbox("Unit", ["g", "ml", "cups", "tbsp", "tsp", "pieces"])
            new_opt = st.checkbox("Optional ingredient")
            submitted = st.form_submit_button("Add ingredient")

            if submitted and new_ing:
                st.session_state.ingredient_rows.append({
                    "name": new_ing.strip(),
                    "quantity": new_qty,
                    "unit": new_unit,
                    "is_optional": new_opt
                })

        if st.session_state.ingredient_rows:
            st.markdown("### 🧾 Ingredients added")
            for row in st.session_state.ingredient_rows:
                st.write(f"- {row['name']} — {row['quantity']} {row['unit']}")

    # ---------- SAVE ----------
    if st.button("💾 Save Recipe"):
        if not recipe_name or not st.session_state.ingredient_rows:
            st.error("Recipe name and ingredients are required.")
        else:
            recipe_payload = {
                "name": recipe_name,
                "dish_type": dish_type,
                "dish_category": dish_category,
                "cuisine": cuisine,
                "cooking_time_minutes": cooking_time_minutes,
                "diet_type": diet_type_ingest,
                "requires_airfryer": requires_airfryer,
                "requires_soaking": requires_soaking,
                "meal_prep_friendly": meal_prep_friendly,
                "video_link": video_link
            }

            paths = {
                "recipes": DATA_DIR / "recipes.csv",
                "ingredients": DATA_DIR / "ingredients.csv",
                "recipe_ingredients": DATA_DIR / "recipe_ingredients.csv"
            }

            new_id = ingest_recipe(
                recipes_df=recipes,
                ingredients_df=ingredients,
                recipe_ingredients_df=recipe_ingredients,
                recipe_payload=recipe_payload,
                ingredients_payload=st.session_state.ingredient_rows,
                user=user,
                paths=paths
            )

            st.session_state.ingredient_rows = []
            st.success(f"✅ Recipe added! (ID: {new_id})")
