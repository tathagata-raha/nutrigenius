# %%
import json
import time
from llm_utils import compute_nutrition_score_and_reasoning, compute_personalised_reasoning

# %%

# %%
with open("../data/tmp.json", "r") as f:
    data = json.load(f)
nutriments, ingredients = data["product"]["nutriments"], data["product"]["ingredients_text_en"]

# %%
nutrition_score_and_reasoning = compute_nutrition_score_and_reasoning(ingredients, nutriments)
# %%
health_condition = "diabetes, allergies to peanuts"
personalised_reasoning = compute_personalised_reasoning(ingredients, nutriments, health_condition)
# %%
