import streamlit as st
import pandas as pd
import io

# === App Title ===
st.title("🔍 Excel File Comparator (Accurate All-Column)")
st.markdown("Upload two Excel files to compare all column values row-by-row using `DMX_ISSUER_ID` as the key.")

# === File Upload ===
file1 = st.file_uploader("Upload First Excel File", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx", "xls"])

# === Helper: Load and Normalize ===
def load_and_normalize(file):
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    df = df.applymap(lambda x: str(x).strip().lower() if pd.notnull(x) else "")
    return df

# === Main Compare Logic ===
def compare_dataframes(df1, df2, id_col="DMX_ISSUER_ID", name_col="DMX_ISSUER_NAME"):
    # Ensure required column exists
    if id_col not in df1.columns or id_col not in df2.columns:
        raise Exception(f"Missing column '{id_col}' in one or both files.")

    # Rename columns to add source suffixes
    df1 = df1.copy()
    df2 = df2.copy()
    df1.columns = [f"{col}_FILE1" for col in df1.columns]
    df2.columns = [f"{col}_FILE2" for col in df2.columns]

    # Merge on the ID column
    df_merged = pd.merge(
        df1, df2,
        left_on=f"{id_col}_FILE1", right_on=f"{id_col}_FILE2",
        how='inner', suffixes=('_FILE1', '_FILE2')
    )

    mismatches = []

    # Detect mismatched columns
    all_cols_file1 = [col for col in df1.columns if col.endswith("_FILE1")]
    for col1 in all_cols_file1:
        col_base = col1.replace("_FILE1", "")
        col2 = f"{col_base}_FILE2"

        if col2 in df_merged.columns:
            for _, row in df_merged.iterrows():
                val1 = row[col1]
                val2 = row[col2]
                if val1 != val2:
                    mismatches.append({
                        id_col: row[f"{id_col}_FILE1"],
                        name_col: row.get(f"{name_col}_FILE1", row.get(f"{name_col}_FILE2", "")),
                        "MISMATCHED_COLUMN": col_base,
                        "VALUE_IN_FILE1": val1,
                        "VALUE_IN_FILE2": val2
                    })

    return pd.DataFrame(mismatches)

# === Run App ===
if file1 and file2:
    try:
        df1 = load_and_normalize(file1)
        df2 = load_and_normalize(file2)

        mismatch_df = compare_dataframes(df1, df2)

        if not mismatch_df.empty:
            st.success(f"✅ {len(mismatch_df)} mismatches found.")
            st.dataframe(mismatch_df)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                mismatch_df.to_excel(writer, index=False)
            output.seek(0)

            st.download_button(
                label="📥 Download Mismatch Report",
                data=output,
                file_name="final_mismatch_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("✅ No mismatches found between the files!")

    except Exception as e:
        st.error(f"❌ Error: {e}")
