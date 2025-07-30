import streamlit as st
import pandas as pd
import io

# === Title ===
st.title("🔍 Excel File Comparator (All Columns)")
st.markdown("Upload two Excel files to compare values across all columns, row-by-row based on `DMX_ISSUER_ID`.")

# === File Upload ===
file1 = st.file_uploader("Upload First Excel File", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx", "xls"])

# === Helper: Load and Normalize ===
def load_and_normalize(uploaded_file):
    df = pd.read_excel(uploaded_file, dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    df = df.applymap(lambda x: str(x).strip().lower() if pd.notnull(x) else "")
    return df

# === Helper: Compare All Columns ===
def compare_all_columns(df1, df2, id_column="DMX_ISSUER_ID", name_column="DMX_ISSUER_NAME"):
    df1 = df1.copy().fillna("").astype(str)
    df2 = df2.copy().fillna("").astype(str)

    df1.columns = df1.columns.str.strip().str.upper()
    df2.columns = df2.columns.str.strip().str.upper()

    if id_column not in df1.columns or id_column not in df2.columns:
        raise Exception(f"Missing ID column '{id_column}' in one of the files.")

    df1.set_index(id_column, inplace=True)
    df2.set_index(id_column, inplace=True)

    all_columns = sorted(set(df1.columns).union(set(df2.columns)))
    df1 = df1.reindex(columns=all_columns, fill_value="")
    df2 = df2.reindex(columns=all_columns, fill_value="")

    df1 = df1.applymap(lambda x: str(x).strip().lower())
    df2 = df2.applymap(lambda x: str(x).strip().lower())

    mismatches = []
    shared_ids = df1.index.intersection(df2.index)

    for idx in shared_ids:
        row1 = df1.loc[idx]
        row2 = df2.loc[idx]

        # Safely get name column value
        name_val = ""
        if name_column in row1 and pd.notnull(row1[name_column]):
            name_val = row1[name_column]
        elif name_column in row2 and pd.notnull(row2[name_column]):
            name_val = row2[name_column]

        for col in all_columns:
            val1 = row1.get(col, "")
            val2 = row2.get(col, "")
            if val1 != val2:
                mismatches.append({
                    id_column: idx,
                    name_column: name_val,
                    "MISMATCHED_COLUMN": col,
                    "VALUE_IN_FILE1": val1,
                    "VALUE_IN_FILE2": val2
                })

    return pd.DataFrame(mismatches)

# === Main Execution ===
if file1 and file2:
    try:
        df1 = load_and_normalize(file1)
        df2 = load_and_normalize(file2)

        mismatch_df = compare_all_columns(df1, df2)

        if not mismatch_df.empty:
            st.success(f"✅ Found {len(mismatch_df)} mismatched values.")
            st.dataframe(mismatch_df)

            # Export to Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                mismatch_df.to_excel(writer, index=False)
            output.seek(0)

            st.download_button(
                label="📥 Download Mismatch Report",
                data=output,
                file_name="all_column_mismatches.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("✅ No mismatches found!")

    except Exception as e:
        st.error(f"❌ Error: {e}")
