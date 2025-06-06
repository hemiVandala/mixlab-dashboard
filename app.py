import streamlit as st

st.set_page_config(page_title="MixLab Dashboard", layout="wide", page_icon="🧪")

st.title("🧪 MixLab Dashboard")
st.markdown("Welcome to your personal eLiquid lab — all your tools in one place.")

# Tabs for Tools
tabs = st.tabs([
    "📖 Recipes", "🧂 Flavor Stash", "⏳ Steep Timers", 
    "🧠 VapeSim AI", "🔥 Synergy Heatmap", 
    "🧬 Recipe Diff Tool", "⚡ Quick Mix Assistant"
])

with tabs[0]:
    st.subheader("📖 Recipes")
    st.info("View, edit, and analyze your saved recipes.")
    st.button("Open Recipes")

with tabs[1]:
    st.subheader("🧂 Flavor Stash")
    st.info("Manage your concentrate inventory.")
    st.button("Edit Flavor Stash")

with tabs[2]:
    st.subheader("⏳ Steep Timers")
    st.info("Track steep times and readiness.")
    st.button("Launch Steep Timers")

with tabs[3]:
    st.subheader("🧠 VapeSim AI")
    st.info("Predictive flavor interaction and steep projections.")
    st.button("Run VapeSim AI")

with tabs[4]:
    st.subheader("🔥 Synergy Heatmap")
    st.info("Visualize high-synergy flavor pairs.")
    st.button("Show Heatmap")

with tabs[5]:
    st.subheader("🧬 Recipe Diff Tool")
    st.info("Compare two recipes side-by-side.")
    st.button("Compare Recipes")

with tabs[6]:
    st.subheader("⚡ Quick Mix Assistant")
    st.info("Rapid recipe generator using AI.")
    st.button("Start Quick Mix")
