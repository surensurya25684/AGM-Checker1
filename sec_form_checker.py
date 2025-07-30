import streamlit as st
import pandas as pd
import io

# === Title ===
st.title("📊 Excel File Comparator")
st.markdown("Upload two Excel files to compare values in:")
st.markdown("- `DMX_ISSUER_NAME`")
st.markdown("- `DMX_ISSUER_ID`")
st.markdown("- `SHPPROPOSALTEXT`")

# === File Upload ===
file1 = st.file_uploader("Upload First Excel File", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx", "xls"])

# === Columns to Compare ===
key_columns = ['DMX_ISSUER_NAME', 'DMX_ISSUER_ID', 'SHPPROPOSALTEXT']

def load_and_prepare(file):
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    df = df[[col for col in df.columns if col in key_columns]].copy()
    for col in key_columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def find_mismatches(df1, df2):
    merged = pd.merge(df1, df2, on='DMX_ISSUER_ID', how='outer', suffixes=('_FILE1', '_FILE2'), indicator=True)

    mismatch_records = []

    for _, row in merged.iterrows():
        issuer_id = row.get('DMX_ISSUER_ID')
        name1 = row.get('DMX_ISSUER_NAME_FILE1', '')
        name2 = row.get('DMX_ISSUER_NAME_FILE2', '')

        for col in ['DMX_ISSUER_NAME', 'SHPPROPOSALTEXT']:
            val1 = row.get(f"{col}_FILE1", "")
            val2 = row.get(f"{col}_FILE2", "")

            if pd.notna(val1) and pd.notna(val2) and val1.strip() != val2.strip():
                mismatch_records.append({
                    "DMX_ISSUER_ID": issuer_id,
                    "DMX_ISSUER_NAME": name1 if name1 else name2,
                    "MISMATCHED_COLUMN": col,
                    "VALUE_IN_FILE1": val1,
                    "VALUE_IN_FILE2": val2
                })

    return pd.DataFrame(mismatch_records)

# === Main Logic ===
if file1 and file2:
    try:
        df1 = load_and_prepare(file1)
        df2 = load_and_prepare(file2)

        mismatch_df = find_mismatches(df1, df2)

        if not mismatch_df.empty:
            st.success(f"✅ {len(mismatch_df)} mismatched values found.")
            st.dataframe(mismatch_df)

            # Downloadable Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                mismatch_df.to_excel(writer, index=False)
            output.seek(0)

            st.download_button(
                label="📥 Download Detailed Mismatch Report",
                data=output,
                file_name="detailed_mismatch_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("✅ No mismatches found!")

    except Exception as e:
        st.error(f"❌ Error: {e}")
