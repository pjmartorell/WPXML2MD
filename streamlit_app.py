import streamlit as st
import xml.etree.ElementTree as ET
import os
import zipfile
from markdownify import markdownify as md

def process_xml(uploaded_file, concatenate=False):
    """Process the XML file and convert its content to Markdown."""
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    namespace = {"wp": "http://wordpress.org/export/1.2/"}
    items = root.findall("./channel/item")
    txt_files = []
    concatenated_content = ""

    for item in items:
        title = item.find("title").text
        content_encoded = item.find("wp:post_content", namespace)
        content = content_encoded.text if content_encoded is not None else None

        if content is None:
            continue  # Skip items with no content

        # Sanitize the title for a valid filename
        sanitized_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{sanitized_title}.md"

        # Convert HTML content to Markdown
        markdown_content = md(content)
        
        if concatenate:
            concatenated_content += f"# {title}\n\n{markdown_content}\n\n"
        else:
            # Write the content to an individual markdown file
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{markdown_content}")
            txt_files.append(filename)

    if concatenate and concatenated_content:
        # Write concatenated content to a single markdown file
        concatenated_filename = "all_pages.md"
        with open(concatenated_filename, "w", encoding="utf-8") as f:
            f.write(concatenated_content)
        txt_files.append(concatenated_filename)

    return txt_files


st.title("WordPress XML to Markdown Converter")

uploaded_file = st.file_uploader("Upload your WordPress XML file", type=["xml"])
concatenate = st.checkbox("Concatenate all Markdown files into a single file", value=False)

if uploaded_file is not None:
    txt_files = process_xml(uploaded_file, concatenate)

    if txt_files:  # Ensure there are files to process
        # Create a zip archive of the .md files
        with zipfile.ZipFile("output.zip", "w") as zipf:
            for txt_file in txt_files:
                zipf.write(txt_file)
                os.remove(txt_file)  # Clean up individual .md files after zipping

        # Download button for the zip archive
        st.download_button(
            label="Download Markdown Files (ZIP)",
            data=open("output.zip", "rb").read(),
            file_name="markdown_files.zip",
            mime="application/zip"
        )
        os.remove("output.zip")  # Clean up the zip file after download
    else:
        st.error("No valid content found in the XML file.")
