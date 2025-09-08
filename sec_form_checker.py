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

        # Step 2: Match by Proposal Text within issuer
        proposals1 = group1.groupby("PROPOSAL TEXT (SHPPROPOSALTEXT)")
        proposals2 = group2.groupby("PROPOSAL TEXT (SHPPROPOSALTEXT)")

        common_proposals = proposals1.groups.keys() & proposals2.groups.keys()

        for proposal_text in common_proposals:
            row1 = proposals1.get_group(proposal_text).iloc[0]
            row2 = proposals2.get_group(proposal_text).iloc[0]

            issuer_name = row1.get("DMX_ISSUER_NAME", "") or row2.get("DMX_ISSUER_NAME", "")

            # Step 3: Compare all other columns (excluding match keys)
            for col in df1.columns:
                if col in ["DMX_ISSUER_ID", "PROPOSAL TEXT (SHPPROPOSALTEXT)"]:
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
