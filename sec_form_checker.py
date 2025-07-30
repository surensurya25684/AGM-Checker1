import streamlit as st
import pandas as pd
import io

# === Title ===
st.title("📊 Excel File Comparison Tool")
st.markdown("Upload two Excel files to compare based on:")
st.markdown("- `DMX_ISSUER_NAME`")
st.markdown("- `DMX_ISSUER_ID`")
st.markdown("- `SHPPROPOSALTEXT`")

# === File Upload ===
file1 = st.file_uploader("Upload First Excel File", type=["xlsx", "xls"], key="file1")
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx", "xls"], key="file2")

# === Columns to Compare ===
key_columns = ['DMX_ISSUER_NAME', 'DMX_ISSUER_ID', 'SHPPROPOSALTEXT']

def load_and_prepare(uploaded_file):
    df = pd.read_excel(uploaded_file, dtype=str)
    df.columns = df.columns.str.strip().str.upper()

    df = df[[col for col in df.columns if col in key_columns]].copy()

    for col in key_columns:
        df[col] = df[col].astype(str).str.strip().str.upper()

    return df

# === Comparison Logic ===
if file1 and file2:
    try:
        df1 = load_and_prepare(file1)
        df2 = load_and_prepare(file2)

        df1['SOURCE'] = 'File1'
        df2['SOURCE'] = 'File2'

        merged = pd.merge(df1, df2, on=key_columns, how='outer', indicator=True)
        mismatches = merged[merged['_merge'] != 'both']

        if not mismatches.empty:
            st.success(f"✅ {len(mismatches)} mismatched rows found.")
            st.dataframe(mismatches)

            # Export to Excel in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                mismatches.to_excel(writer, index=False)
            output.seek(0)

            st.download_button(
                label="📥 Download Mismatch Report",
                data=output,
                file_name="mismatch_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("✅ No mismatches found between the two files!")

    except Exception as e:
        st.error(f"❌ Error: {e}")
