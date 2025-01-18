import re
import os
import nbformat
import joblib
import numpy as np
import streamlit as st
from nbconvert import HTMLExporter
from xhtml2pdf import pisa
from sklearn.ensemble import RandomForestClassifier
import logging

logging.basicConfig(level=logging.INFO)

# Initialize global model variable
model = None

# Function to load the model from an uploaded file
def load_uploaded_model(uploaded_model_file):
    try:
        return joblib.load(uploaded_model_file)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        st.stop()

# Function for prediction
def predict_penguin_sex(culmen_length, culmen_depth):
    try:
        features = np.array([[float(culmen_length), float(culmen_depth)]])
        sex_prediction = model.predict(features)[0]
        return "Male" if sex_prediction == 1 else "Female"
    except ValueError:
        return "Please enter valid numeric values."

# Function to preprocess HTML to remove problematic CSS selectors and fix encoding
def clean_html_for_pdf(html_content):
    cleaned_html = re.sub(r':not\([^\)]*\)', '', html_content)
    cleaned_html = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_html)
    cleaned_html = re.sub(r'<script.*?>.*?</script>', '', cleaned_html, flags=re.DOTALL)
    cleaned_html = re.sub(r'<style.*?>.*?</style>', '', cleaned_html, flags=re.DOTALL)
    return cleaned_html

# Function to convert .ipynb file to PDF (using HTML as intermediary)
def convert_ipynb_to_pdf(input_ipynb, output_pdf):
    try:
        with open(input_ipynb, 'r', encoding='utf-8') as f:
            notebook_content = nbformat.read(f, as_version=4)

        html_exporter = HTMLExporter()
        html_exporter.exclude_input = False  
        html_exporter.exclude_output = False  
        html_exporter.exclude_input_prompt = True  
        html_exporter.exclude_output_prompt = True  

        (body, resources) = html_exporter.from_notebook_node(notebook_content)

        custom_css = """
        <style>
            .code-cell {
                background-color: #f0f0f0; 
                padding: 10px; 
                border: 1px solid #ddd;
                color: #333;
                font-family: 'Courier New', monospace;
            }
            .text-cell {
                background-color: #e0f7fa;
                padding: 10px;
                border: 1px solid #ddd;
                color: #000;
                font-family: Arial, sans-serif;
            }
            .output-cell {
                background-color: #f9f9f9;
                padding: 10px;
                border: 1px solid #ddd;
                color: #000;
                font-family: 'Courier New', monospace;
            }
        </style>
        """

        body = custom_css + body
        cleaned_html = clean_html_for_pdf(body)

        html_output = "temp_output.html"
        with open(html_output, 'w', encoding='utf-8') as f:
            f.write(cleaned_html)

        with open(html_output, "r") as html_file:
            with open(output_pdf, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(html_file, dest=pdf_file)

        if pisa_status.err:
            return f"Error: {pisa_status.err}"
        return output_pdf

    except Exception as e:
        return f"An error occurred: {e}"

# Function to convert .py file to PDF
def convert_py_to_pdf(input_py, output_pdf):
    try:
        with open(input_py, 'r', encoding='utf-8') as f:
            py_content = f.read()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    background-color: #f0f0f0;
                    padding: 20px;
                }}
                pre {{
                    white-space: pre-wrap;
                }}
            </style>
        </head>
        <body>
            <pre>{py_content}</pre>
        </body>
        </html>
        """

        html_output = "temp_output.html"
        with open(html_output, 'w', encoding='utf-8') as f:
            f.write(html_content)

        with open(html_output, "r") as html_file:
            with open(output_pdf, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(html_file, dest=pdf_file)

        if pisa_status.err:
            return f"Error: {pisa_status.err}"
        return output_pdf

    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit UI for penguin sex prediction and file conversion
def main():
    global model
    st.title('Penguin Sex Predictor & IPYNB/PY to PDF Converter')
    st.markdown("""
        **Penguin Sex Predictor:**  
        Predict the sex of a penguin based on its culmen length and depth.  
        **Steps:**  
        1. Upload your model file (.joblib).  
        2. Input culmen measurements.  
        3. Get the prediction!

        **IPYNB/PY to PDF Converter:**  
        Upload a Jupyter Notebook file (.ipynb) or Python file (.py), and the app will convert it into a styled PDF.
        For Python files, only the code will be converted without styling for cells.
    """)

    # Model upload for penguin sex prediction
    uploaded_model_file = st.file_uploader("Upload a Trained Model File (.joblib)", type=["joblib"])
    if uploaded_model_file is not None:
        st.write("Model uploaded successfully!")
        model = load_uploaded_model(uploaded_model_file)

    # Check if the model is loaded
    if model is not None:
        # User inputs for penguin features
        culmen_length = st.text_input("Culmen Length (mm)", "0.0")
        culmen_depth = st.text_input("Culmen Depth (mm)", "0.0")

        if st.button('Predict Penguin Sex'):
            if culmen_length and culmen_depth:
                result = predict_penguin_sex(culmen_length, culmen_depth)
                st.write(f"**Prediction:** {result}")
            else:
                st.write("Please fill in all fields.")
    else:
        st.warning("Please upload a model file for penguin sex prediction.")

    # File conversion section
    st.header("IPYNB and PY to PDF Converter")
    uploaded_file = st.file_uploader("Choose a file", type=["ipynb", "py"])

    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        # Use the original file name to avoid path issues
        input_file = uploaded_file.name
        
        # Save the uploaded file
        with open(input_file, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("File uploaded successfully!")

        if file_type == "ipynb":
            output_pdf = input_file.replace('.ipynb', '.pdf')
            result = convert_ipynb_to_pdf(input_file, output_pdf)
        elif file_type == "py":
            output_pdf = input_file.replace('.py', '.pdf')
            result = convert_py_to_pdf(input_file, output_pdf)
        else:
            st.error("Unsupported file type.")
            return

        if isinstance(result, str) and result.endswith(".pdf"):
            st.success("Conversion successful!")
            with open(result, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name=result,
                    mime="application/pdf"
                )
        else:
            st.error(f"Error: {result}")

if __name__ == "__main__":
    main()
