# Workplace Health Study — Clinical Health Data & Research Portal

A multi-disciplinary clinical and epidemiological research analysis of **286 de-identified workplace health profiles** from an occupational screening cohort.

All data in this repository is strictly anonymized:
- Identifiers are mapped to standardized research study IDs (`Subject_001` through `Subject_286`, `ORD_001` through `ORD_286`).
- No personal identifying information (PII) or external personal links are stored in this repository.

---

## 📊 Summary of Cohort Findings (N = 286)

| Clinical Focus | Key Metric / Prevalence | Clinical Implication |
| :--- | :--- | :--- |
| **Demographics** | **Median Age: 26 Yrs** (69.6% &lt;30) | Young active workforce with shift-work lifestyle risk factors |
| **Female Anemia** | **80.5% (33 / 41 Women)** | Critical public health priority; microcytic hypochromic iron deficiency |
| **Suboptimal HDL** | **42.3% (120 / 284)** | Low protective HDL cholesterol (&lt;40 mg/dL) |
| **Hypertriglyceridemia** | **40.1% (114 / 284)** | High triglycerides (&gt;150 mg/dL) indicating refined carb/oil intake |
| **Hepatic Transaminases** | **25.3% (72 / 285)** | Elevated ALT/SGPT (&gt;49 U/L), signaling silent metabolic fatty liver risk |
| **Systemic Inflammation** | **28.1% (79 / 281)** | Elevated ESR (&gt;12 mm/1st hr) |
| **Renal Clearance** | **Mean eGFR &gt; 105 mL/min** | Preserved baseline renal parenchyma (98.6% normal creatinine) |

---

## 🗂️ Key Files & Structure

```
.
├── master health data.csv               # De-identified master dataset of all 286 subjects
├── master health data - highlighted.xlsx # Excel with conditional formatting for out-of-range values
├── master health data with flags.csv    # Flagged CSV with summary of abnormal tests
├── build_master_data.py                 # Automated data extraction pipeline
├── anonymize_all.py                     # De-identification and sanitization pipeline
├── web/                                 # Interactive Research Web Application
│   ├── index.html                       # Clinical dashboard and research presentation
│   ├── styles.css                       # Medical UI design system
│   ├── app.js                           # Interactive charts, search, and modal inspector
│   └── data.js                          # Embedded anonymized cohort dataset
└── README.md
```

---

## 🚀 Running the Interactive Web Portal

To view the interactive clinical research dashboard locally:

```bash
# Start a local web server
python3 -m http.server 8000 -d web
```

Then open your browser to `http://localhost:8000` or double-click `web/index.html`.

---

## 🏥 Medical Research Board Divisions

- **Epidemiology & Preventive Medicine Division**
- **Cardiometabolic & Endocrinology Panel**
- **Hematology & Transfusion Medicine Panel**
- **Hepatology & Gastroenterology Panel**
- **Nephrology & Clinical Biochemistry Panel**
