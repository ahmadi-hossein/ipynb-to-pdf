import streamlit as st
import nbformat
from nbconvert import HTMLExporter
from xhtml2pdf import pisa
import re
import os

# Function to preprocess HTML to remove problematic CSS selectors and fix encoding
def clean_html_for_pdf(html_content):
    cleaned_html = re.sub(r':not\([^\)]*\)', '', html_content)
    cleaned_html = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_html)
    cleaned_html = re.sub(r'<script.*?>.*?</script>', '', cleaned_html, flags=re.DOTALL)
    cleaned_html = re.sub(r'<style.*?>.*?</style>', '', cleaned_html, flags=re.DOTALL)
    return cleaned_html

# Function to convert Python (.py) file to PDF, preserving HTML tags
def convert_py_to_pdf(input_py, output_pdf):
    try:
        # Read the .py file content
        with open(input_py, 'r', encoding='utf-8') as f:
            py_content = f.read()

        # Wrap Python code in HTML, treating HTML tags in the code as valid
        html_content = f"""
        <html>
        <head>
        <style>
            body {{
                font-family: 'Courier New', monospace;
                background-color: #f9f9f9;
                color: #333;
                line-height: 1.5;
            }}
            pre {{
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                padding: 10px;
                overflow-x: auto;
            }}
            .rendered-html {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                padding: 10px;
            }}
        </style>
        </head>
        <body>
        <h1>Python Script with HTML Content</h1>
        <div class="rendered-html">{py_content}</div>
        </body>
        </html>
        """

        # Clean the HTML content
        cleaned_html = clean_html_for_pdf(html_content)

        # Convert HTML to PDF using xhtml2pdf
        with open(output_pdf, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(cleaned_html, dest=pdf_file)

        if pisa_status.err:
            return f"Error: {pisa_status.err}"
        return output_pdf

    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit UI
def main():
    st.title("File to PDF Converter by Hossein Ahmadi")
    st.markdown("""
        Upload a Jupyter Notebook file (.ipynb) or Python script file (.py), 
        and the app will convert it into a styled PDF. 
        Any HTML tags in your Python file will also be rendered correctly in the PDF.
    """)

    # File upload widget
    uploaded_file = st.file_uploader("Choose a Jupyter Notebook or Python file", type=["ipynb", "py"])

    if uploaded_file is not None:
        # Save the uploaded file to disk
        input_file = uploaded_file.name
        with open(input_file, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write(f"File '{input_file}' uploaded successfully!")

        # Determine the file type and convert accordingly
        if input_file.endswith('.ipynb'):
            output_pdf = input_file.replace('.ipynb', '.pdf')
            result = convert_ipynb_to_pdf(input_file, output_pdf)
        elif input_file.endswith('.py'):
            output_pdf = input_file.replace('.py', '.pdf')
            result = convert_py_to_pdf(input_file, output_pdf)

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
