import streamlit as st
import xml.etree.ElementTree as ET
import zipfile
import os
from markdownify import markdownify as md

def process_xml(file):
    txt_files = []
    concatenated_content = ""

    # Parse the XML file
    try:
        tree = ET.parse(file)
        root = tree.getroot()
    except Exception as e:
        st.error(f"Error parsing XML: {e}")
        return [], ""

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
                # Skip items with no content
                # st.warning(f"Skipping item {i}: Content is None")
                continue

            # Convert HTML to Markdown using markdownify
            markdown_content = md(content, heading_style="ATX")  # Use ATX-style headings (#)

            # Sanitize title
            sanitized_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            if not sanitized_title:
                sanitized_title = f"untitled_{i}"

            # Create .md file for individual files
            filename = f"{sanitized_title}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            txt_files.append(filename)

            # Concatenate content if checkbox is checked
            concatenated_content += f"\n\n# {title}\n\n{markdown_content}"

        except Exception as e:
            st.warning(f"Error processing item {i}: {e}")
            continue  # Skip problematic items

    return txt_files, concatenated_content

# Streamlit UI
st.title("XML to Markdown Converter")

uploaded_file = st.file_uploader("Upload an XML file", type=["xml"])

# Option to concatenate all Markdown files
concatenate_files = st.checkbox("Concatenate all Markdown files into a single file")

if uploaded_file is not None:
    txt_files, concatenated_content = process_xml(uploaded_file)

    # Create a zip archive of the .md files
    with zipfile.ZipFile("output.zip", "w") as zipf:
        if concatenate_files:
            # Add only the concatenated markdown to the zip
            if concatenated_content:
                concatenated_filename = "concatenated_markdown.md"
                with open(concatenated_filename, "w", encoding="utf-8") as f:
                    f.write(concatenated_content)
                zipf.write(concatenated_filename)
                os.remove(concatenated_filename)  # Clean up concatenated file
        else:
            # Add individual .md files to zip if concatenation is not enabled
            for txt_file in txt_files:
                if os.path.exists(txt_file):  # Check if the file exists
                    zipf.write(txt_file)
                    os.remove(txt_file)  # Clean up individual files after adding them to the zip

    # Provide download link
    with open("output.zip", "rb") as f:
        st.download_button(
            label="Download ZIP file",
            data=f,
            file_name="output.zip",
            mime="application/zip"
        )
