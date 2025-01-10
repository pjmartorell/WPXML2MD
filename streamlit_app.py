import streamlit as st
import xml.etree.ElementTree as ET
import zipfile
import os
import shutil
import unicodedata
from markdownify import markdownify as md

# Set wider layout
st.set_page_config(
    page_title="WordPress XML to Markdown",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': 'https://wpxml2md.featurebase.app/',
        'About': '''
        Convert your WordPress export XML files to clean Markdown format.

        [![GitHub](https://img.shields.io/github/sponsors/pjmartorell?label=Sponsor&logo=GitHub)](https://github.com/sponsors/pjmartorell)
        [![Liberapay](https://img.shields.io/liberapay/receives/pj.martorell.svg?logo=liberapay)](https://liberapay.com/pj.martorell/donate)

        Made with ❤️ by [pjmartorell](https://github.com/pjmartorell)

        Have feedback? Visit [wpxml2md.featurebase.app](https://wpxml2md.featurebase.app/)
        '''
    }
)

# Sidebar with instructions and settings
with st.sidebar:
    st.title("⚙️ Settings & How-To")

    with st.expander("📖 How to Use", expanded=True):
        st.markdown("""
        1. Export your content from WordPress (Tools → Export)
        2. Upload your XML file(s) below
        3. Configure conversion options
        4. Click Process and download results
        """)

    with st.expander("🛠️ Advanced Options"):
        st.markdown("### Conversion Settings")
        heading_style = st.selectbox(
            "Heading Style",
            ["ATX (#)", "Setext (===)"],
            help="Choose the style for markdown headings"
        )

        preserve_linebreaks = st.checkbox(
            "Preserve Line Breaks",
            value=True,
            help="Keep original line breaks from WordPress"
        )

        remove_empty = st.checkbox(
            "Skip Empty Content",
            value=True,
            help="Skip posts/pages with no meaningful content"
        )

# Main content area
st.title("📝 WordPress XML to Markdown")
st.markdown("Convert your WordPress export XML files to clean Markdown files with ease!")

# Create two columns for upload and options
col1, col2 = st.columns([2, 1], gap="medium")

