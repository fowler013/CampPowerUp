function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
    const text = document.createElement('span');
    text.textContent = message;
    const close = document.createElement('button');
    close.className = 'close-btn';
    close.type = 'button';
    close.setAttribute('aria-label', 'Dismiss notification');
    close.textContent = '×';
    close.addEventListener('click', () => toast.remove());
    toast.append(text, close);
    document.body.append(toast);
    requestAnimationFrame(() => toast.classList.add('show'));
    setTimeout(() => toast.remove(), 8000);
}

function searchRegistrations() {
    const term = document.getElementById('searchInput').value.trim().toLowerCase();
    const cards = document.querySelectorAll('.registration-card');
    let count = 0;
    cards.forEach(card => {
        const matches = card.dataset.searchText.toLowerCase().includes(term);
        card.hidden = !matches;
        if (matches) count += 1;
    });
    document.getElementById('searchStatus').textContent =
        `${count} of ${cards.length} registrations shown. Summary totals are for the selected session.`;
    document.getElementById('noSearchResults').hidden = count !== 0 || cards.length === 0;
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    searchRegistrations();
}

async function registrationAction(button) {
    if (button.disabled) return;
    const action = button.dataset.action;
    const prompts = {
        paid: 'Mark this registration as fully paid?',
        reminder: 'Send one payment reminder email to this registration’s parent or guardian?',
        delete: 'Delete this registration permanently? This cannot be undone.',
    };
    if (!Object.hasOwn(prompts, action) || !confirm(prompts[action])) return;
    const routes = {paid: 'mark-paid', reminder: 'send-reminder', delete: 'delete'};
    const label = button.textContent;
    button.disabled = true;
    button.textContent = 'Working…';
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
        const response = await fetch(
            `/admin/${routes[action]}/${encodeURIComponent(button.dataset.id)}${location.search}`,
            {
                method: 'POST',
                signal: controller.signal,
                headers: {
                    Accept: 'application/json',
                    'X-CSRF-Token': document.querySelector('meta[name="admin-csrf-token"]').content,
                },
            }
        );
        if (response.redirected || response.status === 401) {
            throw new Error('Your admin session expired. Sign in again, then reload this page.');
        }
        if (!response.headers.get('content-type')?.includes('application/json')) {
            throw new Error('The server returned an unexpected response. Check the record before trying again.');
        }
        const result = await response.json();
        if (!response.ok || result.success !== true) {
            throw new Error(result.error || 'The action was not completed.');
        }
        showToast(result.message || 'Action completed.');
        if (action !== 'reminder') setTimeout(() => location.reload(), 600);
    } catch (error) {
        showToast(
            error.name === 'AbortError'
                ? 'The request timed out. Check whether it completed before trying again.'
                : error.message,
            'error'
        );
    } finally {
        clearTimeout(timer);
        button.disabled = false;
        button.textContent = label;
    }
}

document.getElementById('searchInput').addEventListener('input', searchRegistrations);
document.getElementById('registrationsList').addEventListener('click', event => {
    const button = event.target.closest('button[data-action]');
    if (button) registrationAction(button);
});
searchRegistrations();
