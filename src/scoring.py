import pandas as pd


def aggregate_feedback(recipe_feedback: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate feedback per recipe.
    """
    return (
        recipe_feedback
        .groupby("recipe_id")
        .agg(
            avg_rating=("rating", "mean"),
            times_cooked=("rating", "count"),
            would_make_again_rate=("would_make_again", "mean")
        )
        .reset_index()
    )


def apply_scoring(scoring_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute final recommendation score.
    """

    df = scoring_df.copy()

    # Defaults for unseen recipes
    df["avg_rating"] = df["avg_rating"].fillna(3.0)
    df["times_cooked"] = df["times_cooked"].fillna(0)
    df["would_make_again_rate"] = df["would_make_again_rate"].fillna(0.5)

    # Normalize
    df["pantry_score"] = df["pantry_match_pct"] / 100
    df["rating_score"] = df["avg_rating"] / 5
    df["repeat_score"] = df["would_make_again_rate"]

    # Weighted score
    df["final_score"] = (
        0.6 * df["pantry_score"] +
        0.3 * df["rating_score"] +
        0.1 * df["repeat_score"]
    )

    # Penalize bad experiences
    df.loc[df["avg_rating"] < 2.5, "final_score"] *= 0.3
    df.loc[df["would_make_again_rate"] < 0.3, "final_score"] *= 0.5

    return df
