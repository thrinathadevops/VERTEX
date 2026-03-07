import sys
sys.path.append("c:/Users/ThrinathaReddy/PycharmProjects/VERTEX/varex_driftguard/backend")
from app.reports.excel_gen import generate_excel_report

drift_results = [
    {
        "parameter": "DB_Patch",
        "prod_value": "SQL*Plus: Release 19.0.0.0.0 - Production\nVersion 19.29.0.0.0\n\nCopyright (c) 1982, 2025, Oracle. All rights reserved.",
        "dr_value": "SQL*Plus: Release 19.0.0.0.0 - Production\nVersion 19.29.0.0.0\n\nCopyright (c) 1982, 2025, Oracle. All rights reserved.",
        "status": "MATCH",
        "remediation": "-"
    },
    {
        "parameter": "v_Param_Info",
        "prod_value": "SQL*Plus: Release 19.0.0.0.0 - Production",
        "dr_value": "SQL*Plus: Release 19.0.0.0.0 - Production",
        "status": "MATCH",
        "remediation": "-"
    },
    {
        "parameter": "undo_file_Size(GB)",
        "prod_value": "SQL*Plus: Release 19.0.0.0.0 - Production",
        "dr_value": "SQL*Plus: Release 18.0.0.0.0 - Production",
        "status": "DRIFT",
        "remediation": "Update DR to match PROD version"
    }
]

metadata = {
    "Server Name": "Oracle Server",
    "IP Address 1": "10.9.50.24",
    "IP Address 2": "10.0.137.237",
    "Baseline Name": "Default Oracle DB AIX",
    "Instance (Primary)": "AXMOBILE1"
}

try:
    output = generate_excel_report(drift_results, "database", metadata)
    with open("c:/Users/ThrinathaReddy/PycharmProjects/VERTEX/varex_driftguard/backend/test_drift_report.xlsx", "wb") as f:
        f.write(output.read())
    print("Excel report generated successfully to test_drift_report.xlsx")
except Exception as e:
    print(f"Error generating Excel: {e}")
