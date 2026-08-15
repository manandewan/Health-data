// Literary Clinical Medical Research Portal JavaScript Logic

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
  const navBtns = document.querySelectorAll('.nav-item-btn');
  const sections = document.querySelectorAll('.chapter-section');

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      
      navBtns.forEach(b => b.classList.remove('active'));
      sections.forEach(s => s.classList.remove('active'));

      btn.classList.add('active');
      const targetSection = document.getElementById(targetId);
      if (targetSection) {
        targetSection.classList.add('active');
        window.scrollTo({ top: targetSection.offsetTop - 100, behavior: 'smooth' });
      }
    });
  });
}

// Chart Initializations
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
          label: 'Number of Screened Employees',
          data: [24, 175, 61, 17, 9],
          backgroundColor: '#0f2d59',
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true, grid: { color: '#f1f5f9' }, title: { display: true, text: 'Subject Count' } },
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
        labels: ['Normal Lipids (33.5%)', 'Isolated Low HDL (22.2%)', 'Isolated High TG (20.1%)', 'Both High TG + Low HDL (20.0%)'],
        datasets: [{
          data: [95, 63, 57, 57],
          backgroundColor: ['#047857', '#b45309', '#ea580c', '#be123c'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } }
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
        labels: ['Female Cohort (N = 41)', 'Male Cohort (N = 245)'],
        datasets: [
          {
            label: 'Normal Hemoglobin',
            data: [8, 211],
            backgroundColor: '#047857',
            borderRadius: 4
          },
          {
            label: 'Anemic (Hb < Reference Threshold)',
            data: [33, 34],
            backgroundColor: '#be123c',
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: { stacked: true, beginAtZero: true, grid: { color: '#f1f5f9' }, title: { display: true, text: 'Number of Individuals' } }
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
        labels: ['Lipid Dysregulation (48.9%)', 'ESR Inflammation (28.1%)', 'Elevated ALT / Liver (25.3%)', 'Anemia (23.8%)', 'Elevated TSH (8.1%)', 'Elevated Creatinine (1.4%)'],
        datasets: [{
          data: [48.9, 28.1, 25.3, 23.8, 8.1, 1.4],
          backgroundColor: [
            'rgba(180, 83, 9, 0.75)',
            'rgba(190, 18, 60, 0.75)',
            'rgba(8, 127, 140, 0.75)',
            'rgba(225, 29, 72, 0.75)',
            'rgba(100, 116, 139, 0.75)',
            'rgba(15, 45, 89, 0.75)'
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

// Cohort Explorer
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

  if (searchInput) searchInput.addEventListener('input', applyFilters);
  if (genderFilter) genderFilter.addEventListener('change', applyFilters);
  if (riskFilter) riskFilter.addEventListener('change', applyFilters);

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        renderTable();
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      const totalPages = Math.ceil(filteredPatients.length / pageSize);
      if (currentPage < totalPages) {
        currentPage++;
        renderTable();
      }
    });
  }

  renderTable();
}

function renderTable() {
  const tbody = document.getElementById('patient-table-body');
  const paginationInfo = document.getElementById('pagination-info');
  const prevBtn = document.getElementById('btn-prev-page');
  const nextBtn = document.getElementById('btn-next-page');

  if (!tbody) return;

  tbody.innerHTML = '';

  const total = filteredPatients.length;
  const totalPages = Math.ceil(total / pageSize) || 1;
  const start = (currentPage - 1) * pageSize;
  const end = Math.min(start + pageSize, total);
  const pageData = filteredPatients.slice(start, end);

  if (paginationInfo) {
    paginationInfo.textContent = total > 0 
      ? `Showing ${start + 1}-${end} of ${total} subjects`
      : 'No matching subjects found';
  }

  if (prevBtn) prevBtn.disabled = currentPage === 1;
  if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

  pageData.forEach(p => {
    const tr = document.createElement('tr');
    
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
      <td style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--navy-primary);">${p.order_id}</td>
      <td><strong>${p.name}</strong></td>
      <td>${p.age || '-'}</td>
      <td>${p.gender}</td>
      <td style="${isHba1cHigh ? 'color: var(--crimson); font-weight: 700;' : ''}">${hba1c}</td>
      <td style="${isCholHigh ? 'color: var(--amber); font-weight: 700;' : ''}">${chol}</td>
      <td style="${isTgHigh ? 'color: var(--crimson); font-weight: 700;' : ''}">${tg}</td>
      <td style="${isAltHigh ? 'color: var(--amber); font-weight: 700;' : ''}">${alt}</td>
      <td style="${isCreatHigh ? 'color: var(--crimson); font-weight: 700;' : ''}">${creat}</td>
      <td style="${isTshHigh ? 'color: var(--amber); font-weight: 700;' : ''}">${tsh}</td>
      <td style="${isHbLow ? 'color: var(--crimson); font-weight: 700;' : ''}">${hb}</td>
      <td>
        <span class="badge ${p.abnormal_count > 3 ? 'badge-red' : (p.abnormal_count > 0 ? 'badge-amber' : 'badge-green')}">
          ${p.abnormal_count} flags
        </span>
      </td>
      <td>
        <button class="inspect-btn" onclick="openPatientModal(${p.id})">View Dossier</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Modal Dossier Handling
function initModal() {
  const modal = document.getElementById('patient-modal');
  const closeBtn = document.getElementById('modal-close-btn');

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      modal.classList.remove('open');
    });
  }

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('open');
      }
    });
  }
}

function openPatientModal(patientId) {
  const patient = HEALTH_DATA.find(p => p.id === patientId);
  if (!patient) return;

  document.getElementById('modal-patient-name').textContent = `${patient.name} &bull; Clinical Diagnostic Dossier`;
  document.getElementById('modal-order-id').textContent = `Order Identifier: ${patient.order_id}`;
  document.getElementById('modal-age-gender').textContent = `${patient.age || 'N/A'} Yrs &bull; ${patient.gender}`;
  document.getElementById('modal-barcode').textContent = patient.barcode || 'N/A';
  document.getElementById('modal-collected').textContent = patient.collected_on || patient.camp_date;

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
    row.className = `dossier-row ${isAbnormal ? 'abnormal' : ''}`;
    row.innerHTML = `
      <div>
        <strong>${testName}</strong>
        ${isAbnormal ? `<span style="font-size: 0.72rem; margin-left: 6px;">[${isAbnormal.status} &bull; Bio Ref: ${isAbnormal.ref}]</span>` : ''}
      </div>
      <div style="font-family: var(--font-mono);">${testVal}</div>
    `;
    container.appendChild(row);
  }

  document.getElementById('patient-modal').classList.add('open');
}
