import pandas as pd


def aggregate_pantry(pantry_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate pantry quantities by ingredient_id.
    """
    return (
        pantry_df
        .groupby("ingredient_id", as_index=False)
        .agg({"quantity": "sum"})
    )


def compute_recipe_ingredient_status(
    recipe_ingredients_df: pd.DataFrame,
    pantry_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Returns ingredient-level availability status for each recipe.
    """

    pantry_agg = aggregate_pantry(pantry_df)

    df = recipe_ingredients_df.merge(
        pantry_agg,
        on="ingredient_id",
        how="left"
    )

    df["available_quantity"] = df["quantity_y"].fillna(0)
    df = df.rename(columns={"quantity_x": "required_quantity"})
    df.drop(columns=["quantity_y"], inplace=True)

    df["is_available"] = df["available_quantity"] >= df["required_quantity"]

    # Optional ingredients should not penalize availability
    df.loc[df["is_optional"], "is_available"] = True

    df["status"] = df.apply(_ingredient_status, axis=1)

    return df


def _ingredient_status(row) -> str:
    if row["is_optional"]:
        return "optional"
    elif row["is_available"]:
        return "available"
    elif row["available_quantity"] > 0:
        return "partial"
    else:
        return "missing"


def compute_recipe_match_metrics(
    ingredient_status_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Computes recipe-level pantry match metrics.
    """

    metrics = (
        ingredient_status_df[ingredient_status_df["status"] != "optional"]
        .groupby("recipe_id")
        .agg(
            total_ingredients=("ingredient_id", "count"),
            available_count=("status", lambda x: (x == "available").sum()),
            missing_count=("status", lambda x: (x == "missing").sum()),
            partial_count=("status", lambda x: (x == "partial").sum())
        )
        .reset_index()
    )

    metrics["pantry_match_pct"] = (
        metrics["available_count"] / metrics["total_ingredients"]
    ) * 100

    return metrics


def get_missing_ingredients(
    ingredient_status_df: pd.DataFrame,
    ingredients_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Returns missing ingredients per recipe.
    """

    missing = (
        ingredient_status_df[ingredient_status_df["status"] == "missing"]
        .merge(ingredients_df, on="ingredient_id", how="left")
        .groupby("recipe_id")["name"]
        .apply(list)
        .reset_index(name="missing_ingredients")
    )

    return missing
