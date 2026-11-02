/**
 * Module 3: Deep Health Analytics and Visualizations
 * Day-of-week trends, monthly distributions, and scatter correlation charts.
 */

let dowChartInstance = null;
let monthlyChartInstance = null;
let scatterStepsCalInstance = null;
let scatterActiveHrInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    if (!document.getElementById('dowComparisonChart')) return;
    await loadAnalyticsData();
});

async function loadAnalyticsData() {
    try {
        const response = await fetch('/api/visualization-data');
        const res = await response.json();
        if (!res.has_data) return;

        renderDOWChart(res.day_of_week);
        renderMonthlyChart(res.monthly);
        renderScatterStepsCal(res.correlations.scatter_steps_calories);
        renderScatterActiveHR(res.correlations.scatter_active_rhr);
        renderCorrelationGrid(res.correlations.matrix, res.correlations.metrics);
    } catch (err) {
        console.error('Failed to load analytics visualizations:', err);
    }
}

function renderDOWChart(dowData) {
    const ctx = document.getElementById('dowComparisonChart').getContext('2d');
    if (dowChartInstance) dowChartInstance.destroy();

    dowChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dowData.labels,
            datasets: [
                {
                    label: 'Avg Daily Steps',
                    data: dowData.steps,
                    backgroundColor: '#0284c7',
                    borderRadius: 6,
                    yAxisID: 'y'
                },
                {
                    label: 'Active Minutes',
                    data: dowData.active_minutes,
                    backgroundColor: '#0d9488',
                    borderRadius: 6,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end' }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Steps' },
                    grid: { color: 'rgba(226, 232, 240, 0.6)' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Active Minutes' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

function renderMonthlyChart(monthlyData) {
    const ctx = document.getElementById('monthlySummaryChart').getContext('2d');
    if (monthlyChartInstance) monthlyChartInstance.destroy();

    monthlyChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: monthlyData.labels,
            datasets: [
                {
                    label: 'Avg Heart Rate (bpm)',
                    data: monthlyData.avg_hr,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    yAxisID: 'y_hr',
                    fill: false
                },
                {
                    label: 'Avg Sleep Duration (hrs)',
                    data: monthlyData.avg_sleep,
                    borderColor: '#6366f1',
                    borderWidth: 2.5,
                    tension: 0.3,
                    yAxisID: 'y_sleep',
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end' }
            },
            scales: {
                y_hr: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Heart Rate (bpm)' },
                    grid: { color: 'rgba(226, 232, 240, 0.6)' }
                },
                y_sleep: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Sleep (hours)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

function renderScatterStepsCal(scatterData) {
    const ctx = document.getElementById('scatterStepsCalChart').getContext('2d');
    if (scatterStepsCalInstance) scatterStepsCalInstance.destroy();

    scatterStepsCalInstance = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Steps vs Calories Burned',
                data: scatterData,
                backgroundColor: 'rgba(2, 132, 199, 0.65)',
                borderColor: '#0284c7',
                borderWidth: 1,
                pointRadius: 4.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.raw.x.toLocaleString()} steps -> ${ctx.raw.y} kcal`
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Daily Steps' },
                    grid: { color: 'rgba(226, 232, 240, 0.6)' }
                },
                y: {
                    title: { display: true, text: 'Total Calories Burned (kcal)' },
                    grid: { color: 'rgba(226, 232, 240, 0.6)' }
                }
            }
        }
    });
}

function renderScatterActiveHR(scatterData) {
    const ctx = document.getElementById('scatterActiveHrChart').getContext('2d');
    if (scatterActiveHrInstance) scatterActiveHrInstance.destroy();

    scatterActiveHrInstance = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Active Minutes vs Resting Heart Rate',
                data: scatterData,
                backgroundColor: 'rgba(13, 148, 136, 0.65)',
                borderColor: '#0d9488',
                borderWidth: 1,
                pointRadius: 4.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.raw.x} mins active -> ${ctx.raw.y} bpm resting HR`
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Active Exercise (Minutes)' },
                    grid: { color: 'rgba(226, 232, 240, 0.6)' }
                },
                y: {
                    title: { display: true, text: 'Resting Heart Rate (bpm)' },
                    grid: { color: 'rgba(226, 232, 240, 0.6)' }
                }
            }
        }
    });
}

function renderCorrelationGrid(matrix, metrics) {
    const container = document.getElementById('correlationMatrixContainer');
    if (!container || !matrix) return;

    const colKeys = ['steps', 'resting_heart_rate', 'sleep_hours', 'active_minutes', 'calories_burned', 'stress_level'];
    const prettyHeaders = ['Steps', 'Resting HR', 'Sleep', 'Active Mins', 'Calories', 'Stress'];

    let html = `
        <div class="table-responsive">
            <table class="table table-sm table-bordered text-center align-middle font-monospace small mb-0">
                <thead class="table-light">
                    <tr>
                        <th class="text-start">Metric</th>
                        ${prettyHeaders.map(h => `<th>${h}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
    `;

    colKeys.forEach((rowKey, idx) => {
        html += `<tr><th class="text-start table-light">${prettyHeaders[idx]}</th>`;
        colKeys.forEach(colKey => {
            const val = matrix[rowKey] ? matrix[rowKey][colKey] : 0;
            let bgColor = '#ffffff';
            let textColor = '#1e293b';

            if (val >= 0.7) { bgColor = '#bbf7d0'; textColor = '#166534'; }
            else if (val >= 0.4) { bgColor = '#dcfce7'; textColor = '#15803d'; }
            else if (val <= -0.5) { bgColor = '#fed7aa'; textColor = '#9a3412'; }
            else if (val <= -0.2) { bgColor = '#ffedd5'; textColor = '#c2410c'; }

            html += `<td style="background-color: ${bgColor}; color: ${textColor}; font-weight: 600;">${val !== undefined ? val.toFixed(2) : '-'}</td>`;
        });
        html += `</tr>`;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;
}
