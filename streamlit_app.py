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

def is_content_empty(content: str) -> bool:
    """Check if markdown content is effectively empty"""
    # Remove common markdown characters and whitespace
    cleaned = content.replace('#', '').replace('-', '').replace('*', '').strip()
    # Check if there's any meaningful content left
    return not cleaned or cleaned.isspace()

def get_unique_filename(base_filename: str, used_filenames: set) -> str:
    """Generate a unique filename by adding a counter if needed"""
    if base_filename not in used_filenames:
        return base_filename

    # Split filename and extension
    name, ext = os.path.splitext(base_filename)
    counter = 1

    # Keep trying until we find an unused name
    while True:
        new_name = f"{name}_{counter}{ext}"
        if new_name not in used_filenames:
            return new_name
        counter += 1

def process_xml(file):
    txt_files = []
    concatenated_content = ""
    used_filenames = set()  # Track used filenames

    try:
        cleanup_output()
        tree = ET.parse(file)
        root = tree.getroot()
    except Exception as e:
        st.error(f"Error parsing XML: {e}")
        return [], ""

    # Add counter for processed files
    processed_count = 0
    skipped_count = 0

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
                continue

            # Convert HTML to Markdown using markdownify
            markdown_content = md(content, heading_style="ATX")

            # Enhanced empty content check
            if is_content_empty(markdown_content):
                skipped_count += 1
                st.warning(f"Skipping empty content: {title}")
                continue

            # Sanitize title and ensure unique filename
            sanitized_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            if not sanitized_title:
                sanitized_title = f"untitled_{i}"

            base_filename = f"{sanitized_title}.md"
            unique_filename = get_unique_filename(base_filename, used_filenames)
            used_filenames.add(unique_filename)

            # Save non-empty files to output directory with unique name
            filepath = os.path.join(OUTPUT_DIR, unique_filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            txt_files.append(filepath)
            processed_count += 1

            # Use original title for concatenated content
            concatenated_content += f"\n\n# {title}\n\n{markdown_content}"

        except Exception as e:
            st.warning(f"Error processing item {i}: {e}")
            skipped_count += 1
            continue

    # Show processing summary
    if processed_count > 0:
        st.info(f"Successfully processed {processed_count} files" +
                (f" (skipped {skipped_count} empty files)" if skipped_count > 0 else ""))

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
