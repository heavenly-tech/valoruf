// app.js
// Dynamically determine the base host (protocol://domain:port)
const BASE_HOST = window.location.protocol + '//' + window.location.host;
// The API endpoints are all under /api/uf, make this the base URL
const API_BASE_URL = BASE_HOST + '/api/uf';

const tableBody = document.getElementById('data-table-body');
const loadingElement = document.getElementById('loading');
const tableWrapper = document.getElementById('table-wrapper');
const errorMessageElement = document.getElementById('error-message');

const singleDateForm = document.getElementById('single-date-form');
const rangeDateForm = document.getElementById('range-date-form');
const showTodayBtn = document.getElementById('show-today-btn');
const showLast7DaysBtn = document.getElementById('show-last-7-days-btn');
const showCachedBtn = document.getElementById('show-cached-btn');


/**
 * Formats a date string.
 * @param {string} dateString 
 * @returns {string}
 */
function formatDate(dateString) {
    return dateString; // API returns in 'YYYY-MM-DD'
}

/**
 * Fetches data from the API based on the constructed URL and renders the table.
 * @param {string} url - The full API URL.
 */
async function fetchDataAndRender(url) {
    loadingElement.classList.remove('hidden');
    tableWrapper.classList.add('hidden');
    errorMessageElement.classList.add('hidden');

    try {
        const response = await fetch(url);
        if (!response.ok) {
            // Attempt to parse JSON error message
            try {
                const err = await response.json();
                throw new Error(err.error || `HTTP error! status: ${response.status}`);
            } catch {
                // If response body is not JSON, use generic error
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        }
        const data = await response.json();
        
        let dataArray = Array.isArray(data) ? data : [data];

        let html = '';
        
        if (dataArray.length === 0 || (dataArray.length > 0 && dataArray[0].date === undefined)) {
             html = `<tr><td colspan="2" class="px-6 py-6 text-center text-gray-500 italic bg-gray-50">No se encontraron datos para las fechas solicitadas.</td></tr>`;
        } else {
            // Sort data by date descending (newest first)
            dataArray.sort((a, b) => b.date.localeCompare(a.date));

            dataArray.forEach(item => {
                const formattedDate = formatDate(item.date);
                const value = typeof item.value === 'number' ? item.value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : 'N/A';

                html += `
                    <tr class="transition duration-100 even:bg-gray-50 hover:bg-gray-100">
                        <td class="px-6 py-3 whitespace-nowrap text-sm font-medium text-text-dark">${formattedDate}</td>
                        <td class="px-6 py-3 whitespace-nowrap text-sm text-right font-mono text-primary-blue font-bold">${value}</td>
                    </tr>
                `;
            });
        }

        tableBody.innerHTML = html;
        tableWrapper.classList.remove('hidden');

    } catch (error) {
        console.error("Error fetching data from API:", error);
        errorMessageElement.textContent = `Error al obtener los datos: ${error.message}`;
        errorMessageElement.classList.remove('hidden');
    } finally {
        loadingElement.classList.add('hidden');
    }
}

// --- Event Listeners for Forms ---

// 1. Single Date Search
singleDateForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const dateInput = document.getElementById('single-date-input').value;
    if (dateInput) {
        const url = `${API_BASE_URL}/${dateInput}`;
        fetchDataAndRender(url);
    }
});

// 2. Date Range Search
rangeDateForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const startDate = document.getElementById('start-date-input').value;
    const endDate = document.getElementById('end-date-input').value;
    
    if (startDate && endDate) {
        const url = `${API_BASE_URL}/${startDate}/${endDate}`;
        fetchDataAndRender(url);
    }
});

// 3. Show Today Button
showTodayBtn.addEventListener('click', () => {
    const todayStr = new Date().toISOString().split('T')[0];
    const url = `${API_BASE_URL}/${todayStr}`;
    fetchDataAndRender(url);
});

// 4. Show Last 7 Days Button
showLast7DaysBtn.addEventListener('click', () => {
     const endDate = new Date();
     const startDate = new Date();
     startDate.setDate(endDate.getDate() - 6);
     
     const endDateStr = endDate.toISOString().split('T')[0];
     const startDateStr = startDate.toISOString().split('T')[0];

     const url = `${API_BASE_URL}/${startDateStr}/${endDateStr}`;
     fetchDataAndRender(url);
});

// 5. Show All Cached Values Button
showCachedBtn.addEventListener('click', () => {
    const url = `${API_BASE_URL}/cached`;
    fetchDataAndRender(url);
});

// Fetch default data on initial page load (last 7 days)
document.addEventListener('DOMContentLoaded', () => {
    showLast7DaysBtn.click();
});
