import streamlit as st
import pandas as pd
import io

# === Title ===
st.title("🔍 Excel File Comparator (All Columns)")
st.markdown("Upload two Excel files to compare all column values for matching rows.")

# === Upload Files ===
file1 = st.file_uploader("Upload First Excel File", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx", "xls"])

# === Function to Load & Normalize ===
def load_file(uploaded_file):
    df = pd.read_excel(uploaded_file, dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    df = df.applymap(lambda x: str(x).strip() if pd.notnull(x) else "")
    return df

# === Mismatch Finder ===
def compare_all_columns(df1, df2, id_column="DMX_ISSUER_ID", name_column="DMX_ISSUER_NAME"):
    df1 = df1.copy()
    df2 = df2.copy()

    df1.set_index(id_column, inplace=True)
    df2.set_index(id_column, inplace=True)

    # Align columns
    all_columns = sorted(set(df1.columns).union(set(df2.columns)))
    df1 = df1.reindex(columns=all_columns, fill_value="")
    df2 = df2.reindex(columns=all_columns, fill_value="")

    mismatches = []

    # Compare row by row
    common_ids = df1.index.intersection(df2.index)

    for idx in common_ids:
        row1 = df1.loc[idx]
        row2 = df2.loc[idx]

        for col in all_columns:
            val1 = row1[col]
            val2 = row2[col]
            if val1 != val2:
                mismatches.append({
                    id_column: idx,
                    name_column: row1.get(name_column, row2.get(name_column, "")),
                    "MISMATCHED_COLUMN": col,
                    "VALUE_IN_FILE1": val1,
                    "VALUE_IN_FILE2": val2
                })

    return pd.DataFrame(mismatches)

# === Main App Logic ===
if file1 and file2:
    try:
        df1 = load_file(file1)
        df2 = load_file(file2)

        if 'DMX_ISSUER_ID' not in df1.columns or 'DMX_ISSUER_ID' not in df2.columns:
            st.error("❌ Both files must contain the column: 'DMX_ISSUER_ID'")
        else:
            mismatch_df = compare_all_columns(df1, df2)

            if not mismatch_df.empty:
                st.success(f"✅ Found {len(mismatch_df)} mismatched values.")
                st.dataframe(mismatch_df)

                # Export as Excel
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
