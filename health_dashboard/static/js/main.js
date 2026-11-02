/**
 * Main Application JavaScript
 * Global utilities, Toast alerts, and Sample data loaders
 */

document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Mobile Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const appSidebar = document.getElementById('appSidebar');
    if (sidebarToggleBtn && appSidebar) {
        sidebarToggleBtn.addEventListener('click', () => {
            appSidebar.classList.toggle('show');
        });
    }

    // Auto-dismiss standard alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // Global "Load Demo Sample Data" button listener
    const demoLoadBtns = document.querySelectorAll('.btn-load-sample-data');
    demoLoadBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            btn.disabled = true;
            const originalHtml = btn.innerHTML;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-1"></span> Loading 90 Days Data...`;
            
            try {
                const response = await fetch('/api/load-sample-data', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                const data = await response.json();
                if (data.success) {
                    showToast(`Successfully loaded ${data.processed_rows} wearable records!`, 'success');
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1000);
                } else {
                    showToast(data.error || 'Failed to load sample data', 'danger');
                    btn.disabled = false;
                    btn.innerHTML = originalHtml;
                }
            } catch (err) {
                showToast(`Request failed: ${err.message}`, 'danger');
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        });
    });
});

/**
 * Universal Toast Notification Generator
 */
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success text-white' :
                    type === 'danger' ? 'bg-danger text-white' :
                    type === 'warning' ? 'bg-warning text-dark' : 'bg-primary text-white';

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 shadow-lg" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center gap-2">
                    <i class="bi bi-info-circle-fill"></i>
                    <span>${message}</span>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);
    const toastEl = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastEl, { delay: 4500 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}
