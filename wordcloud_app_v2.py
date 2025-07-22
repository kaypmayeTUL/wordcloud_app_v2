
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import re

# Updated text cleaning function from 2nd notebook
def clean_text_column(df, column_name):
    def clean_text(text):
        if pd.isnull(text):
            return ""
        text = text.lower()
        text = text.replace(" ", "-")
        text = text.replace("(", "-").replace(")", "-")
        text = text.replace("--", "_").replace("-", "_")
        text = text.replace(" _", " ")
        return text

    df[column_name] = df[column_name].apply(clean_text)
    return df

# Streamlit UI
st.title("Library Word Cloud Generator (V2)")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Preview of the uploaded file:")
    st.dataframe(df.head())

    column_name = st.selectbox("Select a column for word cloud generation", df.columns)

    if st.button("Generate Word Cloud"):
        df = clean_text_column(df, column_name)
        text = " ".join(df[column_name].dropna().tolist())

        wc = WordCloud(width=800, height=400, background_color="white").generate(text)

        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
