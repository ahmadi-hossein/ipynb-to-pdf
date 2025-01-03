import streamlit as st
import nbformat
from nbconvert import HTMLExporter
from xhtml2pdf import pisa
import re
import os

# Function to preprocess HTML to remove problematic CSS selectors and fix encoding
def clean_html_for_pdf(html_content):
    # Regular expression to remove any ":not(" selectors that might cause issues
    cleaned_html = re.sub(r':not\([^\)]*\)', '', html_content)
    
    # Remove non-ASCII characters or replace with a space
    cleaned_html = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_html)
    
    # Additional cleanup for other known problematic patterns (optional)
    # Remove JavaScript references (if any)
    cleaned_html = re.sub(r'<script.*?>.*?</script>', '', cleaned_html, flags=re.DOTALL)
    # Remove any inline styles (optional)
    cleaned_html = re.sub(r'<style.*?>.*?</style>', '', cleaned_html, flags=re.DOTALL)
    
    return cleaned_html

# Function to convert .ipynb file to PDF (using HTML as intermediary)
def convert_ipynb_to_pdf(input_ipynb, output_pdf):
    try:
        # Load the notebook content
        with open(input_ipynb, 'r', encoding='utf-8') as f:
            notebook_content = nbformat.read(f, as_version=4)

        # Initialize the HTMLExporter with settings to include both inputs (code) and outputs (results)
        html_exporter = HTMLExporter()
        html_exporter.exclude_input = False  # Include code cells (inputs)
        html_exporter.exclude_output = False  # Include output cells (outputs)
        html_exporter.exclude_input_prompt = True  # Optional: exclude the input prompts (In [1]:)
        html_exporter.exclude_output_prompt = True  # Optional: exclude the output prompts (Out [1]:)

        # Convert the notebook to HTML
        (body, resources) = html_exporter.from_notebook_node(notebook_content)

        # Add custom CSS for styling the code, text, and output cells
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

        # Wrap the HTML body with the custom CSS
        body = custom_css + body

        # Preprocess HTML to remove problematic parts (e.g., :not() selector)
        cleaned_html = clean_html_for_pdf(body)

        # Write the cleaned HTML to a temporary file
        html_output = "temp_output.html"
        with open(html_output, 'w', encoding='utf-8') as f:
            f.write(cleaned_html)

        # Convert HTML to PDF using xhtml2pdf
        with open(html_output, "r") as html_file:
            with open(output_pdf, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(html_file, dest=pdf_file)

        if pisa_status.err:
            return f"Error: {pisa_status.err}"
        return output_pdf

    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit UI
def main():
    st.title("IPYNB to PDF Converter by Hossein Ahmadi")
    st.markdown("""
        Upload a Jupyter Notebook file (.ipynb), and the app will convert it into a styled PDF.
        Code, text, and output cells will be separated with different background colors.
    """)

    # File upload widget
    uploaded_file = st.file_uploader("Choose a Jupyter Notebook file", type="ipynb")

    if uploaded_file is not None:
        # Save the uploaded file to disk
        input_ipynb = "uploaded_notebook.ipynb"
        with open(input_ipynb, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("File uploaded successfully!")

        # Convert the .ipynb to PDF
        output_pdf = input_ipynb.replace('.ipynb', '.pdf')
        result = convert_ipynb_to_pdf(input_ipynb, output_pdf)

        if isinstance(result, str) and result.endswith(".pdf"):
            st.success("Conversion successful!")
            with open(output_pdf, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name=output_pdf,
                    mime="application/pdf"
                )
        else:
            st.error(f"Error: {result}")

if __name__ == "__main__":
    main()