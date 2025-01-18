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
    cleaned_html = re.sub(r'<script.*?>.*?</script>', '', cleaned_html, flags=re.DOTALL)
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
        html_exporter.exclude_input = False  
        html_exporter.exclude_output = False  
        html_exporter.exclude_input_prompt = True  
        html_exporter.exclude_output_prompt = True  

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

        # Preprocess HTML to remove problematic parts
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

# Function to convert .py file to PDF
def convert_py_to_pdf(input_py, output_pdf):
    try:
        # Read the Python file content
        with open(input_py, 'r', encoding='utf-8') as f:
            py_content = f.read()

        # Simple HTML template for Python code
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

        # Write HTML to temporary file
        html_output = "temp_output.html"
        with open(html_output, 'w', encoding='utf-8') as f:
            f.write(html_content)

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
    st.title("IPYNB and PY to PDF Converter by Hossein Ahmadi")
    st.markdown("""
        Upload a Jupyter Notebook file (.ipynb) or Python file (.py), and the app will convert it into a styled PDF.
        For Python files, only the code will be converted without styling for cells.
    """)

    # File upload widget with multiple types
    uploaded_file = st.file_uploader("Choose a file", type=["ipynb", "py"])

    if uploaded_file is not None:
        file_type = uploaded_file.name.split('.')[-1].lower()
        
        if file_type == "ipynb":
            input_file = "uploaded_notebook.ipynb"
            output_pdf = "notebook.pdf"
            result = convert_ipynb_to_pdf(input_file, output_pdf)
        elif file_type == "py":
            input_file = "uploaded_script.py"
            output_pdf = "script.pdf"
            result = convert_py_to_pdf(input_file, output_pdf)
        else:
            st.error("Unsupported file type.")
            return

        # Save the uploaded file to disk
        with open(input_file, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.write("File uploaded successfully!")

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
