/**
 * Module 1 & 3: Main Dashboard Visualizations
 * Chart.js initialization for steps, cardiac trends, and sleep/activity
 */

let stepsChartInstance = null;
let heartRateChartInstance = null;
let sleepChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Only execute if dashboard charts exist on current view
    if (!document.getElementById('stepsOverviewChart')) return;
    
    await loadDashboardCharts();
});

async function loadDashboardCharts() {
    try {
        const response = await fetch('/api/visualization-data');
        const res = await response.json();
        
        if (!res.has_data) return;
        
        renderStepsChart(res.daily);
        renderHeartRateChart(res.daily);
        renderSleepChart(res.daily);
    } catch (err) {
        console.error('Failed to load dashboard charts:', err);
    }
}

function renderStepsChart(daily) {
    const ctx = document.getElementById('stepsOverviewChart').getContext('2d');
    if (stepsChartInstance) stepsChartInstance.destroy();

    // Use last 30 days for clean dashboard overview
    const sliceCount = Math.min(30, daily.dates.length);
    const labels = daily.dates.slice(-sliceCount);
    const dataSteps = daily.steps.slice(-sliceCount);
    const dataMA = daily.steps_ma.slice(-sliceCount);

    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, 'rgba(2, 132, 199, 0.25)');
    gradient.addColorStop(1, 'rgba(2, 132, 199, 0.00)');

    stepsChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Daily Steps',
                    data: dataSteps,
                    borderColor: '#0284c7',
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.3,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointHoverRadius: 6
                },
                {
                    label: '7-Day Moving Avg',
                    data: dataMA,
                    borderColor: '#0d9488',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toLocaleString()} steps`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: 'rgba(226, 232, 240, 0.6)' },
                    ticks: { callback: (v) => v.toLocaleString() }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function renderHeartRateChart(daily) {
    const ctx = document.getElementById('heartRateOverviewChart').getContext('2d');
    if (heartRateChartInstance) heartRateChartInstance.destroy();

    const sliceCount = Math.min(30, daily.dates.length);
    const labels = daily.dates.slice(-sliceCount);
    const restingHR = daily.resting_hr.slice(-sliceCount);
    const avgHR = daily.avg_hr.slice(-sliceCount);
    const maxHR = daily.max_hr.slice(-sliceCount);

    heartRateChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Resting HR',
                    data: restingHR,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.25,
                    fill: true,
                    pointRadius: 2.5
                },
                {
                    label: 'Average HR',
                    data: avgHR,
                    borderColor: '#0284c7',
                    borderWidth: 2,
                    tension: 0.25,
                    pointRadius: 2
                },
                {
                    label: 'Peak / Max HR',
                    data: maxHR,
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw} bpm`
                    }
                }
            },
            scales: {
                y: {
                    suggestedMin: 50,
                    suggestedMax: 150,
                    grid: { color: 'rgba(226, 232, 240, 0.6)' },
                    ticks: { callback: (v) => `${v} bpm` }
                },
                x: { grid: { display: false } }
            }
        }
    });
}

function renderSleepChart(daily) {
    const ctx = document.getElementById('sleepOverviewChart').getContext('2d');
    if (sleepChartInstance) sleepChartInstance.destroy();

    const sliceCount = Math.min(14, daily.dates.length); // last 14 days
    const labels = daily.dates.slice(-sliceCount);
    const deepSleep = daily.sleep_deep.slice(-sliceCount);
    const lightSleep = daily.sleep_light.slice(-sliceCount);

    sleepChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Deep Sleep (hrs)',
                    data: deepSleep,
                    backgroundColor: '#6366f1',
                    borderRadius: 4
                },
                {
                    label: 'Light / REM Sleep (hrs)',
                    data: lightSleep,
                    backgroundColor: '#a5b4fc',
                    borderRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', align: 'end' },
                tooltip: {
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw} hrs`
                    }
                }
            },
            scales: {
                x: { stacked: true, grid: { display: false } },
                y: {
                    stacked: true,
                    suggestedMax: 10,
                    grid: { color: 'rgba(226, 232, 240, 0.6)' },
                    ticks: { callback: (v) => `${v}h` }
                }
            }
        }
    });
}
