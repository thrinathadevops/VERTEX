import io
import pandas as pd
from datetime import datetime

def generate_excel_report(drift_results: list, component_type: str) -> io.BytesIO:
    """
    Takes drift results and generates the VAREX standard Excel format.
    Uses pandas and openpyxl to stylize red and green backgrounds.
    """
    # 1. Prepare DataFrames
    
    # Summary Info
    total_checks = len(drift_results)
    mismatches = len([d for d in drift_results if d['status'] == 'DRIFT'])
    
    summary_data = {
        "Metric": [
            "Report Generated", 
            "Component Type",
            "Environments Compared", 
            "Total Parameters Checked", 
            "Total Drifts (Mismatches)", 
            "Overall Status"
        ],
        "Value": [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            component_type.upper(),
            "PROD vs DR",
            total_checks,
            mismatches,
            "❌ DRIFT DETECTED" if mismatches > 0 else "✅ IN SYNC"
        ]
    }
    df_summary = pd.DataFrame(summary_data)
    
    # Detailed Info
    df_details = pd.DataFrame(drift_results)
    if 'parameter' in df_details.columns:
        df_details = df_details[['parameter', 'prod_value', 'dr_value', 'status', 'remediation']]
        df_details.columns = ['Parameter', 'PROD Value', 'DR Value', 'Status', 'Remediation']
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name="📊 Summary", index=False)
        df_details.to_excel(writer, sheet_name=f"⚙️ {component_type.title()} Config", index=False)
        
        # Openpyxl objects to style
        workbook = writer.book
        worksheet_summary = writer.sheets["📊 Summary"]
        worksheet_details = writer.sheets[f"⚙️ {component_type.title()} Config"]
        
        # Adjust column widths
        for col in worksheet_summary.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet_summary.column_dimensions[column].width = adjusted_width
            
        for col in worksheet_details.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = max(15, min(max_length + 2, 50)) # Cap at 50 width
            worksheet_details.column_dimensions[column].width = adjusted_width
            
    output.seek(0)
    return output
