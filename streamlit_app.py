import streamlit as st
import xml.etree.ElementTree as ET
import zipfile
import os

# Function to process the XML file
def process_xml(file):
    txt_files = []

    # Parse the XML file
    tree = ET.parse(file)
    root = tree.getroot()
    namespaces = {
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }

    # Extract posts/pages
    for item in root.findall('.//item'):
        title = item.find('title').text if item.find('title') is not None else "untitled"
        content = item.find('content:encoded', namespaces).text if item.find('content:encoded', namespaces) is not None else ""

        # Sanitize the title for file naming
        sanitized_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()

        # Create a .txt file for each post/page
        filename = f"{sanitized_title}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        txt_files.append(filename)

    return txt_files

# Streamlit App
st.title("WordPress XML to TXT Converter")
st.write("Upload your WordPress XML file to extract text from posts and pages into `.txt` files.")

# File uploader
uploaded_file = st.file_uploader("Upload XML File", type=["xml"])

if uploaded_file is not None:
    # Process XML file when the user uploads it
    with st.spinner("Processing XML file..."):
        txt_files = process_xml(uploaded_file)

    # Create a zip archive of the .txt files
    with zipfile.ZipFile("output.zip", "w") as zipf:
        for txt_file in txt_files:
            zipf.write(txt_file)
            os.remove(txt_file)  # Clean up individual .txt files after zipping

    # Download button for the zip archive
    with open("output.zip", "rb") as f:
        st.download_button("Download TXT Files", f, file_name="output.zip")

    st.success("Conversion completed!")
