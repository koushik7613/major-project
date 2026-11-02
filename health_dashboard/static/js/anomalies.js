/**
 * Module 4: Machine Learning Anomaly Detection Center
 * Triggers Isolation Forest detection, filters outliers, and renders explanations.
 */

document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('btnRunAnomalyML');
    const metricFilter = document.getElementById('anomalyMetricFilter');
    const severityFilter = document.getElementById('anomalySeverityFilter');
    const tableBody = document.getElementById('anomalyTableBody');

    if (runBtn) {
        runBtn.addEventListener('click', async () => {
            runBtn.disabled = true;
            const origText = runBtn.innerHTML;
            runBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Running Isolation Forest ML...`;

            try {
                const response = await fetch('/api/run-anomaly-detection', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const res = await response.json();

                if (res.success) {
                    showToast(`Identified ${res.total_anomalies} health pattern anomalies!`, 'success');
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    showToast(res.message || 'Detection failed', 'warning');
                    runBtn.disabled = false;
                    runBtn.innerHTML = origText;
                }
            } catch (err) {
                showToast(`Request failed: ${err.message}`, 'danger');
                runBtn.disabled = false;
                runBtn.innerHTML = origText;
            }
        });
    }

    // Filter functionality
    function filterTable() {
        if (!tableBody) return;
        const selectedMetric = metricFilter ? metricFilter.value.toLowerCase() : 'all';
        const selectedSeverity = severityFilter ? severityFilter.value.toLowerCase() : 'all';

        const rows = tableBody.querySelectorAll('tr');
        rows.forEach(row => {
            const metric = row.getAttribute('data-metric') || '';
            const severity = row.getAttribute('data-severity') || '';

            const matchMetric = (selectedMetric === 'all') || metric.toLowerCase().includes(selectedMetric);
            const matchSeverity = (selectedSeverity === 'all') || (severity.toLowerCase() === selectedSeverity);

            if (matchMetric && matchSeverity) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    if (metricFilter) metricFilter.addEventListener('change', filterTable);
    if (severityFilter) severityFilter.addEventListener('change', filterTable);
});
