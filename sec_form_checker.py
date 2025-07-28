import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from io import BytesIO

st.set_page_config(page_title="Excel Validator", layout="centered")

st.title("🔍 Excel File Validator")
st.write("Match records using **DMX_ISSUER_NAME** and **SHPPROPOSALTEXT** columns with fuzzy logic.")

# Upload files
file1 = st.file_uploader("Upload File 1 (Excel)", type=["xlsx"])
file2 = st.file_uploader("Upload File 2 (Excel)", type=["xlsx"])

# Slider to adjust the fuzzy matching threshold
threshold = st.slider("Matching Threshold", 70, 100, 85)

def validate_files(df1, df2, threshold):
    company_col = 'DMX_ISSUER_NAME'
    proposal_col = 'SHPPROPOSALTEXT'
    matches = []
    unmatched_file1 = []
    unmatched_file2 = df2.copy()

    for _, row1 in df1.iterrows():
        best_match = None
        best_score = 0
        best_idx = None

        for idx2, row2 in unmatched_file2.iterrows():
            company_score = fuzz.token_sort_ratio(str(row1[company_col]), str(row2[company_col]))
            proposal_score = fuzz.token_sort_ratio(str(row1[proposal_col]), str(row2[proposal_col]))
            avg_score = (company_score + proposal_score) / 2

            if avg_score > best_score:
                best_score = avg_score
                best_match = row2
                best_idx = idx2

        if best_score >= threshold:
            matches.append({
                'File1_Company': row1[company_col],
                'File2_Company': best_match[company_col],
                'File1_Proposal': row1[proposal_col],
                'File2_Proposal': best_match[proposal_col],
                'Match Score': best_score
            })
            unmatched_file2 = unmatched_file2.drop(index=best_idx)
        else:
            unmatched_file1.append(row1)

    return pd.DataFrame(matches), pd.DataFrame(unmatched_file1), unmatched_file2

def to_excel(matches_df, unmatched1_df, unmatched2_df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        matches_df.to_excel(writer, index=False, sheet_name='Matches')
        unmatched1_df.to_excel(writer, index=False, sheet_name='Unmatched_File1')
        unmatched2_df.to_excel(writer, index=False, sheet_name='Unmatched_File2')
    output.seek(0)
    return output

# Main logic
if file1 and file2:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    if 'DMX_ISSUER_NAME' in df1.columns and 'SHPPROPOSALTEXT' in df1.columns and \
       'DMX_ISSUER_NAME' in df2.columns and 'SHPPROPOSALTEXT' in df2.columns:

        st.success("✅ Files uploaded. Starting comparison...")
        matches_df, unmatched1_df, unmatched2_df = validate_files(df1, df2, threshold)

        st.subheader("🔗 Matches")
        st.dataframe(matches_df.head())

        st.subheader("❌ Unmatched Rows (File 1)")
        st.dataframe(unmatched1_df.head())

        st.subheader("❌ Unmatched Rows (File 2)")
        st.dataframe(unmatched2_df.head())

        excel_file = to_excel(matches_df, unmatched1_df, unmatched2_df)
        st.download_button(
            label="📥 Download Result Excel",
            data=excel_file,
            file_name="validation_result.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("⚠️ One or both files do not contain required columns: 'DMX_ISSUER_NAME' and 'SHPPROPOSALTEXT'")
