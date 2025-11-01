import streamlit as st
from PyPDF2 import PdfReader

st.set_page_config(page_title="ATDW PDF Field Inspector", layout="wide")

st.title("🕵️ Across a Thousand Dead Worlds – PDF Field Inspector")

pdf_path = "Blank Character Sheet with fields.pdf"

try:
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()

    if fields:
        st.success(f"✅ Found {len(fields)} form fields in '{pdf_path}'")
        field_names = sorted(fields.keys())
        st.write("### Field Names Found:")
        st.dataframe({"Field Name": field_names})
    else:
        st.warning("⚠️ No form fields found in this PDF.")
except FileNotFoundError:
    st.error(f"❌ Could not find PDF file: '{pdf_path}'")
except Exception as e:
    st.error(f"⚠️ Error reading PDF: {e}")
