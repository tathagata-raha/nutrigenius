from call_llm import parse_ingredients, get_reasoning, get_personalised_reasoning


def get_nutriments_per_100g(nutriments: dict) -> dict:
    return {k[:-5]: v for k, v in nutriments.items() if k.endswith("_100g") and k not in ["energy_100g", "nova-group_100g", "nutrition-score-fr_100g"]}
def get_ingredients_list(ingredients: str) -> list:
    return ingredients.split(",")
def calculate_negative_score_for_calories(calories: float) -> float:
    if calories <= 80: return 0
    elif calories <= 160: return 1
    elif calories <= 240: return 2
    elif calories <= 320: return 3
    elif calories <= 400: return 4
    elif calories <= 480: return 5
    elif calories <= 560: return 6
    elif calories <= 640: return 7
    elif calories <= 720: return 8
    elif calories <= 800: return 9
    else: return 10

def calculate_negative_score_for_saturated_fat(sat_fat: float) -> float:
    if sat_fat <= 1: return 0
    elif sat_fat <= 2: return 1
    elif sat_fat <= 3: return 2
    elif sat_fat <= 4: return 3
    elif sat_fat <= 5: return 4
    elif sat_fat <= 6: return 5
    elif sat_fat <= 7: return 6
    elif sat_fat <= 8: return 7
    elif sat_fat <= 9: return 8
    elif sat_fat <= 10: return 9
    else: return 10

def calculate_negative_score_for_trans_fat(trans_fat: float, has_trans_fat_ingredient: bool) -> float:
    if trans_fat == 0 and not has_trans_fat_ingredient: return 0
    elif trans_fat == 0 and has_trans_fat_ingredient: return 4
    else: return 5  # Penalty for any trans fat

def calculate_negative_score_for_sodium(sodium: float) -> float:
    if sodium <= 90: return 0
    elif sodium <= 180: return 1
    elif sodium <= 270: return 2
    elif sodium <= 360: return 3
    elif sodium <= 450: return 4
    elif sodium <= 540: return 5
    elif sodium <= 630: return 6
    elif sodium <= 720: return 7
    elif sodium <= 810: return 8
    elif sodium <= 900: return 9
    else: return 10
    
def calculate_negative_score_for_sugar(sugar: float) -> float:
    if sugar <= 4.5: return 0
    elif sugar <= 9: return 1
    elif sugar <= 13.5: return 2
    elif sugar <= 18: return 3
    elif sugar <= 22.5: return 4
    elif sugar <= 27: return 5
    elif sugar <= 31: return 6
    elif sugar <= 36: return 7
    elif sugar <= 40: return 8
    elif sugar <= 45: return 9
    elif sugar <= 50: return 10
    elif sugar <= 55: return 11
    elif sugar <= 60: return 12
    elif sugar <= 65: return 13
    elif sugar <= 70: return 14
    elif sugar <= 75: return 15
    elif sugar <= 80: return 16
    else: return 17
    
def determine_sugar_multiplier(ingredients_list: list) -> float:
    added_sugar_present = False
    natural_sugar_present = False
    added_sugar_first = False
    for ingredient in ingredients_list:
        if ingredient["natural_sugar"] == "yes":
            natural_sugar_present = True
        elif ingredient["added_sugar"] == "yes":
            added_sugar_present = True
            if not natural_sugar_present:
                added_sugar_first = True
    if natural_sugar_present and not added_sugar_present:
        return 1
    elif natural_sugar_present and not added_sugar_first:
        return 1.16
    elif natural_sugar_present and added_sugar_first:
        return 1.33
    elif added_sugar_present and not natural_sugar_present:
        return 1.5
    else:
        return 0
    
def calculate_negative_score_for_low_calorie_sweetner(sugar: float, ingredients_list: list) -> float:
    low_calorie_sweetner_present = False
    for ingredient in ingredients_list:
        if ingredient["low_calorie_sweetner"] == "yes":
            low_calorie_sweetner_present = True
    if low_calorie_sweetner_present and sugar > 0:
        return 3.75
    elif low_calorie_sweetner_present and sugar == 0:
        return 7.5
    else:
        return 0

def calculate_positive_score_for_fruit_vegetable_content(fruit_veg_content: float) -> float:
    if fruit_veg_content <= 40: return 0
    elif fruit_veg_content <= 60: return 1
    elif fruit_veg_content <= 80: return 2
    else: return 5

def calculate_positive_score_for_protein(protein: float) -> float:
    if protein <= 1.6: return 0
    elif protein <= 3.2: return 1
    elif protein <= 4.8: return 2
    elif protein <= 6.4: return 3
    elif protein <= 8.0: return 4
    else: return 5

