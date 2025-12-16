import pandas as pd
import numpy as np


def aggregate_feedback(feedback: pd.DataFrame) -> pd.DataFrame:
    if feedback.empty:
        return pd.DataFrame(
            columns=["recipe_id", "avg_rating", "would_make_again"]
        )

    agg = (
        feedback
        .groupby("recipe_id")
        .agg(
            avg_rating=("rating", "mean"),
            would_make_again=("would_make_again", "mean")
        )
        .reset_index()
    )

    return agg


WEIGHTS = {
    "pantry_match": 0.45,
    "rating": 0.25,
    "would_make_again": 0.15,
    "cuisine_match": 0.10,
    "time_penalty": 0.05
}


def apply_scoring(df: pd.DataFrame) -> pd.DataFrame:
    scored = df.copy()

    # ---------- Ensure columns exist ----------
    if "avg_rating" not in scored.columns:
        scored["avg_rating"] = 3.0

    if "would_make_again" not in scored.columns:
        scored["would_make_again"] = 0.0

    if "pantry_match_pct" not in scored.columns:
        scored["pantry_match_pct"] = 0.0

    if "cuisine_match" not in scored.columns:
        scored["cuisine_match"] = False

    if "cooking_time_minutes" not in scored.columns:
        scored["cooking_time_minutes"] = 60

    # ---------- Clean values ----------
    scored["avg_rating"] = scored["avg_rating"].fillna(3)
    scored["would_make_again"] = scored["would_make_again"].fillna(0)
    scored["pantry_match_pct"] = scored["pantry_match_pct"].fillna(0)
    scored["cuisine_match"] = scored["cuisine_match"].fillna(False)
    scored["cooking_time_minutes"] = (
        scored["cooking_time_minutes"]
        .fillna(60)
        .clip(lower=5)
    )

    # ---------- Time score ----------
    max_time = max(scored["cooking_time_minutes"].max(), 1)
    scored["time_score"] = 1 - (scored["cooking_time_minutes"] / max_time)

    # ---------- Final score ----------
    scored["final_score"] = (
        WEIGHTS["pantry_match"] * (scored["pantry_match_pct"] / 100) +
        WEIGHTS["rating"] * (scored["avg_rating"] / 5) +
        WEIGHTS["would_make_again"] * scored["would_make_again"] +
        WEIGHTS["cuisine_match"] * scored["cuisine_match"].astype(int) +
        WEIGHTS["time_penalty"] * scored["time_score"]
    )

    # ---------- Score breakdown (for UI) ----------
    scored["score_breakdown"] = scored.apply(
        lambda r: {
            "pantry_match_pct": round(r["pantry_match_pct"], 1),
            "avg_rating": round(r["avg_rating"], 2),
            "would_make_again": round(r["would_make_again"], 2),
            "cuisine_match": bool(r["cuisine_match"]),
            "cooking_time_minutes": int(r["cooking_time_minutes"])
        },
        axis=1
    )

    return scored
