import pandas as pd
from datetime import datetime


def _get_next_id(df: pd.DataFrame, id_col: str) -> int:
    if df.empty:
        return 1
    return int(df[id_col].max()) + 1


def ingest_recipe(
    recipes_df: pd.DataFrame,
    ingredients_df: pd.DataFrame,
    recipe_ingredients_df: pd.DataFrame,
    recipe_payload: dict,
    ingredients_payload: list,
    user: str,
    paths: dict
):
    """
    Ingest a new recipe and related ingredients safely.
    """

    now = datetime.utcnow().isoformat()

    # --- 1. Create recipe ---
    recipe_id = _get_next_id(recipes_df, "recipe_id")

    new_recipe = {
        "recipe_id": recipe_id,
        "name": recipe_payload["name"],
        "dish_type": recipe_payload["dish_type"],
        "requires_airfryer": recipe_payload["requires_airfryer"],
        "requires_soaking": recipe_payload["requires_soaking"],
        "meal_prep_friendly": recipe_payload["meal_prep_friendly"],
        "video_link": recipe_payload["video_link"],
        "created_at": now,
        "created_by": user,
        "is_active": True
    }

    recipes_updated = pd.concat(
        [recipes_df, pd.DataFrame([new_recipe])],
        ignore_index=True
    )

    # --- 2. Handle ingredients ---
    ingredients_updated = ingredients_df.copy()
    recipe_ing_rows = []

    for ing in ingredients_payload:
        match = ingredients_updated[
            ingredients_updated["name"].str.lower() == ing["name"].lower()
        ]

        if match.empty:
            ingredient_id = _get_next_id(
                ingredients_updated, "ingredient_id"
            )
            ingredients_updated = pd.concat(
                [
                    ingredients_updated,
                    pd.DataFrame([{
                        "ingredient_id": ingredient_id,
                        "name": ing["name"]
                    }])
                ],
                ignore_index=True
            )
        else:
            ingredient_id = match.iloc[0]["ingredient_id"]

        recipe_ing_rows.append({
            "recipe_id": recipe_id,
            "ingredient_id": ingredient_id,
            "quantity": ing["quantity"],
            "is_optional": ing["is_optional"]
        })

    recipe_ingredients_updated = pd.concat(
        [recipe_ingredients_df, pd.DataFrame(recipe_ing_rows)],
        ignore_index=True
    )

    # --- 3. Persist (append-only) ---
    recipes_updated.to_csv(paths["recipes"], index=False)
    ingredients_updated.to_csv(paths["ingredients"], index=False)
    recipe_ingredients_updated.to_csv(paths["recipe_ingredients"], index=False)

    return recipe_id