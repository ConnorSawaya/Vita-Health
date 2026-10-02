#modules imported
import os
import requests
from datetime import datetime

MOCK_ANALYSIS = """72 out of 100.
Demo (offline) analysis — no OPENROUTER_API_KEY found, so this sample is shown instead of a live AI call.
Product: Demo Hazelnut Cocoa Spread (sample data).
- Calories ~539/100g, sugar ~56g (high), fat ~31g (high), protein ~6g.
- Flag: high sugar + palm oil; allergens: milk, hazelnut, soy.
- Healthier swap: no-added-sugar nut butter (score ~85/100).
- Portion tip: 15g serving. Add OPENROUTER_API_KEY in .env for live analysis."""

def add_scan_to_history(history: list[dict], barcode: str, product_name: str, ai_result: str) -> dict:
    """Keep a scan in the caller's session-owned history list."""
    item = {
        "barcode": barcode,
        "product_name": product_name,
        "ai_result": ai_result,
        "chat_log": [],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    history.insert(0, item)
    return item


def handle_follow_up(user_question: str, history: list[dict]):
    """Handles a follow-up question about the last scanned item."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return "Offline demo mode: add OPENROUTER_API_KEY in .env for live follow-ups."
    url = "https://ai.hackclub.com/proxy/v1/chat/completions"
    if not history:
        return "You need to scan an item first."

    # The Streamlit caller passes only the current visitor's session history.
    last_item = history[0]
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
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
    except Exception as e:
        return f"AI service unreachable (offline?): {e}"
    if response.status_code != 200:
        return f"AI service error ({response.status_code})."

    ai_response = response.json()["choices"][0]["message"]["content"]

    # Keep the conversation in this visitor's session-owned history only.
    last_item["chat_log"].append({"user": user_question, "ai": ai_response})
    return ai_response


def ai_analysis(product_barcode: str, history: list[dict]) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    url = "https://ai.hackclub.com/proxy/v1/chat/completions" 

    if not product_barcode or not str(product_barcode).strip():
        return "Empty barcode. Scan an item or use the demo button."
    
    # Step 1: Fetch product data
    try:
        response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{product_barcode}.json", timeout=15)
    except Exception as e:
        add_scan_to_history(history, str(product_barcode), "Unknown (offline)", MOCK_ANALYSIS)
        return MOCK_ANALYSIS + f" (network unreachable: {e})"
    if response.status_code != 200:
        add_scan_to_history(history, str(product_barcode), "Unknown (lookup blocked offline)", MOCK_ANALYSIS)
        return MOCK_ANALYSIS + f" (product lookup HTTP {response.status_code}; showing demo analysis)"
    
    try:
        product_data = response.json()
    except Exception:
        add_scan_to_history(history, str(product_barcode), "Unknown (bad lookup response)", MOCK_ANALYSIS)
        return MOCK_ANALYSIS + " (lookup response unreadable; showing demo analysis)"
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
    if not api_key:
        add_scan_to_history(history, str(product_barcode), product_name, MOCK_ANALYSIS)
        return MOCK_ANALYSIS
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
    except Exception as e:
        add_scan_to_history(history, str(product_barcode), product_name, MOCK_ANALYSIS)
        return MOCK_ANALYSIS + f" (network unreachable: {e})"
    if response.status_code != 200:
        return f"AI service error ({response.status_code}). Please try again later."

    result_text = response.json()["choices"][0]["message"]["content"]

    add_scan_to_history(history, product_barcode, product_name, result_text)

    return result_text
