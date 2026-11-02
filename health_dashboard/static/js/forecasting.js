/**
 * Module 5: Time-Series Health Forecasting
 * Interactive metric switching, Chart.js multi-series forecasting, and RMSE display.
 */

let forecastChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    const metricSelect = document.getElementById('forecastMetricSelect');
    const horizonSelect = document.getElementById('forecastHorizonSelect');
    const btnRunForecast = document.getElementById('btnRunForecast');

    if (!document.getElementById('forecastChart')) return;

    // Load initial forecast for steps
    loadForecast('steps', 7);

    if (btnRunForecast) {
        btnRunForecast.addEventListener('click', () => {
            const m = metricSelect.value;
            const h = horizonSelect.value;
            loadForecast(m, h);
        });
    }

    if (metricSelect) {
        metricSelect.addEventListener('change', () => {
            loadForecast(metricSelect.value, horizonSelect ? horizonSelect.value : 7);
        });
    }
});

async function loadForecast(metric = 'steps', horizon = 7) {
    const chartContainer = document.getElementById('forecastChartContainer');
    const statusContainer = document.getElementById('forecastStatusContainer');
    const evalRmse = document.getElementById('evalRmse');
    const evalMae = document.getElementById('evalMae');
    const evalInterp = document.getElementById('evalInterp');
    const futureTableBody = document.getElementById('futureForecastTableBody');

    try {
        const response = await fetch(`/api/forecast?metric=${metric}&horizon=${horizon}`);
        const res = await response.json();

        if (!res.success) {
            if (chartContainer) chartContainer.classList.add('d-none');
            if (statusContainer) {
                statusContainer.classList.remove('d-none');
                statusContainer.innerHTML = `
                    <div class="alert alert-warning border-0 shadow-sm d-flex align-items-center gap-3 p-4 rounded-4">
                        <i class="bi bi-exclamation-triangle-fill fs-2 text-warning"></i>
                        <div>
                            <h5 class="fw-bold mb-1">Insufficient Data for Forecasting</h5>
                            <p class="mb-2 text-muted">${res.error}</p>
                            <a href="/upload" class="btn btn-sm btn-primary-custom">Upload Wearable Dataset</a>
                            <button class="btn btn-sm btn-outline-secondary ms-2 btn-load-sample-data">Load 90-Day Sample</button>
                        </div>
                    </div>
                `;
            }
            return;
        }

        if (statusContainer) statusContainer.classList.add('d-none');
        if (chartContainer) chartContainer.classList.remove('d-none');

        // Update Evaluation Metrics
        if (evalRmse) evalRmse.textContent = `${res.evaluation.rmse} ${res.metric_meta.unit}`;
        if (evalMae) evalMae.textContent = `${res.evaluation.mae} ${res.metric_meta.unit}`;
        if (evalInterp) evalInterp.textContent = res.evaluation.interpretation;

        // Render Chart.js Multi-series Forecast
        renderForecastChart(res);

        // Render Future Forecast Day-by-day Table
        if (futureTableBody) {
            futureTableBody.innerHTML = res.forecast.dates.map((dateStr, i) => {
                const pred = res.forecast.predicted[i];
                const lower = res.forecast.lower_bound[i];
                const upper = res.forecast.upper_bound[i];
                return `
                    <tr>
                        <td class="fw-semibold">${dateStr}</td>
                        <td class="text-primary fw-bold">${pred} ${res.metric_meta.unit}</td>
                        <td class="text-muted small">${lower} ${res.metric_meta.unit}</td>
                        <td class="text-muted small">${upper} ${res.metric_meta.unit}</td>
                        <td><span class="badge bg-light text-secondary border">± ${(pred - lower).toFixed(1)}</span></td>
                    </tr>
                `;
            }).join('');
        }
    } catch (err) {
        console.error('Forecasting error:', err);
    }
}

function renderForecastChart(res) {
    const ctx = document.getElementById('forecastChart').getContext('2d');
    if (forecastChartInstance) forecastChartInstance.destroy();

    const histDates = res.historical.dates;
    const histValues = res.historical.values;
    const futureDates = res.forecast.dates;
    const futureValues = res.forecast.predicted;
    const futureLower = res.forecast.lower_bound;
    const futureUpper = res.forecast.upper_bound;

    // Combine all labels chronologically
    const allLabels = [...histDates, ...futureDates];

    // Align historical dataset (pad end with nulls)
    const alignedHist = [...histValues, ...new Array(futureDates.length).fill(null)];

    // Align future forecast dataset (pad start with nulls, connect to last historical point)
    const alignedFuture = new Array(histDates.length - 1).fill(null);
    alignedFuture.push(histValues[histValues.length - 1]); // Anchor point
    alignedFuture.push(...futureValues);

    const alignedUpper = new Array(histDates.length - 1).fill(null);
    alignedUpper.push(histValues[histValues.length - 1]);
    alignedUpper.push(...futureUpper);

    const alignedLower = new Array(histDates.length - 1).fill(null);
    alignedLower.push(histValues[histValues.length - 1]);
    alignedLower.push(...futureLower);

    forecastChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allLabels,
            datasets: [
                {
                    label: `Historical Actuals (${res.metric_meta.unit})`,
                    data: alignedHist,
                    borderColor: '#0284c7',
                    borderWidth: 2,
                    pointRadius: 2,
                    fill: false,
                    tension: 0.2
                },
                {
                    label: `7-Day ML Forecast (${res.metric_meta.unit})`,
                    data: alignedFuture,
                    borderColor: '#0d9488',
                    backgroundColor: 'rgba(13, 148, 136, 0.1)',
                    borderWidth: 2.8,
                    borderDash: [5, 4],
                    pointRadius: 4,
                    pointBackgroundColor: '#0d9488',
                    tension: 0.2
                },
                {
                    label: 'Confidence Upper Bound',
                    data: alignedUpper,
                    borderColor: 'rgba(148, 163, 184, 0.4)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: 'Confidence Lower Bound',
                    data: alignedLower,
                    borderColor: 'rgba(148, 163, 184, 0.4)',
                    backgroundColor: 'rgba(226, 232, 240, 0.4)',
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: '-1' // fills area between lower and upper
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
                        label: (ctx) => `${ctx.dataset.label}: ${ctx.raw !== null ? ctx.raw : '-'} ${res.metric_meta.unit}`
                    }
                }
            },
            scales: {
                y: {
                    grid: { color: 'rgba(226, 232, 240, 0.6)' },
                    ticks: { callback: (v) => `${v} ${res.metric_meta.unit}` }
                },
                x: {
                    grid: { display: false },
                    ticks: { maxTicksLimit: 12 }
                }
            }
        }
    });
}
