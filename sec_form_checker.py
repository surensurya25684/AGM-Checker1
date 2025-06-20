import streamlit as st
import pandas as pd

st.set_page_config(page_title="Vote Results Comparator", layout="wide")
st.title("📊 Shareholder Vote Comparison Tool")

st.markdown("Upload two Excel/CSV files with shareholder vote data to find mismatches in vote results by proposal text.")

# Upload base and comparison files
base_file = st.file_uploader("Upload Base File", type=["csv", "xlsx"], key="base")
comparison_file = st.file_uploader("Upload Comparison File", type=["csv", "xlsx"], key="comp")

if base_file and comparison_file:
    # Load files
    def load_file(uploaded_file):
        if uploaded_file.name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        else:
            return pd.read_excel(uploaded_file)

    df_base = load_file(base_file)
    df_comp = load_file(comparison_file)

    # Required columns
    id_columns = ["DMX_ISSUER_ID", "DMX_ISSUER_NAME", "Proposal Text (SHPPROPOSALTEXT)"]
    vote_columns = [
        'Vote Results - For (SHPVOTESYES)',
        'Vote Results - Against (SHPVOTESNO)',
        'Vote Results - Abstained (SHPVOTESABSTAINED)',
        'Vote Results - Withheld (SHPVOTESWITHHELD)',
        'Vote Results - Broker Non-Votes (SHPVOTESBROKERNONVOTES)',
        'Proposal Vote Results: Total (SHPVOTESTOTAL)'
    ]

    try:
        df_base = df_base[id_columns + vote_columns]
        df_comp = df_comp[id_columns + vote_columns]
    except KeyError:
        st.error("One or both files are missing required columns. Please verify the template.")
    else:
        # Merge by Proposal Text
        merged = pd.merge(df_base, df_comp, on='Proposal Text (SHPPROPOSALTEXT)', suffixes=('_base', '_comp'))

        # Detect mismatches
        mismatch_rows = []
        for col in vote_columns:
            base_col = f"{col}_base"
            comp_col = f"{col}_comp"
            mismatches = merged[merged[base_col] != merged[comp_col]][[
                'DMX_ISSUER_ID_base', 'DMX_ISSUER_NAME_base', 'Proposal Text (SHPPROPOSALTEXT)', base_col, comp_col
            ]].copy()
            mismatches.columns = [
                'DMX_ISSUER_ID', 'DMX_ISSUER_NAME', 'Proposal Text', 'Base File Value', 'Comparison File Value'
            ]
            mismatches['Field'] = col
            mismatches['Is Vote Mismatch'] = 'Yes'
            mismatch_rows.append(mismatches)

        result_df = pd.concat(mismatch_rows, ignore_index=True) if mismatch_rows else pd.DataFrame()

        if not result_df.empty:
            st.success(f"Found {len(result_df)} mismatched vote entries.")
            st.dataframe(result_df, use_container_width=True)

            # Download link
            def convert_df(df):
                return df.to_excel(index=False, engine='openpyxl')

            st.download_button(
                label="📥 Download Mismatch Report",
                data=convert_df(result_df),
                file_name="vote_mismatches_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("No vote mismatches found between the files.")
