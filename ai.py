#modules imported
import os
import json
import requests
from datetime import datetime

HISTORY_FILE = "ai_analysis_history.json"

def save_history(barcode: str, product_name: str, ai_result: str):
    """Save the product analysis to a local JSON history file."""
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M")
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    # Append new entry
    history.append({
        "barcode": barcode,
        "product_name": product_name,
        "ai_result": ai_result,
        "chat_log": [],
        "timestamp": formatted_time
    })

    # Save back to file
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
def handle_follow_up(user_question: str):
    """Handles a follow-up question about the last scanned item."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://ai.hackclub.com/proxy/v1/chat/completions"
    history = []

    # 1. Load the entire history
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                return "Error: History file is corrupted."
    
    if not history:
        return "You need to scan an item first."

    # 2. Get the most recent item for context
    last_item = history[-1]
    product_name = last_item["product_name"]
    initial_analysis = last_item["ai_result"]
    chat_log = last_item.get("chat_log", [])

    # 3. Construct the prompt with history
    messages = [
        {"role": "system", "content": f"You are a health assistant. The user is asking about '{product_name}'. Here is the initial analysis you provided: {initial_analysis}. Now answer the user's follow-up question concisely."},
    ]
    # Add previous chat messages for context
    for entry in chat_log:
        messages.append({"role": "user", "content": entry["user"]})
        messages.append({"role": "assistant", "content": entry["ai"]})
    
    # Add the new user question
    messages.append({"role": "user", "content": user_question})

    # 4. Call the AI
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"model": "x-ai/grok-4.1-fast", "messages": messages}
    
    response = requests.post(url, headers=headers, json=data, timeout=20)
    if response.status_code != 200:
        return f"AI service error ({response.status_code})."

    ai_response = response.json()["choices"][0]["message"]["content"]

    # 5. Update and save the history
    last_item["chat_log"].append({"user": user_question, "ai": ai_response})
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

    return ai_response

def ai_analysis(product_barcode: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://ai.hackclub.com/proxy/v1/chat/completions" 
    
    # Step 1: Fetch product data
    response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{product_barcode}.json")
    if response.status_code != 200:
        return f"Error fetching product data ({response.status_code})"
    
    product_data = response.json()
    product_name = product_data.get('product', {}).get('product_name', 'Unknown')
    
    # Prompt for Ai analysis
    prompt = f"""
Evaluate the health score of the following product: {product_name}.
Suggest healthier alternatives with price comparisons.
List key nutrients and their health benefits.
Look at the _keywords part of the json for more info on the product. and its name. Do not hallucinate.
Flag items with high oil, sodium, or sugar content.
Provide calorie, protein, fat, and carbohydrate information.
Highlight vitamins and minerals present and their amounts.
Indicate dietary suitability (e.g., vegan, gluten-free, low-sodium).
Suggest portion sizes for optimal health.
Warn about potential allergens.
Provide the name and brand of the item as well.
Make health score out of 100, with 100 being the healthiest. 
MAKE IT ON THE FIRST LINE OF THE RESPONSE NO MARKDOWN NO NOTHING just something out of 100 Format it like: <score> out of 100.
Show the alternatives also with a health score out of 100. (no health bars, just scores)
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "x-ai/grok-4.1-fast",
        "messages": [{"role": "user", "content": prompt}],
    }
# Step 2: Call AI service
    response = requests.post(url, headers=headers, json=data, timeout=20)
    if response.status_code != 200:
        return f"AI service error ({response.status_code}). Please try again later."

    result_text = response.json()["choices"][0]["message"]["content"]

    # Step 3: Save to history
    save_history(product_barcode, product_name, result_text)

    return result_text
