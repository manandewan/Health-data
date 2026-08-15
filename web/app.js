// Clinical Health Research Web Application Logic

let currentPage = 1;
const pageSize = 25;
let filteredPatients = [];

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initCharts();
  initExplorer();
  initModal();
});

// Navigation Handling
function initNavigation() {
  const navBtns = document.querySelectorAll('.nav-link-btn');
  const sections = document.querySelectorAll('.section-container');

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      
      navBtns.forEach(b => b.classList.remove('active'));
      sections.forEach(s => s.classList.remove('active'));

      btn.classList.add('active');
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        targetSection.classList.add('active');
      }
    });
  });
}

// Chart Initializations using Chart.js
function initCharts() {
  if (typeof Chart === 'undefined') return;

  // 1. Age Distribution Chart
  const ctxAge = document.getElementById('chart-age')?.getContext('2d');
  if (ctxAge) {
    new Chart(ctxAge, {
      type: 'bar',
      data: {
        labels: ['< 20 yrs', '20 - 29 yrs', '30 - 39 yrs', '40 - 49 yrs', '50+ yrs'],
        datasets: [{
          label: 'Number of Patients',
          data: [24, 175, 61, 17, 9],
          backgroundColor: '#0284c7',
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
          x: { grid: { display: false } }
        }
      }
    });
  }

  // 2. Lipid Profiles Chart
  const ctxLipid = document.getElementById('chart-lipid')?.getContext('2d');
  if (ctxLipid) {
    new Chart(ctxLipid, {
      type: 'doughnut',
      data: {
        labels: ['Normal Lipids', 'Low HDL (<40)', 'High Triglycerides (>150)', 'Both (High TG + Low HDL)'],
        datasets: [{
          data: [95, 63, 57, 57],
          backgroundColor: ['#10b981', '#f59e0b', '#f97316', '#ef4444'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12 } }
        }
      }
    });
  }

  // 3. Anemia by Gender Chart
  const ctxAnemia = document.getElementById('chart-anemia')?.getContext('2d');
  if (ctxAnemia) {
    new Chart(ctxAnemia, {
      type: 'bar',
      data: {
        labels: ['Female Cohort (N=41)', 'Male Cohort (N=245)'],
        datasets: [
          {
            label: 'Normal Hb',
            data: [8, 211],
            backgroundColor: '#10b981',
            borderRadius: 6
          },
          {
            label: 'Anemic (Low Hb)',
            data: [33, 34],
            backgroundColor: '#e11d48',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: { stacked: true, beginAtZero: true, grid: { color: '#f1f5f9' } }
        },
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12 } }
        }
      }
    });
  }

  // 4. Organ Risk Matrix Chart
  const ctxOrgan = document.getElementById('chart-organ')?.getContext('2d');
  if (ctxOrgan) {
    new Chart(ctxOrgan, {
      type: 'polarArea',
      data: {
        labels: ['Lipid / Cardio (48.9%)', 'ESR Inflammation (28.1%)', 'Anemia (23.8%)', 'Liver / ALT (25.3%)', 'Thyroid TSH (8.1%)', 'Renal Creatinine (1.4%)'],
        datasets: [{
          data: [48.9, 28.1, 23.8, 25.3, 8.1, 1.4],
          backgroundColor: [
            'rgba(245, 158, 11, 0.7)',
            'rgba(239, 68, 68, 0.7)',
            'rgba(225, 29, 72, 0.7)',
            'rgba(14, 165, 233, 0.7)',
            'rgba(168, 85, 247, 0.7)',
            'rgba(100, 116, 139, 0.7)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8 } }
        }
      }
    });
  }
}

// Cohort Explorer, Search, Filtering & Pagination
function initExplorer() {
  if (typeof HEALTH_DATA === 'undefined') return;

  filteredPatients = [...HEALTH_DATA];
  
  const searchInput = document.getElementById('patient-search-input');
  const genderFilter = document.getElementById('filter-gender');
  const riskFilter = document.getElementById('filter-risk');
  const prevBtn = document.getElementById('btn-prev-page');
  const nextBtn = document.getElementById('btn-next-page');

  function applyFilters() {
    const query = searchInput.value.toLowerCase().trim();
    const gender = genderFilter.value;
    const risk = riskFilter.value;

    filteredPatients = HEALTH_DATA.filter(p => {
      const matchSearch = !query || 
        p.name.toLowerCase().includes(query) || 
        p.order_id.toLowerCase().includes(query) || 
        p.barcode.toLowerCase().includes(query);
      
      const matchGender = gender === 'all' || p.gender.toLowerCase() === gender.toLowerCase();
      
      const matchRisk = risk === 'all' || p.risk_flags.includes(risk);

      return matchSearch && matchGender && matchRisk;
    });

    currentPage = 1;
    renderTable();
  }

  searchInput.addEventListener('input', applyFilters);
  genderFilter.addEventListener('change', applyFilters);
  riskFilter.addEventListener('change', applyFilters);

  prevBtn.addEventListener('click', () => {
    if (currentPage > 1) {
      currentPage--;
      renderTable();
    }
  });

  nextBtn.addEventListener('click', () => {
    const totalPages = Math.ceil(filteredPatients.length / pageSize);
    if (currentPage < totalPages) {
      currentPage++;
      renderTable();
    }
  });

  renderTable();
}

function renderTable() {
  const tbody = document.getElementById('patient-table-body');
  const paginationInfo = document.getElementById('pagination-info');
  const prevBtn = document.getElementById('btn-prev-page');
  const nextBtn = document.getElementById('btn-next-page');

  tbody.innerHTML = '';

  const total = filteredPatients.length;
  const totalPages = Math.ceil(total / pageSize) || 1;
  const start = (currentPage - 1) * pageSize;
  const end = Math.min(start + pageSize, total);
  const pageData = filteredPatients.slice(start, end);

  paginationInfo.textContent = total > 0 
    ? `Showing ${start + 1}-${end} of ${total} patients`
    : 'No patients found';

  prevBtn.disabled = currentPage === 1;
  nextBtn.disabled = currentPage >= totalPages;

  pageData.forEach(p => {
    const tr = document.createElement('tr');
    
    // Helpers to highlight cells
    const hba1c = p.tests['HbA1c (%)'] || '-';
    const isHba1cHigh = parseFloat(hba1c) >= 5.7;

    const chol = p.tests['Total Cholesterol (mg/dl)'] || '-';
    const isCholHigh = parseFloat(chol) > 200;

    const tg = p.tests['Serum Triglycerides (mg/dL)'] || '-';
    const isTgHigh = parseFloat(tg) > 150;

    const alt = p.tests['SGPT / ALT (U/L)'] || '-';
    const isAltHigh = parseFloat(alt) > 49;

    const creat = p.tests['Serum Creatinine (mg/dl)'] || '-';
    const isCreatHigh = parseFloat(creat) > 1.2;

    const tsh = p.tests['TSH - Ultrasensitive (µIU/ml)'] || '-';
    const isTshHigh = parseFloat(tsh) > 4.78;

    const hb = p.tests['Haemoglobin (HB) (g/dL)'] || '-';
    const isHbLow = (p.gender.toLowerCase() === 'female' && parseFloat(hb) < 12.0) ||
                    (p.gender.toLowerCase() === 'male' && parseFloat(hb) < 13.0);

    tr.innerHTML = `
      <td>${p.id}</td>
      <td class="id-cell">${p.order_id}</td>
      <td><strong>${escapeHtml(p.name)}</strong></td>
      <td>${p.age || '-'}</td>
      <td>${p.gender}</td>
      <td style="${isHba1cHigh ? 'color: var(--danger); font-weight: 700;' : ''}">${hba1c}</td>
      <td style="${isCholHigh ? 'color: var(--warning); font-weight: 700;' : ''}">${chol}</td>
      <td style="${isTgHigh ? 'color: var(--danger); font-weight: 700;' : ''}">${tg}</td>
      <td style="${isAltHigh ? 'color: var(--warning); font-weight: 700;' : ''}">${alt}</td>
      <td style="${isCreatHigh ? 'color: var(--danger); font-weight: 700;' : ''}">${creat}</td>
      <td style="${isTshHigh ? 'color: var(--warning); font-weight: 700;' : ''}">${tsh}</td>
      <td style="${isHbLow ? 'color: var(--danger); font-weight: 700;' : ''}">${hb}</td>
      <td>
        <span class="finding-badge ${p.abnormal_count > 3 ? 'badge-danger' : (p.abnormal_count > 0 ? 'badge-warning' : 'badge-success')}">
          ${p.abnormal_count} abnormal
        </span>
      </td>
      <td>
        <button class="view-btn" onclick="openPatientModal(${p.id})">View Panel</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Modal Inspector
function initModal() {
  const modal = document.getElementById('patient-modal');
  const closeBtn = document.getElementById('modal-close-btn');

  closeBtn.addEventListener('click', () => {
    modal.classList.remove('open');
  });

  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('open');
    }
  });
}

function openPatientModal(patientId) {
  const patient = HEALTH_DATA.find(p => p.id === patientId);
  if (!patient) return;

  document.getElementById('modal-patient-name').textContent = patient.name || 'Anonymous';
  document.getElementById('modal-order-id').textContent = `Order ID: ${patient.order_id}`;
  document.getElementById('modal-age-gender').textContent = `${patient.age || 'N/A'} Yrs / ${patient.gender}`;
  document.getElementById('modal-barcode').textContent = patient.barcode || 'N/A';
  document.getElementById('modal-collected').textContent = patient.collected_on || patient.camp_date;
  
  const linkEl = document.getElementById('modal-report-link');
  if (linkEl) {
    linkEl.href = patient.report_link;
  }

  const container = document.getElementById('modal-tests-container');
  container.innerHTML = '';

  const abnormalMap = {};
  patient.abnormal_items.forEach(ab => {
    abnormalMap[ab.test] = ab;
  });

  for (const [testName, testVal] of Object.entries(patient.tests)) {
    if (!testVal) continue;
    const isAbnormal = abnormalMap[testName];
    const row = document.createElement('div');
    row.className = `modal-test-row ${isAbnormal ? 'is-abnormal' : ''}`;
    row.innerHTML = `
      <div>
        <strong>${testName}</strong>
        ${isAbnormal ? `<span style="font-size: 0.75rem; margin-left: 6px;">(${isAbnormal.status} &bull; Ref: ${isAbnormal.ref})</span>` : ''}
      </div>
      <div>${testVal}</div>
    `;
    container.appendChild(row);
  }

  document.getElementById('patient-modal').classList.add('open');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
