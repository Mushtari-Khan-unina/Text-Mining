import spacy
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
import docx
import pdfplumber
import requests
from bs4 import BeautifulSoup
from graphviz import Digraph

nlp = spacy.load("en_core_web_sm")

def extract_text_from_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        text = ' '.join([p.text for p in soup.find_all('p')])
        return text
    except Exception as e:
        return f"Error fetching content from URL: {str(e)}"

def extract_entities_with_ner_model(text):
    doc = nlp(text[:6000])
    return [(ent.text, ent.label_) for ent in doc.ents]

def extract_entity_pairs(doc):
    entity_pairs = [
        (subj.text, obj.text)
        for token in doc
        if token.dep_ in {"ROOT", "conj", "relcl", "xcomp", "ccomp", "acomp"}
        for subj in (w for w in token.lefts if w.dep_ in {"subj", "nsubj", "nsubjpass"})
        for obj in (
            w for w in token.rights if w.dep_ in {"dobj", "attr", "prep", "pobj"}
        )
    ]
    return entity_pairs

def build_flowchart(text):
    start_time = time.time()
    doc = nlp(text)
    entity_pairs = extract_entity_pairs(doc)
    dot = Digraph()
    for subj, obj in entity_pairs:
        dot.node(subj)
        dot.node(obj)
        dot.edge(subj, obj)
    processing_time = time.time() - start_time
    return dot, processing_time

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages])

def main():
    _author_ = "https://www.linkedin.com/in/sahir-maharaj/"

    st.title("Wordlit.net")
    st.markdown(
        """
        This tool uses NLP to generate a flowchart from the text you provide.\n
        Enter any text or upload a file and hit the '**Generate**' button to visualize the connections between entities.
        
        All code contributed by [Sahir Maharaj](%s) is licensed under Attribution 4.0 International
        """
        % _author_
    )

    tab1, tab2, tab3 = st.tabs(["Upload a File", "Enter Text Manually", "Website URL"])
    user_input = None

    with tab1:
        uploaded_file = st.file_uploader("Upload a file", type=["txt", "docx", "pdf"])
        generate_file_input = st.button("Generate Flowchart from File")

    with tab2:
        text_input = st.text_area(
            "Text Input", height=150, placeholder="Paste your text here..."
        )
        generate_text_input = st.button("Generate Flowchart from Text")
    
    with tab3:
        url_input = st.text_input("Website URL", placeholder="Enter the website URL here...")
        generate_url_input = st.button("Generate Flowchart from Website")
    
    user_input = None

    if generate_file_input and uploaded_file is not None:
        file_type = uploaded_file.type
        if file_type == "text/plain":
            user_input = str(uploaded_file.read(), "utf-8")
        elif file_type == "application/pdf":
            user_input = extract_text_from_pdf(uploaded_file)
        elif (
            file_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            user_input = extract_text_from_docx(uploaded_file)
    elif generate_text_input:
        user_input = text_input
    
    if generate_url_input and url_input:
        user_input = extract_text_from_website(url_input)
    
    if user_input:
        st.session_state.user_input = user_input

    if user_input:
        user_input = st.session_state.get("user_input", None)
        if user_input:
            with st.spinner("Generating Flowchart..."):
                try:
                    dot, processing_time = build_flowchart(user_input)
                    st.graphviz_chart(dot.source)

                    st.write(f"Processing Time: {processing_time:.2f} seconds")

                except Exception as e:
                    st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
