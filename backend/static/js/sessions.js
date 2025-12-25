let debounceTimer;
const DEBOUNCE_DELAY = 1000;

function triggerDebounce() {
    clearTimeout(debounceTimer);

    debounceTimer = setTimeout(() => {
        searchSessions();
    }, DEBOUNCE_DELAY);
}

function handleSearchInput() {
    triggerDebounce();
}

function resetFilters() {
    window.location.href = window.location.pathname;
}

function searchSessions() {
    const keyword = document.getElementById('searchInput').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const status = document.getElementById('statusSelect').value;

    const url = new URL(window.location.href);

    if (keyword) url.searchParams.set('kw', keyword);
    else url.searchParams.delete('kw');

    if (startDate) url.searchParams.set('start_date', startDate);
    else url.searchParams.delete('start_date');

    if (endDate) url.searchParams.set('end_date', endDate);
    else url.searchParams.delete('end_date');

    if (status) url.searchParams.set('status', status);
    else url.searchParams.delete('status');

    url.searchParams.set('page', 1);

    window.location.href = url.toString();
}

function pageinateSessions(page) {
    const url = new URL(window.location.href);
    url.searchParams.set('page', page);
    window.location.href = url.toString();
}