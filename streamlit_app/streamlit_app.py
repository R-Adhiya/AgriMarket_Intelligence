import streamlit as st
import requests

st.set_page_config(
    page_title="AgriMarket Intelligence",
    page_icon="🌾",
    layout="wide"
)

API_URL = "http://127.0.0.1:8000"

st.title("🌾 AgriMarket Intelligence")
st.subheader("Directly from the Farm to Your Hands")

st.write(
    "A smarter agricultural marketplace connecting farmers, "
    "markets, and buyers."
)

st.divider()

st.header("Backend Connection")

try:
    response = requests.get(
        f"{API_URL}/api/health",
        timeout=5
    )

    if response.status_code == 200:
        st.success("✅ FastAPI backend is connected!")
        st.json(response.json())
    else:
        st.error(
            f"Backend returned status code: {response.status_code}"
        )

except requests.exceptions.RequestException as e:
    st.error(f"❌ Could not connect to FastAPI: {e}")