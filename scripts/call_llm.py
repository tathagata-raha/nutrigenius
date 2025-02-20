import requests
from jinja2 import Template
from jsonfinder import jsonfinder
import os
def generate_response(question: str, temperature: float = 0.2):
    api_key = os.getenv("AZURE_API_KEY")
    system_prompt = "Answer the following question truthfully."
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "temperature": temperature,
    }
    api_url = "https://openai-nutrigenius.openai.azure.com/openai/deployments/gpt-4o/chat/completions"
    params = {"api-version": "2024-08-01-preview"}

    response = requests.post(api_url, json=data, headers=headers, params=params)
    try:
        response_content = response.json()["choices"][0]["message"]["content"]
    except:
        print(response, response.json())
        raise
    return response_content

def validate_response_ingredients(response: str):
    json_matches = list(jsonfinder(response))
    
    if not json_matches:
        print("No JSON object found in response")
        raise ValueError("No JSON object found in response")
        
    # Take the largest JSON object found
    response = max(json_matches, key=lambda x: x[1] - x[0])
    response = response[2]
    assert "ingredients" in response, "No ingredients found in response"
    for x in response["ingredients"]:
        assert "name" in x, "No name found in ingredient"
        assert "natural_sugar" in x, "No natural sugar found in ingredient"
        assert "added_sugar" in x, "No added sugar found in ingredient"
        assert "low_calorie_sweetner" in x, "No low calorie sweetner found in ingredient"
        assert "fruit_vegetable_nut_herb_spices" in x, "No fruit vegetable nut herb spices found in ingredient"
    return response

def validate_response_reasoning(response: str):
    json_matches = list(jsonfinder(response))
    if not json_matches:
        print("No JSON object found in response")
        raise ValueError("No JSON object found in response")
    response = max(json_matches, key=lambda x: x[1] - x[0])
    response = response[2]
    assert "negative_factors" in response, "No negative factors found in response"
    assert "positive_factors" in response, "No positive factors found in response"
    return response

def validate_response_personalised(response: str):
    json_matches = list(jsonfinder(response))
    if not json_matches:
        print("No JSON object found in response")
        raise ValueError("No JSON object found in response")
    response = max(json_matches, key=lambda x: x[1] - x[0])
    response = response[2]
    assert "reasoning" in response, "No reasoning found in response"
    assert "assessment" in response, "No assessment found in response"
    assert "recommendation" in response, "No recommendation found in response"
    assert response["assessment"] in ["MINIMAL RISK", "MODERATE RISK", "HIGH RISK"], "Assessment is not one of the three categories"
    return response

def parse_ingredients(ingredients: str):
    prompt_template = Template(open("../prompts/ingredients.jinja").read())
    prompt = prompt_template.render(ingredients=ingredients)
    for i in range(5):
        try:    
            print(f"Attempt {i+1}")
            response = generate_response(prompt)
            response = validate_response_ingredients(response)
            print(response)
            break
        except:
            pass
    return response


def get_reasoning(ingredients: str, nutrients: str, raw_scores: dict):
    prompt_template = Template(open("../prompts/ingredients_reasoning.jinja").read())
    if raw_scores["nutrition_score"] < -3:
        negative_factors = 1
        positive_factors = 4
    elif raw_scores["nutrition_score"] <= 0:
        negative_factors = 2
        positive_factors = 3
    elif raw_scores["nutrition_score"] <= 10:
        negative_factors = 3
        positive_factors = 2
    else:
        negative_factors = 4
        positive_factors = 1
    prompt = prompt_template.render(ingredients=ingredients, nutrients=nutrients, negative_scores=raw_scores["negative_scores"], positive_scores=raw_scores["positive_scores"], min_negative_factors=negative_factors-1, max_negative_factors=negative_factors+1, min_positive_factors=positive_factors-1, max_positive_factors=positive_factors+1)
    for i in range(5):
        try:    
            print(f"Attempt {i+1}")
            response = generate_response(prompt)
            response = validate_response_reasoning(response)
            print(response)
            break
        except:
            pass
    return response

def get_personalised_reasoning(ingredients: str, nutrients: str, health_condition: str):
    prompt_template = Template(open("../prompts/personalised_reasoning.jinja").read())
    prompt = prompt_template.render(ingredients=ingredients, nutrients=nutrients, health_condition=health_condition)
    for i in range(5):
        try:
            response = generate_response(prompt)
            response = validate_response_personalised(response)
            print(response)
            break
        except:
            pass
    return response
