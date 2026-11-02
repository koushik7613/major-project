/**
 * Module 2: CSV Upload and Interactive Column Mapping
 */

document.addEventListener('DOMContentLoaded', () => {
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('csvFileInput');
    const mappingSection = document.getElementById('mappingSection');
    const previewContainer = document.getElementById('previewTableContainer');
    const mappingSelectsContainer = document.getElementById('mappingSelectsContainer');
    const confirmProcessBtn = document.getElementById('btnConfirmProcess');
    
    if (!dropzone || !fileInput) return;

    // Click to browse
    dropzone.addEventListener('click', () => fileInput.click());

    // Drag-and-drop events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    async function handleFileSelect(file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showToast('Only CSV (.csv) files are supported.', 'danger');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        dropzone.innerHTML = `
            <div class="spinner-border text-primary mb-3" role="status"></div>
            <h5 class="fw-bold">Analyzing CSV file structure...</h5>
            <p class="text-muted small">Inspecting headers, row count, and data formats</p>
        `;

        try {
            const response = await fetch('/api/upload-preview', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (!data.success) {
                showToast(data.error || 'Failed to read CSV', 'danger');
                resetDropzone();
                return;
            }

            // Display mapping and preview
            renderMappingInterface(data);
        } catch (err) {
            showToast(`Upload failed: ${err.message}`, 'danger');
            resetDropzone();
        }
    }

    function resetDropzone() {
        dropzone.innerHTML = `
            <i class="bi bi-cloud-arrow-up upload-icon"></i>
            <h5 class="fw-bold mb-1">Drag and drop your wearable CSV file here</h5>
            <p class="text-muted small mb-3">Supports Apple Watch, Fitbit, Garmin, Google Fit, or custom exports</p>
            <button type="button" class="btn btn-outline-primary btn-sm px-4">Browse Files</button>
        `;
    }

    function renderMappingInterface(previewData) {
        mappingSection.classList.remove('d-none');
        document.getElementById('detectedRowsBadge').textContent = `${previewData.total_rows.toLocaleString()} Rows`;
        document.getElementById('detectedColsBadge').textContent = `${previewData.columns.length} Columns`;

        // Render Column Mapping Selectors
        mappingSelectsContainer.innerHTML = '';
        const uploadedCols = previewData.columns;
        const autoMapping = previewData.auto_mapping || {};

        const standardFieldDefs = [
            { key: 'record_date', label: 'Date / Timestamp (Required)', required: true },
            { key: 'steps', label: 'Daily Steps', required: false },
            { key: 'resting_heart_rate', label: 'Resting Heart Rate (bpm)', required: false },
            { key: 'avg_heart_rate', label: 'Average Heart Rate (bpm)', required: false },
            { key: 'max_heart_rate', label: 'Max / Peak Heart Rate', required: false },
            { key: 'sleep_hours', label: 'Sleep Duration (hours)', required: false },
            { key: 'deep_sleep_hours', label: 'Deep Sleep (hours)', required: false },
            { key: 'active_minutes', label: 'Active Physical Minutes', required: false },
            { key: 'calories_burned', label: 'Calories Burned (kcal)', required: false },
            { key: 'distance_km', label: 'Distance Walked (km)', required: false },
            { key: 'spo2', label: 'SpO2 Oxygen Saturation (%)', required: false },
            { key: 'stress_level', label: 'Stress Level Score (0-100)', required: false }
        ];

        standardFieldDefs.forEach(field => {
            const mappedVal = autoMapping[field.key] || '';
            const colDiv = document.createElement('div');
            colDiv.className = 'col-md-6 col-lg-4 mb-3';

            let optionsHtml = `<option value="">-- Skip / None --</option>`;
            uploadedCols.forEach(col => {
                const selected = col === mappedVal ? 'selected' : '';
                optionsHtml += `<option value="${col}" ${selected}>${col}</option>`;
            });

            colDiv.innerHTML = `
                <div class="p-2 border rounded bg-white">
                    <label class="form-label small fw-semibold text-secondary mb-1">
                        ${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}
                    </label>
                    <select class="form-select form-select-sm mapping-select" data-std-field="${field.key}">
                        ${optionsHtml}
                    </select>
                </div>
            `;
            mappingSelectsContainer.appendChild(colDiv);
        });

        // Render Data Preview Table
        renderPreviewTable(previewData.columns, previewData.preview_rows);

        // Smooth scroll to mapping section
        mappingSection.scrollIntoView({ behavior: 'smooth' });
    }

    function renderPreviewTable(columns, rows) {
        if (!rows || rows.length === 0) return;
        let html = `
            <div class="table-responsive">
                <table class="table table-sm table-hover align-middle mb-0 font-monospace small">
                    <thead class="table-light">
                        <tr>
                            ${columns.map(c => `<th>${c}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => `
                            <tr>
                                ${columns.map(c => `<td>${row[c] !== undefined ? row[c] : ''}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        previewContainer.innerHTML = html;
    }

    // Confirm & Commit CSV
    if (confirmProcessBtn) {
        confirmProcessBtn.addEventListener('click', async () => {
            const selects = document.querySelectorAll('.mapping-select');
            const customMapping = {};
            let hasDate = false;

            selects.forEach(sel => {
                const stdKey = sel.getAttribute('data-std-field');
                const val = sel.value;
                if (val) {
                    customMapping[stdKey] = val;
                    if (stdKey === 'record_date') hasDate = true;
                }
            });

            if (!hasDate) {
                showToast('Please map the required Date / Timestamp field.', 'warning');
                return;
            }

            confirmProcessBtn.disabled = true;
            confirmProcessBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Cleaning & Processing...`;

            try {
                const response = await fetch('/api/process-csv', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mapping: customMapping })
                });
                const res = await response.json();

                if (res.success) {
                    showToast(`Success! Processed ${res.processed_rows} records (${res.duplicates_removed} duplicates cleaned, ${res.missing_values_imputed} imputed).`, 'success');
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1200);
                } else {
                    showToast(res.error || 'Failed to process dataset.', 'danger');
                    confirmProcessBtn.disabled = false;
                    confirmProcessBtn.innerHTML = `<i class="bi bi-check2-circle me-1"></i> Confirm & Import Dataset`;
                }
            } catch (err) {
                showToast(`Request failed: ${err.message}`, 'danger');
                confirmProcessBtn.disabled = false;
                confirmProcessBtn.innerHTML = `<i class="bi bi-check2-circle me-1"></i> Confirm & Import Dataset`;
            }
        });
    }
});
