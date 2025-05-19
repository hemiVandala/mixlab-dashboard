
import streamlit as st
import pandas as pd

st.set_page_config(page_title="MixLab Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("# MixLab Dashboard (Dark Mode)")
st.sidebar.title("Navigation")
menu = st.sidebar.radio("Go to:", ["Flavor Stash Manager", "Steep Timers", "Synergy Heatmap", "Recipe Diff Tool", "VapeSim AI", "Quick Mix Assistant"])

# Simulated flavor stash from user's memory
flavor_stash = [
    "FA Custard Premium", "INW Custard", "TFA Bavarian Cream", "NicVape Bavarian Cream",
    "NicVape Vanilla Custard", "CAP French Vanilla", "CAP Sugar Cookie", "INW Biscuit",
    "TFA Cheesecake (Graham Crust)", "TFA Strawberry Ripe", "CAP Sweet Strawberry",
    "NicVape Sweet Strawberry", "NicVape Strawberry Ripe", "TFA Vanilla Swirl",
    "TFA Vanilla Bean Ice Cream", "FW Blueberry", "FA Bilberry", "TFA Blueberry Extra",
    "FA Marshmallow", "Capella Vanilla Custard v1", "FLV Vanilla Pudding", "FA Cream Fresh",
    "INW Strawberry Shisha", "CAP New York Cheesecake", "WF Glazed Donut SC"
]

if menu == "Flavor Stash Manager":
    st.subheader("Your Flavor Stash")
    df = pd.DataFrame({"Flavor Name": flavor_stash})
    st.dataframe(df)

elif menu == "Steep Timers":
    st.subheader("Steep Timers")
    st.info("Coming soon: add and track steep timers for each recipe.")

elif menu == "Synergy Heatmap":
    st.subheader("Flavor Synergy Heatmap")
    st.info("Coming soon: visualize pairwise flavor synergy scores.")

elif menu == "Recipe Diff Tool":
    st.subheader("Recipe Diff Tool")
    st.info("Coming soon: compare any two eLiquid recipes side by side.")

elif menu == "VapeSim AI":
    st.subheader("VapeSim AI")
    st.info("Coming soon: Predictive analysis of recipe performance, balance, and steep curve.")

elif menu == "Quick Mix Assistant":
    st.subheader("Quick Mix Assistant")
    st.info("Coming soon: Enter a flavor or profile and get instant recipe suggestions.")
