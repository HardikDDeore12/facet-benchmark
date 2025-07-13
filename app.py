import streamlit as st
import pandas as pd
import requests
import re

# === INITIAL EMPTY HEADERS ===
HEADERS = {
    "Authorization": "",
    "HTTP-Referer": "https://openrouter.ai",
    "Content-Type": "application/json"
}

MODEL = "mistralai/mixtral-8x7b-instruct"

# === HELPER FUNCTION ===
def score_facet_with_confidence(bot_response, facet):
    prompt = (
        f"You are evaluating the assistant's response for the facet: '{facet}'.\n"
        f"Rate it from 1 (very poor) to 5 (excellent). Then state your confidence as High, Medium, or Low.\n\n"
        f"Response: \"{bot_response}\"\n\n"
        f"Answer format: Score: <1-5>, Confidence: <High/Medium/Low>"
    )

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=HEADERS,
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
        return 3, "Medium"

# === STREAMLIT UI ===
st.set_page_config(page_title="Facet Scoring App", layout="wide")
st.title("🔍 Facet Scoring Benchmark (OpenRouter + Mixtral)")

api_input = st.text_input("🔑 Enter your OpenRouter API Key:", type="password")

if api_input:
    HEADERS["Authorization"] = f"Bearer {api_input}"

uploaded_file = st.file_uploader("📤 Upload Cleaned Conversation CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File loaded successfully!")
    facet = st.selectbox("🎯 Select a facet to score", options=[
        "Clarity", "Helpfulness", "Emotionalism", "Toxicity",
        "Politeness", "Common-sense", "Empathy", "Sarcasm",
        "Naivety", "Safety"
    ])
    
    if st.button("🔁 Run Scoring"):
        scores = []
        confidences = []

        with st.spinner("Scoring in progress..."):
            for i, row in df.iterrows():
                bot_response = row["Bot_Response"]
                score, conf = score_facet_with_confidence(bot_response, facet)
                scores.append(score)
                confidences.append(conf)

        df[facet] = scores
        df[f"{facet}_confidence"] = confidences

        st.success("✅ Scoring complete!")
        st.dataframe(df.head())

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Scored CSV",
            csv,
            f"Scored_{facet}.csv",
            "text/csv",
            key='download-csv'
        )
