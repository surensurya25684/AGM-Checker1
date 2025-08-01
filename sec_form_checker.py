import streamlit as st
import pandas as pd
import io

st.title("🔍 Hierarchical Excel Comparator")
st.markdown("Matches by Issuer ID ➝ Proposal Text ➝ Column-by-Column Vote Comparison")

# === Upload Files ===
file1 = st.file_uploader("Upload First Excel File", type=["xlsx", "xls"])
file2 = st.file_uploader("Upload Second Excel File", type=["xlsx", "xls"])

# === Normalization Function ===
def load_and_prepare(file):
    df = pd.read_excel(file, dtype=str)
    df.columns = df.columns.str.strip().str.upper()
    df = df.applymap(lambda x: str(x).strip().lower() if pd.notnull(x) else "")
    return df

# === Main Comparison Function ===
def hierarchical_compare(df1, df2):
    required_cols = ["DMX_ISSUER_ID", "SHPPROPOSALTEXT", "DMX_ISSUER_NAME"]

    for col in required_cols:
        if col not in df1.columns or col not in df2.columns:
            raise Exception(f"Required column '{col}' missing from one or both files.")

    mismatches = []

    # Step 1: Group by issuer ID
    issuers_file1 = df1.groupby("DMX_ISSUER_ID")
    issuers_file2 = df2.groupby("DMX_ISSUER_ID")

    common_issuer_ids = issuers_file1.groups.keys() & issuers_file2.groups.keys()

    for issuer_id in common_issuer_ids:
        group1 = issuers_file1.get_group(issuer_id)
        group2 = issuers_file2.get_group(issuer_id)

        # Step 2: Match by Proposal Text within issuer
        proposals1 = group1.groupby("SHPPROPOSALTEXT")
        proposals2 = group2.groupby("SHPPROPOSALTEXT")

        common_proposals = proposals1.groups.keys() & proposals2.groups.keys()

        for proposal_text in common_proposals:
            row1 = proposals1.get_group(proposal_text).iloc[0]
            row2 = proposals2.get_group(proposal_text).iloc[0]

            issuer_name = row1.get("DMX_ISSUER_NAME", "") or row2.get("DMX_ISSUER_NAME", "")

            # Step 3: Compare all other columns (excluding match keys)
            for col in df1.columns:
                if col in ["DMX_ISSUER_ID", "SHPPROPOSALTEXT"]:
                    continue
                if col in df2.columns:
                    val1 = row1.get(col, "")
                    val2 = row2.get(col, "")
                    if val1 != val2:
                        mismatches.append({
                            "DMX_ISSUER_ID": issuer_id,
                            "DMX_ISSUER_NAME": issuer_name,
                            "MISMATCHED_COLUMN": col,
                            "VALUE_IN_FILE1": val1,
                            "VALUE_IN_FILE2": val2
                        })

    return pd.DataFrame(mismatches)

# === App Execution ===
if file1 and file2:
    try:
        df1 = load_and_prepare(file1)
        df2 = load_and_prepare(file2)

        mismatch_df = hierarchical_compare(df1, df2)

        if not mismatch_df.empty:
            st.success(f"✅ Found {len(mismatch_df)} mismatched vote values.")
            st.dataframe(mismatch_df)

            # Download option
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                mismatch_df.to_excel(writer, index=False)
            output.seek(0)

            st.download_button(
                label="📥 Download Mismatch Report",
                data=output,
                file_name="issuer_proposal_mismatches.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.success("✅ No mismatches found!")

    except Exception as e:
        st.error(f"❌ Error: {e}")
