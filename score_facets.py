import os
import pandas as pd
import requests
import re
from tqdm import tqdm

# === Load API key from environment ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://openrouter.ai",
    "Content-Type": "application/json"
}

MODEL = "mistralai/mixtral-8x7b-instruct"

# Load dataset
df = pd.read_csv("Cleaned_Conversation_Evaluation.csv")

# Define columns
meta_cols = ["conversation_id", "turn_id", "Topic", "User_Message", "speaker_user",
             "Bot_Response", "speaker_bot", "response_length_words",
             "sentiment_score", "readability_score"]

facet_cols = [col for col in df.columns if col not in meta_cols and not col.endswith("_confidence")]

# Function to query LLM
def query_llm_with_confidence(prompt):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50,
            }
        )
        result = response.json()
        output = result["choices"][0]["message"]["content"]

        score_match = re.search(r"Score\s*[:\-]?\s*([1-5])", output)
        score = int(score_match.group(1)) if score_match else 3

        conf_match = re.search(r"Confidence\s*[:\-]?\s*(High|Medium|Low)", output, re.I)
        confidence = conf_match.group(1).capitalize() if conf_match else "Medium"

        return score, confidence

    except Exception as e:
        print("ERROR:", e)
        return 3, "Medium"

# Score all rows
for idx, row in tqdm(df.iterrows(), total=len(df)):
    bot_response = row["Bot_Response"]
    for facet in facet_cols:
        prompt = (
            f"You are evaluating the assistant's response for the facet: '{facet}'.\n"
            f"Rate it from 1 (very poor) to 5 (excellent). Then state your confidence as High, Medium, or Low.\n\n"
            f"Response: \"{bot_response}\"\n\n"
            f"Answer format: Score: <1-5>, Confidence: <High/Medium/Low>"
        )
        score, confidence = query_llm_with_confidence(prompt)
        df.at[idx, facet] = score
        df.at[idx, f"{facet}_confidence"] = confidence

# Save result
df.to_csv("Scored_Conversation_With_Confidence.csv", index=False)
print("Scoring complete. Output saved.")
