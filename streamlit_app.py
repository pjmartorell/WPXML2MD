import streamlit as st
import xml.etree.ElementTree as ET
import zipfile
import os

def process_xml(file):
    txt_files = []

    # Parse the XML file
    try:
        tree = ET.parse(file)
        root = tree.getroot()
    except Exception as e:
        st.error(f"Error parsing XML: {e}")
        return []

    namespaces = {
        'content': 'http://purl.org/rss/1.0/modules/content/'
    }

    for i, item in enumerate(root.findall('.//item')):
        try:
            # Handle title
            title = item.find('title').text if item.find('title') is not None else f"untitled_{i}"
            title = title.strip() if title else f"untitled_{i}"

            # Handle content
            content = item.find('content:encoded', namespaces).text
            if content is None:
                content = "No content available."  # Default content if None

            # Sanitize title
            sanitized_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            if not sanitized_title:
                sanitized_title = f"untitled_{i}"

            # Create .txt file
            filename = f"{sanitized_title}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            txt_files.append(filename)

        except Exception as e:
            st.warning(f"Error processing item {i}: {e}")
            continue  # Skip problematic items

    return txt_files

# Streamlit UI
st.title("XML to TXT Converter")

uploaded_file = st.file_uploader("Upload an XML file", type=["xml"])

if uploaded_file is not None:
    txt_files = process_xml(uploaded_file)

    if txt_files:
        # Create a zip archive of the .txt files
        with zipfile.ZipFile("output.zip", "w") as zipf:
            for txt_file in txt_files:
                if os.path.exists(txt_file):  # Check if the file exists
                    zipf.write(txt_file)
                else:
                    st.warning(f"File not found: {txt_file}")

        # Clean up individual .txt files after zipping
        for txt_file in txt_files:
            if os.path.exists(txt_file):
                os.remove(txt_file)

        # Provide download link
        with open("output.zip", "rb") as f:
            st.download_button(
                label="Download ZIP file",
                data=f,
                file_name="output.zip",
                mime="application/zip"
            )
 
        st.success("Conversion completed!")
