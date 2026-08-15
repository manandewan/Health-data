import os
import re
import io
import csv
import ssl
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import pdfplumber

CSV_INPUT = 'Blinkit Camp Report_F-403, Ground Floor, Block F, Sushant Lok, Phase 2, Gurugram, 11,12,13 Aug - PII removed.csv'
CSV_OUTPUT = 'master health data.csv'
CACHE_DIR = 'downloaded_reports'

os.makedirs(CACHE_DIR, exist_ok=True)
ssl_ctx = ssl._create_unverified_context()

def download_pdf(file_id):
    local_path = os.path.join(CACHE_DIR, f'{file_id}.pdf')
    if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
        with open(local_path, 'rb') as f:
            return f.read()

    download_urls = [
        f'https://drive.usercontent.google.com/download?id={file_id}&export=download',
        f'https://drive.google.com/uc?export=download&id={file_id}',
    ]

    for url in download_urls:
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            )
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
                content = resp.read()
                if content.startswith(b'%PDF'):
                    with open(local_path, 'wb') as f:
                        f.write(content)
                    return content
        except Exception as e:
            time.sleep(0.5)

    return None

def extract_val(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return ''

def parse_report_text(text, entry):
    data = {
        'Camp Date': entry.get('section_date', ''),
        'Booking ID / Order ID': entry.get('booking_id', ''),
        'Patient Name': '',
        'Age': '',
        'Age Unit': 'Years',
        'Gender': '',
        'Barcode / SIN No': '',
        'Sample Collected On': '',
        'Sample Received On': '',
        'Report Generated On': '',
        'Sample Type': '',
        'Report Status': '',
        'Report Link': f"https://drive.google.com/file/d/{entry['file_id']}/view?usp=drive_link",
        
        # HbA1c
        'HbA1c (%)': '',
        'Average Estimated Glucose (mg/dl)': '',
        
        # Lipid Profile
        'Total Cholesterol (mg/dl)': '',
        'Serum Triglycerides (mg/dL)': '',
        'Serum HDL Cholesterol (mg/dL)': '',
        'LDL Cholesterol Calculated (mg/dL)': '',
        'VLDL Cholesterol Calculated (mg/dl)': '',
        'Total CHOL / HDL Ratio': '',
        'LDL / HDL Ratio': '',
        'HDL / LDL Ratio': '',
        'Non-HDL Cholesterol (mg/dL)': '',
        
        # LFT
        'Total Bilirubin (mg/dl)': '',
        'Direct Bilirubin (mg/dl)': '',
        'Indirect Bilirubin (mg/dl)': '',
        'SGOT / AST (U/L)': '',
        'SGPT / ALT (U/L)': '',
        'SGOT / SGPT Ratio': '',
        'Alkaline Phosphatase (ALP) (U/L)': '',
        'Gamma GT (GGT) (U/L)': '',
        'Total Protein (g/dl)': '',
        'Serum Albumin (g/dl)': '',
        'Serum Globulin (gm/dl)': '',
        'Albumin / Globulin Ratio': '',
        
        # KFT
        'Serum Creatinine (mg/dl)': '',
        'GFR Estimated (mL/min/1.73m2)': '',
        'Serum Uric Acid (mg/dl)': '',
        'Blood Urea (mg/dl)': '',
        'Blood Urea Nitrogen (BUN) (mg/dl)': '',
        'BUN / Creatinine Ratio': '',
        'Urea / Creatinine Ratio': '',
        
        # Thyroid
        'TSH - Ultrasensitive (µIU/ml)': '',
        
        # CBC / Complete Haemogram
        'Haemoglobin (HB) (g/dL)': '',
        'Total Leucocyte Count (TLC) (10^3/uL)': '',
        'Hematocrit (PCV) (%)': '',
        'Red Blood Cell Count (RBC) (10^6/µl)': '',
        'Mean Corp Volume (MCV) (fL)': '',
        'Mean Corp Hb (MCH) (pg)': '',
        'Mean Corp Hb Conc (MCHC) (g/dL)': '',
        'RDW - CV (%)': '',
        'RDW - SD (fL)': '',
        'Mentzer Index': '',
        'RDWI': '',
        'Green and King Index': '',
        'Neutrophils (%)': '',
        'Lymphocytes (%)': '',
        'Monocytes (%)': '',
        'Eosinophils (%)': '',
        'Basophils (%)': '',
        'Absolute Neutrophil Count (ANC) (10^3/uL)': '',
        'Absolute Lymphocyte Count (ALC) (10^3/uL)': '',
        'Absolute Monocyte Count (10^3/uL)': '',
        'Absolute Eosinophil Count (AEC) (10^3/uL)': '',
        'Absolute Basophil Count (10^3/uL)': '',
        'Platelet Count (PLT) (10^3/µl)': '',
        'MPV (fL)': '',
        'ESR (mm/1st hour)': '',
    }

    # Demographics
    pname = extract_val(r'Patient Name\s*:\s*([^:\n]+?)(?:\s+Barcode|\s+SIN|\n|$)', text)
    if pname:
        data['Patient Name'] = pname
    
    barcode = extract_val(r'Barcode\s*:\s*([A-Za-z0-9]+)', text)
    if not barcode:
        barcode = extract_val(r'SIN No\s*:\s*([A-Za-z0-9]+)', text)
    data['Barcode / SIN No'] = barcode

    order_id = extract_val(r'Order Id\s*:\s*([0-9]+)', text)
    if order_id:
        data['Booking ID / Order ID'] = order_id

    age_gender = extract_val(r'Age/Gender\s*:\s*([^:\n]+?)(?:\s+Sample Collected|\n|$)', text)
    if age_gender:
        m_age = re.search(r'(\d+)\s*Y', age_gender, re.IGNORECASE)
        if m_age:
            data['Age'] = m_age.group(1)
        m_gen = re.search(r'/(Male|Female|Other)', age_gender, re.IGNORECASE)
        if m_gen:
            data['Gender'] = m_gen.group(1).capitalize()
        elif 'Male' in age_gender:
            data['Gender'] = 'Male'
        elif 'Female' in age_gender:
            data['Gender'] = 'Female'

    collected = extract_val(r'Sample Collected On\s*:\s*([0-9A-Za-z/:\s]+?[AP]M)', text)
    data['Sample Collected On'] = collected

    received = extract_val(r'Sample Received On\s*:\s*([0-9A-Za-z/:\s]+?[AP]M)', text)
    data['Sample Received On'] = received

    generated = extract_val(r'Report Generated On\s*:\s*([0-9A-Za-z/:\s]+?[AP]M)', text)
    data['Report Generated On'] = generated

    stype = extract_val(r'Sample Type\s*:\s*([^:\n]+?)(?:\s+Report Status|\n|$)', text)
    data['Sample Type'] = stype

    status = extract_val(r'Report Status\s*:\s*([^:\n]+)', text)
    data['Report Status'] = status

    # 1. Diabetes
    data['HbA1c (%)'] = extract_val(r'Hba1c\s*\(Glycosylated Hemoglobin\)\s+([0-9.]+)', text)
    data['Average Estimated Glucose (mg/dl)'] = extract_val(r'Average Estimated Glucose\s+([0-9.]+)', text)

    # 2. Lipid Profile
    data['Total Cholesterol (mg/dl)'] = extract_val(r'Total Cholesterol\s+([0-9.]+)\s+mg/d[lL]', text)
    data['Serum Triglycerides (mg/dL)'] = extract_val(r'Serum Triglycerides\s+([0-9.]+)\s+mg/d[lL]', text)
    data['Serum HDL Cholesterol (mg/dL)'] = extract_val(r'Serum HDL Cholesterol\s+([0-9.]+)\s+mg/d[lL]', text)
    data['LDL Cholesterol Calculated (mg/dL)'] = extract_val(r'LDL Cholesterol Calculated\s+([0-9.]+)\s+mg/d[lL]', text)
    data['VLDL Cholesterol Calculated (mg/dl)'] = extract_val(r'VLDL Cholesterol Calculated\s+([0-9.]+)\s+mg/d[lL]', text)
    data['Total CHOL / HDL Ratio'] = extract_val(r'Total CHOL\s*/\s*HDL Cholesterol Ratio\s+([0-9.]+)', text)
    data['LDL / HDL Ratio'] = extract_val(r'LDL\s*/\s*HDL Cholesterol Ratio\s+([0-9.]+)', text)
    data['HDL / LDL Ratio'] = extract_val(r'HDL\s*/\s*LDL Cholesterol Ratio\s+([0-9.]+)', text)
    data['Non-HDL Cholesterol (mg/dL)'] = extract_val(r'Non-HDL Cholesterol\s+([0-9.]+)\s+mg/d[lL]', text)

    # 3. LFT
    data['Total Bilirubin (mg/dl)'] = extract_val(r'Serum Bilirubin,\s*\(Total\)\s+([0-9.]+)', text)
    data['Direct Bilirubin (mg/dl)'] = extract_val(r'Serum Bilirubin,\s*\(Direct\)\s+([0-9.]+)', text)
    data['Indirect Bilirubin (mg/dl)'] = extract_val(r'Serum Bilirubin,\s*\(Indirect\)\s+([0-9.]+)', text)
    data['SGOT / AST (U/L)'] = extract_val(r'(?:Aspartate Aminotransferase\s*\(AST/SGOT\)|AST/SGOT)\s+([0-9.]+)', text)
    data['SGPT / ALT (U/L)'] = extract_val(r'(?:Alanine Aminotransferase\s*\(ALT/SGPT\)|ALT/SGPT)\s+([0-9.]+)', text)
    data['Alkaline Phosphatase (ALP) (U/L)'] = extract_val(r'Alkaline Phosphatase\s*\(ALP\)\s+([0-9.]+)', text)
    data['Gamma GT (GGT) (U/L)'] = extract_val(r'(?:Gamma Glutamyl Transferase\s*\(GGT\)|Gamma GT)\s+([0-9.]+)', text)
    data['Total Protein (g/dl)'] = extract_val(r'Serum Total Protein\s+([0-9.]+)', text)
    data['Serum Albumin (g/dl)'] = extract_val(r'Serum Albumin\s+([0-9.]+)', text)
    data['Serum Globulin (gm/dl)'] = extract_val(r'Serum Globulin\s+([0-9.]+)', text)
    data['Albumin / Globulin Ratio'] = extract_val(r'Albumin/Globulin Ratio\s+([0-9.]+)', text)
    data['SGOT / SGPT Ratio'] = extract_val(r'SGOT/SGPT Ratio\s+([0-9.]+)', text)

    # 4. KFT
    data['Serum Creatinine (mg/dl)'] = extract_val(r'Serum Creatinine\s+([0-9.]+)', text)
    data['GFR Estimated (mL/min/1.73m2)'] = extract_val(r'GFR,\s*ESTIMATED\s+([0-9.]+)', text)
    data['Serum Uric Acid (mg/dl)'] = extract_val(r'Serum Uric Acid\s+([0-9.]+)', text)
    data['Blood Urea (mg/dl)'] = extract_val(r'Blood Urea\s+([0-9.]+)\s+mg/d[lL]', text)
    data['Blood Urea Nitrogen (BUN) (mg/dl)'] = extract_val(r'Blood Urea Nitrogen\s*\(BUN\)\s+([0-9.]+)', text)
    data['BUN / Creatinine Ratio'] = extract_val(r'Bun/Creatinine Ratio\s+([0-9.]+)', text)
    data['Urea / Creatinine Ratio'] = extract_val(r'Urea/Creatinine Ratio\s+([0-9.]+)', text)

    # 5. Thyroid
    data['TSH - Ultrasensitive (µIU/ml)'] = extract_val(r'Thyroid Stimulating Hormone\s*\(TSH\)-Ultrasensitive\s+([0-9.]+)', text)

    # 6. Complete Haemogram (CBC)
    data['Haemoglobin (HB) (g/dL)'] = extract_val(r'Haemoglobin\s*\(HB\)\s+([0-9.]+)', text)
    data['Total Leucocyte Count (TLC) (10^3/uL)'] = extract_val(r'Total Leucocyte Count\s*\(TLC\)\s+([0-9.]+)', text)
    data['Hematocrit (PCV) (%)'] = extract_val(r'Hematocrit\s*\(PCV\)\s+([0-9.]+)', text)
    data['Red Blood Cell Count (RBC) (10^6/µl)'] = extract_val(r'Red Blood Cell Count\s*\(RBC\)\s+([0-9.]+)', text)
    data['Mean Corp Volume (MCV) (fL)'] = extract_val(r'Mean Corp Volume\s*\(MCV\)\s+([0-9.]+)', text)
    data['Mean Corp Hb (MCH) (pg)'] = extract_val(r'Mean Corp Hb\s*\(MCH\)\s+([0-9.]+)', text)
    data['Mean Corp Hb Conc (MCHC) (g/dL)'] = extract_val(r'Mean Corp Hb Conc\s*\(MCHC\)\s+([0-9.]+)', text)
    data['RDW - CV (%)'] = extract_val(r'RDW\s*-\s*CV\s+([0-9.]+)', text)
    data['RDW - SD (fL)'] = extract_val(r'RDW\s*-\s*SD\s+([0-9.]+)', text)
    data['Mentzer Index'] = extract_val(r'Mentzer Index\s+([0-9.]+)', text)
    data['RDWI'] = extract_val(r'RDWI\s+([0-9.]+)', text)
    data['Green and King Index'] = extract_val(r'Green and [Kk]ing [Ii]ndex\s+([0-9.]+)', text)
    
    # Differential Count
    data['Neutrophils (%)'] = extract_val(r'(?:Differential Leucocyte Count[\s\S]*?)?Neutrophils\s+([0-9.]+)\s*%', text)
    data['Lymphocytes (%)'] = extract_val(r'Lymphocytes\s+([0-9.]+)\s*%', text)
    data['Monocytes (%)'] = extract_val(r'Monocytes\s+([0-9.]+)\s*%', text)
    data['Eosinophils (%)'] = extract_val(r'Eosinophils\s+([0-9.]+)\s*%', text)
    data['Basophils (%)'] = extract_val(r'Basophils\s+([0-9.]+)\s*%', text)

    # Absolute Leucocyte Count
    data['Absolute Neutrophil Count (ANC) (10^3/uL)'] = extract_val(r'Absolute Neutrophil Count\s*\(ANC\)\s+([0-9.]+)', text)
    data['Absolute Lymphocyte Count (ALC) (10^3/uL)'] = extract_val(r'Absolute Lymphocyte Count\s*\(ALC\)\s+([0-9.]+)', text)
    data['Absolute Monocyte Count (10^3/uL)'] = extract_val(r'Absolute Monocyte Count\s+([0-9.]+)', text)
    data['Absolute Eosinophil Count (AEC) (10^3/uL)'] = extract_val(r'Absolute Eosinophil Count\s*\(AEC\)\s+([0-9.]+)', text)
    data['Absolute Basophil Count (10^3/uL)'] = extract_val(r'Absolute Basophil Count\s+([0-9.]+)', text)

    # Platelets & ESR
    data['Platelet Count (PLT) (10^3/µl)'] = extract_val(r'Platelet Count\s*\(PLT\)\s+([0-9.]+)', text)
    data['MPV (fL)'] = extract_val(r'MPV\s+([0-9.]+)', text)
    data['ESR (mm/1st hour)'] = extract_val(r'ESR\s+([0-9.]+)', text)

    return data

def process_entry(entry):
    fid = entry['file_id']
    pdf_bytes = download_pdf(fid)
    if not pdf_bytes:
        row = parse_report_text('', entry)
        row['Report Status'] = 'Download Failed'
        return row

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages_text = [p.extract_text() or '' for p in pdf.pages]
            full_text = '\n'.join(pages_text)
            return parse_report_text(full_text, entry)
    except Exception as e:
        row = parse_report_text('', entry)
        row['Report Status'] = f'Parsing Error: {str(e)}'
        return row

def main():
    entries = []
    current_section = 'Unknown'
    with open(CSV_INPUT, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line_s = line.strip()
            if not line_s:
                continue
            if ('Aug' in line_s or 'August' in line_s) and 'drive.google' not in line_s:
                current_section = line_s.strip(',').strip()
                continue
            m = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)', line_s)
            if m:
                fid = m.group(1)
                bid_match = re.search(r'^\"?(\d{8,})', line_s)
                bid = bid_match.group(1) if bid_match else ''
                entries.append({
                    'section_date': current_section,
                    'booking_id': bid,
                    'file_id': fid,
                    'raw_line': line_s
                })

    print(f'Total entries to process: {len(entries)}')

    results = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(process_entry, e): idx for idx, e in enumerate(entries)}
        completed = 0
        for f in as_completed(futures):
            res = f.result()
            results.append((futures[f], res))
            completed += 1
            if completed % 25 == 0 or completed == len(entries):
                print(f'Processed {completed}/{len(entries)} reports...')

    # Sort back to original order
    results.sort(key=lambda x: x[0])
    final_rows = [r[1] for r in results]

    if final_rows:
        fieldnames = list(final_rows[0].keys())
        with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(final_rows)
        print(f'Successfully wrote {len(final_rows)} records to "{CSV_OUTPUT}"!')

if __name__ == '__main__':
    main()
