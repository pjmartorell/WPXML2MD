import streamlit as st
import xml.etree.ElementTree as ET
import zipfile
import os
import shutil
from markdownify import markdownify as md

# Set page config
st.set_page_config(
    page_title="WordPress XML to Markdown",
    page_icon="📝",
    layout="centered"
)

# Title and description
st.title("📝 WordPress XML to Markdown")
st.markdown("Convert your WordPress export XML files to clean Markdown files with ease!")

# Instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. Export your content from WordPress (Tools → Export)
    2. Upload your XML file using the uploader below
    3. Choose whether you want individual files or a single combined file
    4. Download your converted Markdown files
    """)

# Create output directory if it doesn't exist
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def cleanup_output():
    """Remove all files in output directory"""
    for filename in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            st.error(f"Error cleaning up {file_path}: {e}")

def process_xml(file):
    txt_files = []
    concatenated_content = ""

    # Parse the XML file
    try:
        # Cleanup before processing
        cleanup_output()

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

            # Save files to output directory
            filename = os.path.join(OUTPUT_DIR, f"{sanitized_title}.md")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            txt_files.append(filename)

            # Concatenate content if checkbox is checked
            concatenated_content += f"\n\n# {title}\n\n{markdown_content}"

        except Exception as e:
            st.warning(f"Error processing item {i}: {e}")
            continue  # Skip problematic items

    return txt_files, concatenated_content

# Main converter section
st.subheader("1️⃣ Upload Your WordPress XML")
uploaded_file = st.file_uploader("Choose your WordPress XML export file", type=["xml"])

if uploaded_file is not None:
    # Conversion Options
    st.subheader("2️⃣ Select Conversion Options")
    concatenate_files = st.checkbox(
        "Combine all posts into a single Markdown file",
        help="If checked, all posts will be combined into one file. Otherwise, each post will be in a separate file."
    )

    # Process button
    st.subheader("3️⃣ Convert")
    if st.button("🔄 Process XML File"):
        try:
            txt_files, concatenated_content = process_xml(uploaded_file)

            if txt_files or concatenated_content:
                st.success("✅ Conversion completed successfully!")

                # Create zip file directly in output directory
                zip_path = os.path.join(OUTPUT_DIR, "markdown_output.zip")
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    if concatenate_files:
                        if concatenated_content:
                            concatenated_filename = os.path.join(OUTPUT_DIR, "concatenated_markdown.md")
                            with open(concatenated_filename, "w", encoding="utf-8") as f:
                                f.write(concatenated_content)
                            zipf.write(concatenated_filename, "concatenated_markdown.md")
                    else:
                        for txt_file in txt_files:
                            zipf.write(txt_file, os.path.basename(txt_file))

                # Download button
                st.subheader("4️⃣ Download")
                with open(zip_path, "rb") as f:
                    st.download_button(
                        label="⬇️ Download Converted Files",
                        data=f,
                        file_name="markdown_output.zip",
                        mime="application/zip"
                    )
            else:
                st.warning("No content found to convert in the XML file.")

        except Exception as e:
            st.error(f"Error processing the file: {str(e)}")
            st.info("Please make sure you've uploaded a valid WordPress XML export file.")
        finally:
            cleanup_output()

# Footer
st.markdown("---")
st.markdown(
    "Made with ❤️ by [pjmartorell](https://twitter.com/pjmartorell) • [View Source](https://github.com/pjmartorell/WPXML2MD) • [Support me](https://github.com/sponsors/pjmartorell)"
)
