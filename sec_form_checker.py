import streamlit as st
import pandas as pd
import io

st.title("🔍 Hierarchical Excel Comparator (Enhanced)")
st.markdown("Matches by Issuer ID ➝ Proposal Count ➝ Proposal Text ➝ Vote-by-Vote Comparison")

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
    required_cols = ["DMX_ISSUER_ID", "PROPOSAL TEXT (SHPPROPOSALTEXT)", "DMX_ISSUER_NAME"]

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

        # --- Check Issuer Name consistency ---
        issuer_name1 = group1["DMX_ISSUER_NAME"].iloc[0]
        issuer_name2 = group2["DMX_ISSUER_NAME"].iloc[0]
        if issuer_name1 != issuer_name2:
            mismatches.append({
                "DMX_ISSUER_ID": issuer_id,
                "DMX_ISSUER_NAME": f"{issuer_name1} | {issuer_name2}",
                "MISMATCHED_COLUMN": "DMX_ISSUER_NAME",
                "VALUE_IN_FILE1": issuer_name1,
                "VALUE_IN_FILE2": issuer_name2,
                "ADDITIONAL_COMMENTS": "Issuer name mismatch"
            })

        # --- Check Proposal Counts ---
        if len(group1) != len(group2):
            mismatches.append({
                "DMX_ISSUER_ID": issuer_id,
                "DMX_ISSUER_NAME": issuer_name1,
                "MISMATCHED_COLUMN": "PROPOSAL COUNT",
                "VALUE_IN_FILE1": len(group1),
                "VALUE_IN_FILE2": len(group2),
                "ADDITIONAL_COMMENTS": f"Proposal count mismatch (file1={len(group1)}, file2={len(group2)})"
            })

        # Step 2: Match by Proposal Text within issuer
        proposals1 = group1.groupby("PROPOSAL TEXT (SHPPROPOSALTEXT)")
        proposals2 = group2.groupby("PROPOSAL TEXT (SHPPROPOSALTEXT)")

        common_proposals = proposals1.groups.keys() & proposals2.groups.keys()
        missing_in_file1 = proposals2.groups.keys() - proposals1.groups.keys()
        missing_in_file2 = proposals1.groups.keys() - proposals2.groups.keys()

        # Record missing proposals
        for p in missing_in_file1:
            mismatches.append({
                "DMX_ISSUER_ID": issuer_id,
                "DMX_ISSUER_NAME": issuer_name1,
                "MISMATCHED_COLUMN": "PROPOSAL TEXT",
                "VALUE_IN_FILE1": "MISSING",
                "VALUE_IN_FILE2": p,
                "ADDITIONAL_COMMENTS": "Proposal missing in File1"
            })

        for p in missing_in_file2:
            mismatches.append({
                "DMX_ISSUER_ID": issuer_id,
                "DMX_ISSUER_NAME": issuer_name1,
                "MISMATCHED_COLUMN": "PROPOSAL TEXT",
                "VALUE_IN_FILE1": p,
                "VALUE_IN_FILE2": "MISSING",
                "ADDITIONAL_COMMENTS": "Proposal missing in File2"
            })

        # Step 3: Compare votes for common proposals
        for proposal_text in common_proposals:
            row1 = proposals1.get_group(proposal_text).iloc[0]
            row2 = proposals2.get_group(proposal_text).iloc[0]

            for col in df1.columns:
                if col in ["DMX_ISSUER_ID", "PROPOSAL TEXT (SHPPROPOSALTEXT)", "DMX_ISSUER_NAME"]:
                    continue
                if col in df2.columns:
                    val1 = row1.get(col, "")
                    val2 = row2.get(col, "")
                    if val1 != val2:
                        mismatches.append({
                            "DMX_ISSUER_ID": issuer_id,
                            "DMX_ISSUER_NAME": issuer_name1,
                            "MISMATCHED_COLUMN": col,
                            "VALUE_IN_FILE1": val1,
                            "VALUE_IN_FILE2": val2,
                            "ADDITIONAL_COMMENTS": "Vote value mismatch"
                        })

    return pd.DataFrame(mismatches)


# === App Execution ===
if file1 and file2:
    try:
        df1 = load_and_prepare(file1)
        df2 = load_and_prepare(file2)

        mismatch_df = hierarchical_compare(df1, df2)

        if not mismatch_df.empty:
            st.success(f"✅ Found {len(mismatch_df)} mismatches or inconsistencies.")
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
