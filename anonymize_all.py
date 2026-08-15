import csv
import json
import xlsxwriter
import re
import os

CSV_INPUT = 'master health data.csv'
CSV_OUTPUT = 'master health data.csv'
CSV_FLAGGED = 'master health data with flags.csv'
XLSX_OUTPUT = 'master health data - highlighted.xlsx'
WEB_DATA_JS = 'web/data.js'

with open(CSV_INPUT, 'r', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

# Define reference ranges
def get_range(col, gender):
    gender = str(gender).lower()
    ranges = {
        'HbA1c (%)': (4.2, 5.7),
        'Average Estimated Glucose (mg/dl)': (70.0, 115.0),
        'Total Cholesterol (mg/dl)': (None, 200.0),
        'Serum Triglycerides (mg/dL)': (None, 150.0),
        'Serum HDL Cholesterol (mg/dL)': (40.0, 60.0),
        'LDL Cholesterol Calculated (mg/dL)': (None, 100.0),
        'VLDL Cholesterol Calculated (mg/dl)': (None, 30.0),
        'Total CHOL / HDL Ratio': (3.30, 4.40),
        'LDL / HDL Ratio': (0.5, 3.0),
        'HDL / LDL Ratio': (0.4, None),
        'Non-HDL Cholesterol (mg/dL)': (0.0, 160.0),
        'Total Bilirubin (mg/dl)': (0.2, 1.1),
        'Direct Bilirubin (mg/dl)': (0.0, 0.3),
        'Indirect Bilirubin (mg/dl)': (0.0, 0.8),
        'SGOT / AST (U/L)': (5.0, 34.0),
        'SGPT / ALT (U/L)': (10.0, 49.0),
        'Alkaline Phosphatase (ALP) (U/L)': (46.0, 116.0),
        'Gamma GT (GGT) (U/L)': (0.0, 38.0),
        'Total Protein (g/dl)': (5.7, 8.2),
        'Serum Albumin (g/dl)': (3.4, 4.8),
        'Serum Globulin (gm/dl)': (3.0, 4.2),
        'Albumin / Globulin Ratio': (1.2, 2.5),
        'SGOT / SGPT Ratio': (0.7, 1.4),
        'Serum Creatinine (mg/dl)': (0.2, 1.2) if 'male' in gender else (0.3, 1.2),
        'Serum Uric Acid (mg/dl)': (3.5, 7.2) if 'male' in gender else (2.6, 6.0),
        'Blood Urea (mg/dl)': (19.3, 49.38),
        'Blood Urea Nitrogen (BUN) (mg/dl)': (8.0, 20.0),
        'TSH - Ultrasensitive (µIU/ml)': (0.55, 4.78),
        'Haemoglobin (HB) (g/dL)': (13.0, 17.0) if 'male' in gender else (12.0, 15.0),
        'Total Leucocyte Count (TLC) (10^3/uL)': (4.0, 10.0),
        'Hematocrit (PCV) (%)': (40.0, 50.0) if 'male' in gender else (36.0, 46.0),
        'Red Blood Cell Count (RBC) (10^6/µl)': (4.50, 5.50) if 'male' in gender else (3.80, 4.80),
        'Mean Corp Volume (MCV) (fL)': (83.0, 101.0),
        'Mean Corp Hb (MCH) (pg)': (27.0, 32.0),
        'Mean Corp Hb Conc (MCHC) (g/dL)': (31.5, 34.5),
        'RDW - CV (%)': (11.6, 14.0),
        'RDW - SD (fL)': (39.0, 46.0),
        'Neutrophils (%)': (40.0, 80.0),
        'Lymphocytes (%)': (20.0, 40.0),
        'Monocytes (%)': (2.0, 10.0),
        'Eosinophils (%)': (1.0, 6.0),
        'Basophils (%)': (0.0, 2.0),
        'Absolute Neutrophil Count (ANC) (10^3/uL)': (2.0, 7.0),
        'Absolute Lymphocyte Count (ALC) (10^3/uL)': (1.0, 3.0),
        'Absolute Monocyte Count (10^3/uL)': (0.2, 1.0),
        'Absolute Eosinophil Count (AEC) (10^3/uL)': (0.02, 0.5),
        'Absolute Basophil Count (10^3/uL)': (0.02, 0.10),
        'Platelet Count (PLT) (10^3/µl)': (150.0, 410.0),
        'MPV (fL)': (7.0, 9.0),
        'ESR (mm/1st hour)': (0.0, 12.0),
    }
    return ranges.get(col, (None, None))

def is_out_of_range(val_str, col, gender):
    if not val_str or not val_str.strip():
        return False
    try:
        val = float(val_str.strip())
    except ValueError:
        return False
    low, high = get_range(col, gender)
    if low is not None and val < low:
        return True
    if high is not None and val > high:
        return True
    return False

# 1. Anonymize rows
anonymized_master_rows = []
anonymized_flagged_rows = []
web_patients = []

for idx, r in enumerate(rows, 1):
    subject_id = f"Subject_{idx:03d}"
    order_id = f"ORD_{idx:03d}"
    barcode_id = f"BC_{idx:03d}"
    
    clean_row = dict(r)
    # Replace PII identifiers with systematic clinical study IDs
    clean_row['Booking ID / Order ID'] = order_id
    clean_row['Patient Name'] = subject_id
    clean_row['Barcode / SIN No'] = barcode_id
    clean_row['Report Link'] = 'ANONYMIZED_CLINICAL_ARCHIVE'
    
    # Remove raw collection timestamps if they contain specific location/person notes
    if 'Sample Type' in clean_row and not clean_row['Sample Type']:
        clean_row['Sample Type'] = 'Whole Blood / Serum'
        
    anonymized_master_rows.append(clean_row)
    
    # Flags computation
    gender = clean_row.get('Gender', '')
    abnormal_list = []
    tests = {}
    
    for k, v in clean_row.items():
        if k in ['Camp Date', 'Booking ID / Order ID', 'Patient Name', 'Age', 'Age Unit', 'Gender', 'Barcode / SIN No', 'Sample Collected On', 'Sample Received On', 'Report Generated On', 'Sample Type', 'Report Status', 'Report Link']:
            continue
        v_str = str(v).strip()
        tests[k] = v_str
        if v_str:
            try:
                val = float(v_str)
                low, high = get_range(k, gender)
                if low is not None and val < low:
                    abnormal_list.append(f"{k}: {val} (LOW)")
                elif high is not None and val > high:
                    abnormal_list.append(f"{k}: {val} (HIGH)")
            except ValueError:
                pass
                
    flagged_row = dict(clean_row)
    flagged_row['Total Out of Range Tests'] = len(abnormal_list)
    flagged_row['Abnormal Parameters Summary'] = '; '.join(abnormal_list)
    anonymized_flagged_rows.append(flagged_row)
    
    # Risk flags for Web App
    risk_flags = []
    def to_float(v):
        try: return float(v.strip()) if v and v.strip() else None
        except: return None
        
    tg = to_float(clean_row.get('Serum Triglycerides (mg/dL)'))
    hdl = to_float(clean_row.get('Serum HDL Cholesterol (mg/dL)'))
    if (tg and tg > 150) or (hdl and hdl < 40):
        risk_flags.append('Cardiovascular / Lipid')
        
    alt = to_float(clean_row.get('SGPT / ALT (U/L)'))
    ast = to_float(clean_row.get('SGOT / AST (U/L)'))
    if (alt and alt > 49) or (ast and ast > 34):
        risk_flags.append('Hepatic / Liver')
        
    hb = to_float(clean_row.get('Haemoglobin (HB) (g/dL)'))
    if (gender.lower() == 'female' and hb and hb < 12.0) or (gender.lower() == 'male' and hb and hb < 13.0):
        risk_flags.append('Anemia')
        
    hba1c = to_float(clean_row.get('HbA1c (%)'))
    if hba1c and hba1c >= 5.7:
        risk_flags.append('Hyperglycemia / Diabetic')
        
    tsh = to_float(clean_row.get('TSH - Ultrasensitive (µIU/ml)'))
    if tsh and tsh > 4.78:
        risk_flags.append('Thyroid Elevation')
        
    abnormal_items_for_web = []
    for k, v in tests.items():
        if not v: continue
        try:
            val = float(v)
            low, high = get_range(k, gender)
            if low is not None and val < low:
                abnormal_items_for_web.append({'test': k, 'val': val, 'status': 'LOW', 'ref': f"{low} - {high}" if high else f"> {low}"})
            elif high is not None and val > high:
                abnormal_items_for_web.append({'test': k, 'val': val, 'status': 'HIGH', 'ref': f"{low} - {high}" if low else f"< {high}"})
        except ValueError:
            pass

    web_patients.append({
        'id': idx,
        'order_id': order_id,
        'camp_date': clean_row.get('Camp Date', ''),
        'name': subject_id,
        'age': int(float(clean_row['Age'])) if clean_row.get('Age') and clean_row.get('Age').isdigit() else clean_row.get('Age', ''),
        'gender': gender,
        'barcode': barcode_id,
        'collected_on': clean_row.get('Sample Collected On', ''),
        'report_link': '#',
        'abnormal_count': len(abnormal_items_for_web),
        'abnormal_items': abnormal_items_for_web,
        'risk_flags': risk_flags,
        'tests': tests
    })

# Write master health data.csv
fieldnames = list(anonymized_master_rows[0].keys())
with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(anonymized_master_rows)

# Write master health data with flags.csv
flag_fieldnames = list(anonymized_flagged_rows[0].keys())
with open(CSV_FLAGGED, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=flag_fieldnames)
    writer.writeheader()
    writer.writerows(anonymized_flagged_rows)

# Write web/data.js
with open(WEB_DATA_JS, 'w', encoding='utf-8') as f:
    f.write('const HEALTH_DATA = ' + json.dumps(web_patients, indent=2) + ';\n')

# Write Excel workbook with highlighted cells
wb = xlsxwriter.Workbook(XLSX_OUTPUT)
ws = wb.add_worksheet('Anonymized Health Data')
ws.freeze_panes(1, 4)

fmt_header = wb.add_format({'bold': True, 'bg_color': '#1E293B', 'font_color': '#FFFFFF', 'border': 1, 'align': 'center', 'valign': 'vcenter'})
fmt_normal = wb.add_format({'border': 1, 'valign': 'vcenter'})
fmt_num = wb.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter'})
fmt_abnormal = wb.add_format({'border': 1, 'bg_color': '#FEE2E2', 'font_color': '#991B1B', 'bold': True, 'align': 'right', 'valign': 'vcenter'})

for col_idx, h in enumerate(fieldnames):
    ws.write(0, col_idx, h, fmt_header)

stats = {}
for row_idx, row in enumerate(anonymized_master_rows, 1):
    gender = row.get('Gender', '')
    for col_idx, h in enumerate(fieldnames):
        val = row.get(h, '')
        abnormal = is_out_of_range(val, h, gender)
        
        is_float = False
        fval = None
        try:
            fval = float(val)
            is_float = True
        except ValueError:
            pass
            
        if abnormal:
            if is_float:
                ws.write_number(row_idx, col_idx, fval, fmt_abnormal)
            else:
                ws.write(row_idx, col_idx, val, fmt_abnormal)
        else:
            if is_float:
                ws.write_number(row_idx, col_idx, fval, fmt_num)
            else:
                ws.write(row_idx, col_idx, val, fmt_normal)

# Reference sheet in Excel
ws_ref = wb.add_worksheet('Reference Ranges')
fmt_ref_head = wb.add_format({'bold': True, 'bg_color': '#0F172A', 'font_color': '#FFFFFF', 'border': 1})
ws_ref.write_row(0, 0, ['Test Parameter', 'Ideal Biological Reference Interval'], fmt_ref_head)

ref_descriptions = {
    'HbA1c (%)': '4.2 - 5.7 % (Non-diabetic <5.7%, Prediabetes 5.7-6.4%, Diabetic >=6.5%)',
    'Average Estimated Glucose (mg/dl)': '70.0 - 115.0 mg/dl',
    'Total Cholesterol (mg/dl)': '< 200 mg/dl (Desirable: <200, Borderline: 200-239, High: >=240)',
    'Serum Triglycerides (mg/dL)': '< 150 mg/dL (Desirable: <150, Borderline: 150-199, High: 200-499)',
    'Serum HDL Cholesterol (mg/dL)': '40.0 - 60.0 mg/dL (Good Cholesterol)',
    'LDL Cholesterol Calculated (mg/dL)': '< 100 mg/dL (Optimal <100)',
    'VLDL Cholesterol Calculated (mg/dl)': '< 30.0 mg/dl',
    'Total CHOL / HDL Ratio': '3.30 - 4.40 Ratio',
    'LDL / HDL Ratio': '0.5 - 3.0 Ratio',
    'HDL / LDL Ratio': '> 0.4 Ratio',
    'Non-HDL Cholesterol (mg/dL)': '0.0 - 160.0 mg/dL',
    'Total Bilirubin (mg/dl)': '0.2 - 1.1 mg/dl',
    'Direct Bilirubin (mg/dl)': '0.0 - 0.3 mg/dl',
    'Indirect Bilirubin (mg/dl)': '0.0 - 0.8 mg/dl',
    'SGOT / AST (U/L)': '5.0 - 34.0 U/L',
    'SGPT / ALT (U/L)': '10.0 - 49.0 U/L',
    'Alkaline Phosphatase (ALP) (U/L)': '46.0 - 116.0 U/L',
    'Gamma GT (GGT) (U/L)': '0.0 - 38.0 U/L',
    'Total Protein (g/dl)': '5.7 - 8.2 g/dl',
    'Serum Albumin (g/dl)': '3.4 - 4.8 g/dl',
    'Serum Globulin (gm/dl)': '3.0 - 4.2 gm/dl',
    'Albumin / Globulin Ratio': '1.2 - 2.5 Ratio',
    'SGOT / SGPT Ratio': '0.7 - 1.4 Ratio',
    'Serum Creatinine (mg/dl)': 'Female: 0.3 - 1.2 mg/dl | Male: 0.2 - 1.2 mg/dl',
    'Serum Uric Acid (mg/dl)': 'Female: 2.6 - 6.0 mg/dl | Male: 3.5 - 7.2 mg/dl',
    'Blood Urea (mg/dl)': '19.3 - 49.38 mg/dl',
    'Blood Urea Nitrogen (BUN) (mg/dl)': '8.0 - 20.0 mg/dl',
    'TSH - Ultrasensitive (µIU/ml)': '0.55 - 4.78 µIU/ml',
    'Haemoglobin (HB) (g/dL)': 'Female: 12.0 - 15.0 g/dL | Male: 13.0 - 17.0 g/dL',
    'Total Leucocyte Count (TLC) (10^3/uL)': '4.0 - 10.0 10^3/uL',
    'Hematocrit (PCV) (%)': 'Female: 36.0 - 46.0 % | Male: 40.0 - 50.0 %',
    'Red Blood Cell Count (RBC) (10^6/µl)': 'Female: 3.80 - 4.80 10^6/µl | Male: 4.50 - 5.50 10^6/µl',
    'Mean Corp Volume (MCV) (fL)': '83.0 - 101.0 fL',
    'Mean Corp Hb (MCH) (pg)': '27.0 - 32.0 pg',
    'Mean Corp Hb Conc (MCHC) (g/dL)': '31.5 - 34.5 g/dL',
    'RDW - CV (%)': '11.6 - 14.0 %',
    'RDW - SD (fL)': '39.0 - 46.0 fL',
    'Neutrophils (%)': '40.0 - 80.0 %',
    'Lymphocytes (%)': '20.0 - 40.0 %',
    'Monocytes (%)': '2.0 - 10.0 %',
    'Eosinophils (%)': '1.0 - 6.0 %',
    'Basophils (%)': '0.0 - 2.0 %',
    'Absolute Neutrophil Count (ANC) (10^3/uL)': '2.0 - 7.0 10^3/uL',
    'Absolute Lymphocyte Count (ALC) (10^3/uL)': '1.0 - 3.0 10^3/uL',
    'Absolute Monocyte Count (10^3/uL)': '0.2 - 1.0 10^3/uL',
    'Absolute Eosinophil Count (AEC) (10^3/uL)': '0.02 - 0.5 10^3/uL',
    'Absolute Basophil Count (10^3/uL)': '0.02 - 0.10 10^3/uL',
    'Platelet Count (PLT) (10^3/µl)': '150.0 - 410.0 10^3/µl',
    'MPV (fL)': '7.0 - 9.0 fL',
    'ESR (mm/1st hour)': '0.0 - 12.0 mm/1st hour',
}

for r_idx, (k, desc) in enumerate(ref_descriptions.items(), 1):
    ws_ref.write_row(r_idx, 0, [k, desc])

ws_ref.set_column(0, 0, 35)
ws_ref.set_column(1, 1, 65)
ws.autofit()
wb.close()

print('Successfully re-generated all anonymized datasets!')
