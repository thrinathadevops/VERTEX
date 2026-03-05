def analyze_drift(prod_data: dict, dr_data: dict) -> list:
    """
    Compares Prod vs DR configurations and yields drift status.
    Returns: list of dicts: [{'param': '...', 'prod_val': '...', 'dr_val': '...', 'status': 'MATCH|DRIFT'}]
    """
    results = []
    all_keys = set(prod_data.keys()).union(set(dr_data.keys()))
    
    for key in sorted(all_keys):
        prod_val = prod_data.get(key, "MISSING_IN_PROD")
        dr_val = dr_data.get(key, "MISSING_IN_DR")
        
        # Loose match logic
        is_match = False
        if str(prod_val).lower().strip() == str(dr_val).lower().strip():
            is_match = True
            
        results.append({
            "parameter": key,
            "prod_value": prod_val,
            "dr_value": dr_val,
            "status": "MATCH" if is_match else "DRIFT",
            "remediation": f"Update DR '{key}' to '{prod_val}'" if not is_match and prod_val != "MISSING_IN_PROD" else "-"
        })
        
    return results