with col1:
    st.subheader("1️⃣ Upload Files")
    uploaded_files = st.file_uploader(
        "Drop your WordPress XML export file(s) here",
        type=["xml"],
        accept_multiple_files=True,
        help="You can upload multiple XML files at once"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

with col2:
    st.subheader("2️⃣ Output Format")
    concatenate_files = st.radio(
        "Choose output format",
        ["Individual Markdown Files", "Single Combined File"],
        help="Choose how you want your posts/pages to be organized"
    )

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

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to handle special characters"""
    # Normalize unicode characters
    normalized = unicodedata.normalize('NFKD', filename)
    # Remove diacritics and convert to ASCII
    ascii_text = normalized.encode('ASCII', 'ignore').decode('ASCII')
    # Replace spaces and other special chars
    sanitized = ''.join(c for c in ascii_text if c.isalnum() or c in (' ', '-', '_', '.'))
    return sanitized.strip()

def process_xml(file, heading_style="ATX", preserve_linebreaks=True, remove_empty=True):
    txt_files = []
    concatenated_content = ""
    used_filenames = set()  # Track used filenames

    try:
        cleanup_output()
        tree = ET.parse(file)
        root = tree.getroot()
    except Exception as e:
        st.error(f"Error parsing XML: {e}")
        return [], "", 0, 0

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
            markdown_content = md(content, heading_style=heading_style)

            # Enhanced empty content check
            if remove_empty and is_content_empty(markdown_content):
                skipped_count += 1
                st.warning(f"Skipping empty content: {title}")
                continue

            # Sanitize title and ensure unique filename
            sanitized_title = sanitize_filename(''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip())
            if not sanitized_title:
                sanitized_title = f"untitled_{i}"

            base_filename = f"{sanitized_title}.md"
            unique_filename = get_unique_filename(base_filename, used_filenames)
            used_filenames.add(unique_filename)

            # Save non-empty files to output directory with unique name
            filepath = os.path.join(OUTPUT_DIR, unique_filename)
            filepath = os.path.abspath(filepath)  # Get absolute path
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

    return txt_files, concatenated_content, processed_count, skipped_count

def generate_and_offer_download(txt_files, concatenated_content, is_single_file):
    """Generate zip file and create download button"""
    zip_path = os.path.join(OUTPUT_DIR, "markdown_output.zip")

    with zipfile.ZipFile(zip_path, "w") as zipf:
        if is_single_file:
            if concatenated_content:
                concatenated_filename = os.path.join(OUTPUT_DIR, "concatenated_markdown.md")
                with open(concatenated_filename, "w", encoding="utf-8") as f:
                    f.write(concatenated_content)
                zipf.write(concatenated_filename, "concatenated_markdown.md")
        else:
            for txt_file in txt_files:
                if os.path.exists(txt_file):
                    safe_name = sanitize_filename(os.path.basename(txt_file))
                    zipf.write(txt_file, safe_name)

    # Create download button
    with open(zip_path, "rb") as f:
        st.download_button(
            label="⬇️ Download Converted Files",
            data=f,
            file_name="markdown_output.zip",
            mime="application/zip"
        )

# Process section
if uploaded_files:
    st.subheader("3️⃣ Process Files")

    # Stats containers
    stats_col1, stats_col2, stats_col3 = st.columns(3)
    with stats_col1:
        files_counter = st.empty()
    with stats_col2:
        progress_counter = st.empty()
    with stats_col3:
        time_counter = st.empty()

    if st.button("🔄 Convert to Markdown", use_container_width=True):
        try:
            all_txt_files = []
            all_concatenated_content = ""
            total_processed = 0
            total_skipped = 0

            # Main progress bar
            progress_text = "Overall Progress"
            main_progress_bar = st.progress(0, text=progress_text)

            for idx, xml_file in enumerate(uploaded_files):
                try:
                    with st.status(f"Processing {xml_file.name}...", expanded=True) as status:
                        txt_files, concatenated_content, processed, skipped = process_xml(
                            xml_file,
                            heading_style="ATX" if heading_style == "ATX (#)" else "SETEXT",
                            preserve_linebreaks=preserve_linebreaks,
                            remove_empty=remove_empty
                        )

                        all_txt_files.extend(txt_files)
                        all_concatenated_content += concatenated_content
                        total_processed += processed
                        total_skipped += skipped
                        main_progress_bar.progress((idx + 1) / len(uploaded_files))
                        status.update(label=f"✅ Completed {xml_file.name}", state="complete")

                except Exception as e:
                    st.error(f"Error processing {xml_file.name}: {str(e)}")

            if all_txt_files or all_concatenated_content:
                st.success("🎉 Conversion completed successfully!")

                # Download section
                st.subheader("4️⃣ Download Results")

                # Create download options
                download_col1, download_col2 = st.columns(2)
                with download_col1:
                    # Create and offer zip download
                    generate_and_offer_download(
                        all_txt_files,
                        all_concatenated_content,
                        concatenate_files == "Single Combined File"
                    )
                with download_col2:
                    st.info("📊 Conversion Summary\n"
                           f"- Files Processed: {len(uploaded_files)}\n"
                           f"- Contents Converted: {total_processed}\n"
                           f"- Contents Skipped: {total_skipped}")
            else:
                st.warning("⚠️ No content found to convert in the XML files.")

        except Exception as e:
            st.error(f"❌ Error during conversion: {str(e)}")
            st.info("Please make sure you've uploaded valid WordPress XML export files.")

# Footer
st.markdown("---")
sponsor_html = """
<div style="display: flex; flex-direction: column; gap: 10px; align-items: center;">
    <span>Made with ❤️ by <a href="https://twitter.com/pjmartorell">pjmartorell</a></span>
    <div style="display: flex; align-items: center; gap: 10px;">
        <a href="https://liberapay.com/pj.martorell/donate">
            <img alt="Donate using Liberapay" src="https://liberapay.com/assets/widgets/donate.svg" height="32" style="border: 0;">
        </a>
        <span>•</span>
        <iframe src="https://github.com/sponsors/pjmartorell/button" title="Sponsor pjmartorell" height="32" width="114" style="border: 0; border-radius: 6px;"></iframe>
        <span>•</span>
        <a href='https://ko-fi.com/F1F818PV95' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi6.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
    </div>
</div>
"""
st.markdown(sponsor_html, unsafe_allow_html=True)