def calculate_positive_score_for_fiber(fiber: float) -> float:
    if fiber <= 2.0: return 0
    elif fiber <= 3.0: return 1
    elif fiber <= 5.0: return 2
    elif fiber <= 6.0: return 3
    elif fiber <= 8.0: return 4
    else: return 5

def calculate_raw_nutrition_score(nutriments_per_100g: dict, ingredients: str) -> float:
    positive_score = 0  # For green columns
    negative_score = 0  # For red columns
    
    ingredients_list = parse_ingredients(ingredients)["ingredients"]
    
    # Extract relevant nutrient values
    calories = nutriments_per_100g.get('energy-kcal', 0)
    sat_fat = nutriments_per_100g.get('saturated-fat', 0)
    trans_fat = nutriments_per_100g.get('trans-fat', 0)
    sodium = nutriments_per_100g.get('sodium', 0) * 1000  # Convert to mg
    sugar = nutriments_per_100g.get('sugars', 0)
    fiber = nutriments_per_100g.get('fiber', 0)
    protein = nutriments_per_100g.get('proteins', 0)
    fruits_vegetables_nuts_estimate = nutriments_per_100g.get('fruits-vegetables-nuts-estimate-from-ingredients', 0)
    fruits_vegetables_legumes_estimate = nutriments_per_100g.get('fruits-vegetables-legumes-estimate-from-ingredients', 0)
    fruits_vegetable_estimate = max(fruits_vegetables_nuts_estimate, fruits_vegetables_legumes_estimate)
    
    has_trans_fat_ingredient = False # ask LLM
    fruit_veg_content = 0 # ask LLM
    negative_scores = {
        "calories": calculate_negative_score_for_calories(calories),
        "saturated_fat": calculate_negative_score_for_saturated_fat(sat_fat),
        "trans_fat": calculate_negative_score_for_trans_fat(trans_fat, has_trans_fat_ingredient),
        "sodium": calculate_negative_score_for_sodium(sodium),
        "sugar": calculate_negative_score_for_sugar(sugar) * determine_sugar_multiplier(ingredients_list),
        "low_calorie_sweetner": calculate_negative_score_for_low_calorie_sweetner(sugar, ingredients_list)
    }
    positive_scores = {
        "fruit_vegetable_content": calculate_positive_score_for_fruit_vegetable_content(fruits_vegetable_estimate),
        "protein": calculate_positive_score_for_protein(protein),
        "fiber": calculate_positive_score_for_fiber(fiber)
    }
    return {
        "positive_scores": positive_scores,
        "negative_scores": negative_scores,
        "nutrition_score": sum(negative_scores.values()) - sum(positive_scores.values())
    }
def get_nutrition_score(raw_scores: dict) -> float:
    if raw_scores["nutrition_score"] < -3: return 1
    elif raw_scores["nutrition_score"] <= 0: return 3 + (2/3 * raw_scores["nutrition_score"])
    elif raw_scores["nutrition_score"] <= 10: return 3 + (0.106 * raw_scores["nutrition_score"])
    else: return 2.26 + (0.048 * raw_scores["nutrition_score"])

def format_reasoning(reasoning: str) -> str:
    res = ""
    if len(reasoning["positive_factors"]) > 0:
        res += "### Positive factors:\n"
        res += "\n".join([f"- {factor}" for factor in reasoning["positive_factors"]])
    if len(reasoning["negative_factors"]) > 0:
        if res != "":
            res += "\n\n"
        res += "### Negative factors:\n"
        res += "\n".join([f"- {factor}" for factor in reasoning["negative_factors"]])
    return res

def compute_nutrition_score_and_reasoning(ingredients: str, nutriments: dict) -> dict:
    nutriments_per_100g = get_nutriments_per_100g(nutriments)
    raw_scores = calculate_raw_nutrition_score(nutriments_per_100g, ingredients)
    nutrition_score = get_nutrition_score(raw_scores)
    reasoning = get_reasoning(ingredients, nutriments_per_100g, raw_scores)
    return {
        "nutrition_score": nutrition_score,
        "reasoning": format_reasoning(reasoning),
    }

def format_personalised_reasoning(reasoning: dict) -> str:
    res = ""
    res += f"### Reasoning:\n"
    res += "\n".join([f"- {factor}" for factor in reasoning["reasoning"]])
    res += "\n\n"
    res += f"### Recommendations:\n"
    res += "\n".join([f"- {recommendation}" for recommendation in reasoning["recommendation"]])
    return res

def compute_personalised_reasoning(ingredients: str, nutriments: dict, health_condition: str) -> dict:
    nutriments_per_100g = get_nutriments_per_100g(nutriments)
    reasoning = get_personalised_reasoning(ingredients, nutriments_per_100g, health_condition)
    return {
        "assessment": reasoning["assessment"],
        "markdown": format_personalised_reasoning(reasoning)
    }
