import streamlit as st
from PyPDF2 import PdfReader

st.set_page_config(page_title="ATDW PDF Field Inspector", layout="wide")

st.title("🕵️ Across a Thousand Dead Worlds – PDF Field Inspector (Full List)")

pdf_path = "Blank Character Sheet with fields.pdf"

try:
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()

    if fields:
        field_names = sorted(fields.keys())
        st.success(f"✅ Found {len(field_names)} form fields in '{pdf_path}'")

        # Display all field names in one scrollable text box
        st.text_area(
            "All PDF Field Names:",
            value="\n".join(field_names),
            height=600
        )

        # Optional filter
        search = st.text_input("🔍 Filter field names (case-insensitive)")
        if search:
            filtered = [f for f in field_names if search.lower() in f.lower()]
            st.write(f"### Matching Fields ({len(filtered)})")
            st.write(filtered)
    else:
        st.warning("⚠️ No form fields found in this PDF.")
except FileNotFoundError:
    st.error(f"❌ Could not find PDF file: '{pdf_path}'")
except Exception as e:
    st.error(f"⚠️ Error reading PDF: {e}")
