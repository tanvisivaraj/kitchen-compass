import pandas as pd

from matcher import (
    compute_recipe_ingredient_status,
    compute_recipe_match_metrics,
    get_missing_ingredients
)

from scoring import (
    aggregate_feedback,
    apply_scoring
)


def recommend_recipes(
    recipes: pd.DataFrame,
    ingredients: pd.DataFrame,
    recipe_ingredients: pd.DataFrame,
    pantry: pd.DataFrame,
    recipe_feedback: pd.DataFrame,
    preferences: dict,
    top_n: int = 5
) -> pd.DataFrame:
    """
    End-to-end recommendation pipeline.
    """

    # 1. Pantry matching
    ingredient_status = compute_recipe_ingredient_status(
        recipe_ingredients, pantry
    )

    recipe_metrics = compute_recipe_match_metrics(ingredient_status)

    missing_ingredients = get_missing_ingredients(
        ingredient_status, ingredients
    )

    # 2. Merge recipe metadata
    base_df = (
        recipe_metrics
        .merge(recipes, on="recipe_id", how="left")
        .merge(missing_ingredients, on="recipe_id", how="left")
    )

    base_df["missing_ingredients"] = base_df["missing_ingredients"].fillna('[]')

    # 3. Apply hard constraints
    base_df = _apply_constraints(base_df, preferences)

    if base_df.empty:
        return base_df

    # 4. Feedback aggregation
    feedback_agg = aggregate_feedback(recipe_feedback)

    scoring_df = base_df.merge(
        feedback_agg, on="recipe_id", how="left"
    )

    # 5. Scoring
    scored_df = apply_scoring(scoring_df)

    # 6. Rank & return
    return (
        scored_df
        .sort_values(by="final_score", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


def _apply_constraints(df: pd.DataFrame, prefs: dict) -> pd.DataFrame:
    filtered = df.copy()

    filtered = filtered[
        filtered["pantry_match_pct"] >= prefs.get("min_pantry_match_pct", 0)
    ]

    if "meal_type" in prefs:
        filtered = filtered[filtered["dish_type"] == prefs["meal_type"]]

    if not prefs.get("allow_airfryer", True):
        filtered = filtered[filtered["requires_airfryer"] == False]

    if not prefs.get("allow_soaking", True):
        filtered = filtered[filtered["requires_soaking"] == False]

    return filtered
