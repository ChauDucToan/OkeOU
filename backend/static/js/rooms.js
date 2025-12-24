let debounceTimer;
const DEBOUNCE_DELAY = 2000;

function triggerDebounce() {
    clearTimeout(debounceTimer);

    debounceTimer = setTimeout(() => {
        searchRooms();
    }, DEBOUNCE_DELAY);
}

function handleSearchInput() {
    triggerDebounce();
}

function handleSliderChange(input, displayId) {
    document.getElementById(displayId).innerText = input.value;
    triggerDebounce();
}

function resetFilters() {
    window.location.href = window.location.pathname;
}

function searchRooms() {
    const keyword = document.getElementById('searchInput').value;
    const priceMax = document.getElementById('range2').value;
    const capacity = document.getElementById('range3').value;
    const sort = document.getElementById('sortSelect').value;

    const url = new URL(window.location.href);

    if (keyword) url.searchParams.set('kw', keyword);
    else url.searchParams.delete('kw');

    url.searchParams.set('price_max', priceMax);
    url.searchParams.set('capacity', capacity);
    url.searchParams.set('sort', sort);
    url.searchParams.set('page', 1);

    window.location.href = url.toString();
}