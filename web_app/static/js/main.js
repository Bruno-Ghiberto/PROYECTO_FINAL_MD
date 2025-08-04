// Sistema Solar Explorer - Main Dashboard Controller
// =================================================

// Global state
let currentPage = 1;
let currentFilters = {
    category: '',
    anomaly: false,
    minRadius: null,
    maxRadius: null,
    search: ''
};
let currentObjects = [];
let selectedObject = null;
let isLoading = false;

// API Base URL
const API_BASE = '/api';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Sistema Solar Explorer...');
    
    // Load dashboard stats
    loadDashboardStats();
    
    // Load initial objects
    loadObjects();
    
    // Setup event listeners
    setupEventListeners();
    
    // Check URL parameters for direct object view
    const urlParams = new URLSearchParams(window.location.search);
    const objectId = urlParams.get('object');
    if (objectId) {
        setTimeout(() => selectObject(objectId), 500);
    }
});

// Setup all event listeners
function setupEventListeners() {
    // Search input
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchObjects();
            }
        });
    }
    
    // Category filter
    const categorySelect = document.getElementById('categorySelect');
    if (categorySelect) {
        categorySelect.addEventListener('change', applyFilters);
    }
    
    // Anomaly checkbox
    const anomalyCheck = document.getElementById('anomalyCheck');
    if (anomalyCheck) {
        anomalyCheck.addEventListener('change', applyFilters);
    }
    
    // Size range inputs
    const minRadiusInput = document.getElementById('minRadiusInput');
    const maxRadiusInput = document.getElementById('maxRadiusInput');
    if (minRadiusInput) minRadiusInput.addEventListener('change', applyFilters);
    if (maxRadiusInput) maxRadiusInput.addEventListener('change', applyFilters);
}

// Load objects with filters
async function loadObjects(page = 1) {
    if (isLoading) return;
    
    currentPage = page;
    isLoading = true;
    
    const objectsList = document.getElementById('objectsList');
    objectsList.innerHTML = `
        <div class="text-center p-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando objetos...</span>
            </div>
            <p class="text-muted mt-2">Cargando datos del sistema solar...</p>
        </div>
    `;
    
    try {
        const params = new URLSearchParams({
            page: page,
            page_size: 50
        });
        
        // Add filters
        if (currentFilters.category) params.append('category', currentFilters.category);
        if (currentFilters.anomaly) params.append('anomaly', 'true');
        if (currentFilters.minRadius) params.append('min_radius', currentFilters.minRadius);
        if (currentFilters.maxRadius) params.append('max_radius', currentFilters.maxRadius);
        if (currentFilters.search) params.append('search', currentFilters.search);
        
        const response = await fetch(`${API_BASE}/objects?${params}`);
        const data = await response.json();
        
        if (data.success) {
            currentObjects = data.data;
            displayObjects(data);
            updatePagination(data.pagination);
            document.getElementById('resultsCount').textContent = data.pagination.total;
        } else {
            throw new Error(data.error || 'Failed to load objects');
        }
    } catch (error) {
        console.error('Error loading objects:', error);
        objectsList.innerHTML = `
            <div class="alert alert-danger m-3" role="alert">
                <i class="bi bi-exclamation-triangle"></i> Error al cargar objetos: ${error.message}
            </div>
        `;
    } finally {
        isLoading = false;
    }
}

// Display objects in the list
function displayObjects(data) {
    const objectsList = document.getElementById('objectsList');
    
    if (!data.data || data.data.length === 0) {
        objectsList.innerHTML = `
            <div class="text-center p-4 text-muted">
                <i class="bi bi-search fs-1"></i>
                <p class="mt-2">No se encontraron objetos con los filtros seleccionados</p>
            </div>
        `;
        return;
    }
    
    const objectsHtml = data.data.map(obj => {
        // Determine object icon and color
        const categoryInfo = getCategoryInfo(obj.ui_category || obj.object_type);
        
        // Format size
        let sizeText = 'Tamaño desconocido';
        if (obj.mean_radius_km) {
            sizeText = `Radio: ${formatNumber(obj.mean_radius_km)} km`;
        } else if (obj.diameter_km) {
            sizeText = `Diám: ${formatNumber(obj.diameter_km)} km`;
        }
        
        // Check if anomaly
        const isAnomaly = obj.is_anomaly === true || obj.is_anomaly === 'true';
        
        return `
            <a href="#" class="list-group-item list-group-item-action ${selectedObject?.id === obj.id ? 'active' : ''}" 
               onclick="selectObject('${obj.id}'); return false;"
               data-object-id="${obj.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            <i class="bi ${categoryInfo.icon} ${categoryInfo.color} me-2"></i>
                            <h6 class="mb-0">
                                ${obj.display_name || obj.name}
                                ${isAnomaly ? '<span class="badge bg-warning ms-2" title="Objeto anómalo"><i class="bi bi-exclamation-triangle"></i></span>' : ''}
                            </h6>
                        </div>
                        <div class="d-flex align-items-center">
                            <span class="badge ${categoryInfo.badgeClass} me-2">${obj.ui_category || obj.object_type || 'Desconocido'}</span>
                            <small class="text-muted">${sizeText}</small>
                        </div>
                    </div>
                    <div class="text-end">
                        ${obj.has_image ? '<i class="bi bi-image text-success" title="Tiene imagen"></i>' : ''}
                        ${obj.is_neo ? '<span class="badge bg-danger" title="Near Earth Object">NEO</span>' : ''}
                        ${obj.is_pha ? '<span class="badge bg-danger" title="Potentially Hazardous">PHA</span>' : ''}
                    </div>
                </div>
            </a>
        `;
    }).join('');
    
    objectsList.innerHTML = objectsHtml;
}

// Select and display object details
async function selectObject(objectId) {
    console.log('Selecting object:', objectId);
    
    // Update UI
    document.getElementById('welcomeMessage').style.display = 'none';
    document.getElementById('objectDetail').style.display = 'block';
    
    // Update selected state in list
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
    });
    const selectedItem = document.querySelector(`[data-object-id="${objectId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
        selectedItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    // Show loading state
    showDetailLoading();
    
    try {
        const response = await fetch(`${API_BASE}/objects/${objectId}`);
        const result = await response.json();
        
        if (result.success) {
            selectedObject = result.data;
            displayObjectDetail(result.data);
        } else {
            throw new Error(result.error || 'Failed to load object details');
        }
    } catch (error) {
        console.error('Error loading object details:', error);
        showDetailError(error.message);
    }
}

// Display detailed object information
function displayObjectDetail(obj) {
    console.log('Displaying object:', obj);
    
    // Update header
    document.getElementById('objectName').textContent = obj.display_name || obj.name;
    document.getElementById('objectType').textContent = obj.ui_category || obj.object_type || 'Objeto Desconocido';
    document.getElementById('objectId').textContent = `ID: ${obj.id}`;
    
    // Update image
    const imageContainer = document.getElementById('objectImage');
    if (obj.image && obj.image.url) {
        const imageSource = obj.image.is_local ? 'Imagen local' : obj.image.source || 'NASA';
        imageContainer.innerHTML = `
            <img src="${obj.image.url}" alt="${obj.name}" class="img-fluid rounded shadow">
            <small class="text-muted d-block mt-1 text-center">${imageSource}</small>
        `;
    } else {
        const categoryInfo = getCategoryInfo(obj.ui_category || obj.object_type);
        imageContainer.innerHTML = `
            <div class="placeholder-image bg-secondary rounded d-flex align-items-center justify-content-center" style="height: 200px;">
                <div class="text-center text-white-50">
                    <i class="bi ${categoryInfo.icon} fs-1"></i>
                    <p class="mt-2 mb-0">Sin imagen disponible</p>
                </div>
            </div>
        `;
    }
    
    // Update physical properties
    updatePhysicalProperties(obj);
    
    // Update orbital properties
    updateOrbitalProperties(obj);
    
    // Update discovery info if available
    updateDiscoveryInfo(obj);
    
    // Update classification badges
    updateClassificationBadges(obj);
    
    // Display Horizons data if available
    if (obj.orbital_data) {
        displayHorizonsData(obj.orbital_data);
    } else {
        document.getElementById('horizonsSection').style.display = 'none';
    }
    
    // Create visualization
    createOrbitalChart(obj);
}

// Update physical properties table
function updatePhysicalProperties(obj) {
    const tbody = document.getElementById('physicalProperties');
    const properties = [];
    
    // Size
    if (obj.mean_radius_km) {
        properties.push(['Radio medio', `${formatNumber(obj.mean_radius_km)} km`]);
    } else if (obj.diameter_km) {
        properties.push(['Diámetro', `${formatNumber(obj.diameter_km)} km`]);
    }
    
    // Mass
    if (obj.mass_kg) {
        properties.push(['Masa', formatScientific(obj.mass_kg) + ' kg']);
    }
    
    // Density
    if (obj.density_g_cm3) {
        properties.push(['Densidad', `${formatNumber(obj.density_g_cm3)} g/cm³`]);
    }
    
    // Gravity
    if (obj.gravity_m_s2) {
        properties.push(['Gravedad', `${formatNumber(obj.gravity_m_s2)} m/s²`]);
    }
    
    // Escape velocity
    if (obj.escape_velocity_km_s) {
        properties.push(['Velocidad de escape', `${formatNumber(obj.escape_velocity_km_s)} km/s`]);
    }
    
    // Temperature
    if (obj.avg_temperature_k) {
        properties.push(['Temperatura promedio', `${formatNumber(obj.avg_temperature_k)} K`]);
    }
    
    // Rotation period
    if (obj.rotation_period_h) {
        properties.push(['Período de rotación', `${formatNumber(obj.rotation_period_h)} horas`]);
    }
    
    // Albedo
    if (obj.albedo) {
        properties.push(['Albedo', formatNumber(obj.albedo)]);
    }
    
    tbody.innerHTML = properties.map(([label, value]) => 
        `<tr><td class="text-muted">${label}</td><td><strong>${value}</strong></td></tr>`
    ).join('');
    
    if (properties.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">Sin datos físicos disponibles</td></tr>';
    }
}

// Update orbital properties table
function updateOrbitalProperties(obj) {
    const tbody = document.getElementById('orbitalProperties');
    const properties = [];
    
    // Semimajor axis
    if (obj.semimajor_axis_au) {
        properties.push(['Semieje mayor', `${formatNumber(obj.semimajor_axis_au)} AU`]);
    }
    
    // Eccentricity
    if (obj.eccentricity !== null && obj.eccentricity !== undefined) {
        properties.push(['Excentricidad', formatNumber(obj.eccentricity, 4)]);
    }
    
    // Inclination
    if (obj.inclination_deg !== null && obj.inclination_deg !== undefined) {
        properties.push(['Inclinación', `${formatNumber(obj.inclination_deg)}°`]);
    }
    
    // Orbital period
    if (obj.orbital_period_days) {
        const years = obj.orbital_period_days / 365.25;
        if (years > 1) {
            properties.push(['Período orbital', `${formatNumber(years)} años`]);
        } else {
            properties.push(['Período orbital', `${formatNumber(obj.orbital_period_days)} días`]);
        }
    }
    
    // Perihelion
    if (obj.perihelion_distance_au) {
        properties.push(['Perihelio', `${formatNumber(obj.perihelion_distance_au)} AU`]);
    }
    
    // Aphelion
    if (obj.aphelion_distance_au) {
        properties.push(['Afelio', `${formatNumber(obj.aphelion_distance_au)} AU`]);
    }
    
    // Mean anomaly
    if (obj.mean_anomaly_deg !== null && obj.mean_anomaly_deg !== undefined) {
        properties.push(['Anomalía media', `${formatNumber(obj.mean_anomaly_deg)}°`]);
    }
    
    tbody.innerHTML = properties.map(([label, value]) => 
        `<tr><td class="text-muted">${label}</td><td><strong>${value}</strong></td></tr>`
    ).join('');
    
    if (properties.length === 0) {
        tbody.innerHTML = '<tr><td colspan="2" class="text-center text-muted">Sin datos orbitales disponibles</td></tr>';
    }
}

// Update discovery information
function updateDiscoveryInfo(obj) {
    const container = document.getElementById('discoveryInfo');
    if (!container) return;
    
    if (obj.discovery && (obj.discovery.discoverer || obj.discovery.date)) {
        let html = '<h6 class="text-muted mb-2">Descubrimiento</h6><ul class="list-unstyled small">';
        
        if (obj.discovery.discoverer) {
            html += `<li><strong>Descubridor:</strong> ${obj.discovery.discoverer}</li>`;
        }
        
        if (obj.discovery.date) {
            html += `<li><strong>Fecha:</strong> ${obj.discovery.date}</li>`;
        }
        
        html += '</ul>';
        container.innerHTML = html;
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

// Update classification badges
function updateClassificationBadges(obj) {
    const container = document.getElementById('classificationBadges');
    if (!container) return;
    
    const badges = [];
    
    if (obj.classification) {
        if (obj.classification.is_neo) {
            badges.push('<span class="badge bg-warning">NEO</span>');
        }
        if (obj.classification.is_pha) {
            badges.push('<span class="badge bg-danger">PHA</span>');
        }
        if (obj.classification.is_anomaly) {
            badges.push(`<span class="badge bg-info">Anomalía: ${obj.classification.anomaly_type || 'Detectada'}</span>`);
        }
    }
    
    if (badges.length > 0) {
        container.innerHTML = badges.join(' ');
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

// Display Horizons data
function displayHorizonsData(data) {
    const section = document.getElementById('horizonsSection');
    const content = document.getElementById('horizonsData');
    
    if (!data || data.source !== 'horizons') {
        section.style.display = 'none';
        return;
    }
    
    section.style.display = 'block';
    
    let html = '<div class="row small">';
    
    if (data.absolute_magnitude !== undefined) {
        html += `
            <div class="col-md-6 mb-2">
                <span class="text-muted">Magnitud absoluta:</span>
                <strong>${formatNumber(data.absolute_magnitude)}</strong>
            </div>
        `;
    }
    
    if (data.diameter_km) {
        html += `
            <div class="col-md-6 mb-2">
                <span class="text-muted">Diámetro (Horizons):</span>
                <strong>${formatNumber(data.diameter_km)} km</strong>
            </div>
        `;
    }
    
    if (data.rotation_period_hours) {
        html += `
            <div class="col-md-6 mb-2">
                <span class="text-muted">Rotación (Horizons):</span>
                <strong>${formatNumber(data.rotation_period_hours)} h</strong>
            </div>
        `;
    }
    
    html += `
        <div class="col-12">
            <small class="text-muted">
                <i class="bi bi-info-circle"></i> 
                Datos obtenidos de NASA JPL Horizons
            </small>
        </div>
    `;
    
    html += '</div>';
    content.innerHTML = html;
}

// Create orbital visualization
function createOrbitalChart(obj) {
    const chartDiv = document.getElementById('orbitalChart');
    
    if (!obj.semimajor_axis_au || obj.eccentricity === null || obj.eccentricity === undefined) {
        chartDiv.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="bi bi-graph-down fs-1"></i>
                <p class="mt-2">Datos orbitales insuficientes para visualización</p>
            </div>
        `;
        return;
    }
    
    // Create scatter plot
    const objectTrace = {
        x: [obj.semimajor_axis_au],
        y: [obj.eccentricity],
        mode: 'markers',
        type: 'scatter',
        name: obj.name,
        marker: {
            size: 14,
            color: '#ff4444',
            line: { color: 'white', width: 2 }
        },
        text: [`${obj.name}<br>a: ${formatNumber(obj.semimajor_axis_au)} AU<br>e: ${formatNumber(obj.eccentricity)}`],
        hovertemplate: '%{text}<extra></extra>'
    };
    
    // Reference planets
    const planets = [
        {name: 'Mercurio', a: 0.387, e: 0.206, color: '#8B7355'},
        {name: 'Venus', a: 0.723, e: 0.007, color: '#FFC649'},
        {name: 'Tierra', a: 1.0, e: 0.017, color: '#4169E1'},
        {name: 'Marte', a: 1.524, e: 0.093, color: '#CD5C5C'},
        {name: 'Júpiter', a: 5.203, e: 0.048, color: '#DAA520'},
        {name: 'Saturno', a: 9.537, e: 0.054, color: '#F4A460'},
        {name: 'Urano', a: 19.191, e: 0.047, color: '#4FD0E0'},
        {name: 'Neptuno', a: 30.069, e: 0.009, color: '#4169E1'}
    ];
    
    const planetsTrace = {
        x: planets.map(p => p.a),
        y: planets.map(p => p.e),
        mode: 'markers+text',
        type: 'scatter',
        name: 'Planetas',
        marker: {
            size: 10,
            color: planets.map(p => p.color),
            line: { color: 'white', width: 1 }
        },
        text: planets.map(p => p.name),
        textposition: 'top center',
        textfont: { size: 10 },
        hovertemplate: '%{text}<br>a: %{x} AU<br>e: %{y}<extra></extra>'
    };
    
    const layout = {
        title: {
            text: 'Comparación Orbital',
            font: { size: 16 }
        },
        xaxis: {
            title: 'Semieje Mayor (AU)',
            type: 'log',
            gridcolor: '#e0e0e0',
            range: [-0.5, 2]
        },
        yaxis: {
            title: 'Excentricidad',
            gridcolor: '#e0e0e0',
            range: [-0.05, Math.max(0.5, obj.eccentricity * 1.2)]
        },
        hovermode: 'closest',
        plot_bgcolor: '#fafafa',
        paper_bgcolor: 'white',
        showlegend: true,
        legend: {
            x: 0.7,
            y: 0.95,
            bgcolor: 'rgba(255, 255, 255, 0.8)'
        },
        margin: { t: 40, r: 20, b: 40, l: 60 }
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot(chartDiv, [objectTrace, planetsTrace], layout, config);
}

// Dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await fetch(`${API_BASE}/stats`);
        const result = await response.json();
        
        if (result.success) {
            const stats = result.data;
            
            // Update stats cards
            document.getElementById('totalObjectsCount').textContent = formatNumber(stats.total_objects);
            document.getElementById('anomaliesCount').textContent = formatNumber(stats.anomalies_detected);
            
            // Setup stats modal
            const statsModal = document.getElementById('statsModal');
            if (statsModal) {
                statsModal.addEventListener('show.bs.modal', function() {
                    displayStatsModal(stats);
                });
            }
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Display statistics in modal
function displayStatsModal(stats) {
    const content = document.getElementById('statsContent');
    
    let html = '<div class="row">';
    
    // Category breakdown
    html += `
        <div class="col-md-6">
            <h6 class="mb-3">Objetos por Categoría</h6>
            <ul class="list-unstyled">
    `;
    
    for (const [category, count] of Object.entries(stats.by_category || {})) {
        const categoryInfo = getCategoryInfo(category);
        const percentage = ((count / stats.total_objects) * 100).toFixed(1);
        html += `
            <li class="mb-2">
                <i class="bi ${categoryInfo.icon} ${categoryInfo.color}"></i>
                <strong>${category}:</strong> ${formatNumber(count)}
                <small class="text-muted">(${percentage}%)</small>
            </li>
        `;
    }
    
    html += '</ul></div>';
    
    // Data sources
    html += `
        <div class="col-md-6">
            <h6 class="mb-3">Fuentes de Datos</h6>
            <ul class="list-unstyled">
    `;
    
    for (const [source, count] of Object.entries(stats.data_sources || {})) {
        html += `<li class="mb-2"><strong>${source}:</strong> ${formatNumber(count)}</li>`;
    }
    
    html += '</ul>';
    
    // Additional stats
    html += `
        <div class="col-12 mt-3">
            <h6>Estadísticas Adicionales</h6>
            <div class="row">
                <div class="col-6">
                    <p class="mb-1"><strong>Objetos con imágenes:</strong> ${stats.with_images || 'N/A'}</p>
                    <p class="mb-1"><strong>Objetos con clustering:</strong> ${stats.has_clustering || 0}</p>
                </div>
                <div class="col-6">
                    <p class="mb-1"><strong>Anomalías detectadas:</strong> ${formatNumber(stats.anomalies_detected)}</p>
                    <p class="mb-1"><strong>Última actualización:</strong> ${new Date(stats.last_updated).toLocaleDateString()}</p>
                </div>
            </div>
        </div>
    `;
    
    html += '</div></div>';
    
    content.innerHTML = html;
}

// Filter functions
function applyFilters() {
    currentFilters.category = document.getElementById('categorySelect').value;
    currentFilters.anomaly = document.getElementById('anomalyCheck').checked;
    currentFilters.minRadius = parseFloat(document.getElementById('minRadiusInput').value) || null;
    currentFilters.maxRadius = parseFloat(document.getElementById('maxRadiusInput').value) || null;
    
    loadObjects(1);
}

function searchObjects() {
    currentFilters.search = document.getElementById('searchInput').value;
    loadObjects(1);
}

function resetFilters() {
    document.getElementById('categorySelect').value = '';
    document.getElementById('anomalyCheck').checked = false;
    document.getElementById('minRadiusInput').value = '';
    document.getElementById('maxRadiusInput').value = '';
    document.getElementById('searchInput').value = '';
    
    currentFilters = {
        category: '',
        anomaly: false,
        minRadius: null,
        maxRadius: null,
        search: ''
    };
    
    loadObjects(1);
}

function clearSelection() {
    selectedObject = null;
    document.getElementById('objectDetail').style.display = 'none';
    document.getElementById('welcomeMessage').style.display = 'block';
    document.querySelectorAll('.list-group-item').forEach(item => {
        item.classList.remove('active');
    });
}

// Pagination
function updatePagination(pagination) {
    const paginationEl = document.getElementById('pagination');
    const totalPages = pagination.total_pages;
    const currentPage = pagination.page;
    
    let html = '';
    
    // Previous button
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadObjects(${currentPage - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    if (startPage > 1) {
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadObjects(1); return false;">1</a>
            </li>
        `;
        if (startPage > 2) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadObjects(${i}); return false;">${i}</a>
            </li>
        `;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            html += '<li class="page-item disabled"><span class="page-link">...</span></li>';
        }
        html += `
            <li class="page-item">
                <a class="page-link" href="#" onclick="loadObjects(${totalPages}); return false;">${totalPages}</a>
            </li>
        `;
    }
    
    // Next button
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadObjects(${currentPage + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    paginationEl.innerHTML = html;
}

// Utility functions
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    return new Intl.NumberFormat('es-ES', { 
        maximumFractionDigits: decimals,
        minimumFractionDigits: 0
    }).format(num);
}

function formatScientific(num) {
    if (num === null || num === undefined || isNaN(num)) return 'N/A';
    if (num === 0) return '0';
    const exponent = Math.floor(Math.log10(Math.abs(num)));
    const mantissa = num / Math.pow(10, exponent);
    return `${mantissa.toFixed(2)} × 10<sup>${exponent}</sup>`;
}

function getCategoryInfo(category) {
    const categoryMap = {
        'Planetas': { icon: 'bi-globe', color: 'text-primary', badgeClass: 'bg-primary' },
        'Lunas': { icon: 'bi-moon', color: 'text-info', badgeClass: 'bg-info' },
        'Asteroides': { icon: 'bi-circle-fill', color: 'text-secondary', badgeClass: 'bg-secondary' },
        'Cometas': { icon: 'bi-stars', color: 'text-warning', badgeClass: 'bg-warning text-dark' },
        'Objetos Cercanos': { icon: 'bi-exclamation-circle', color: 'text-danger', badgeClass: 'bg-danger' },
        'NEO': { icon: 'bi-exclamation-circle', color: 'text-danger', badgeClass: 'bg-danger' },
        'Asteroides Peligrosos': { icon: 'bi-radioactive', color: 'text-danger', badgeClass: 'bg-danger' },
        'Asteroides Troyanos': { icon: 'bi-triangle', color: 'text-success', badgeClass: 'bg-success' },
        'Centauros': { icon: 'bi-diamond', color: 'text-purple', badgeClass: 'bg-purple' }
    };
    
    return categoryMap[category] || { 
        icon: 'bi-question-circle', 
        color: 'text-muted', 
        badgeClass: 'bg-secondary' 
    };
}

function showDetailLoading() {
    const sections = ['objectName', 'objectType', 'objectId', 'objectImage', 
                     'physicalProperties', 'orbitalProperties', 'horizonsData'];
    
    sections.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            if (id === 'objectImage') {
                element.innerHTML = `
                    <div class="text-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                    </div>
                `;
            } else if (id.includes('Properties') || id === 'horizonsData') {
                element.innerHTML = `
                    <tr>
                        <td colspan="2" class="text-center">
                            <div class="spinner-border spinner-border-sm" role="status">
                                <span class="visually-hidden">Cargando...</span>
                            </div>
                        </td>
                    </tr>
                `;
            } else {
                element.innerHTML = '<span class="placeholder col-6"></span>';
            }
        }
    });
}

function showDetailError(message) {
    document.getElementById('objectDetail').innerHTML = `
        <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">Error al cargar objeto</h4>
            <p>${message}</p>
            <hr>
            <button class="btn btn-primary" onclick="clearSelection()">
                <i class="bi bi-arrow-left"></i> Volver a la lista
            </button>
        </div>
    `;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement);
    
    const toast = new bootstrap.Toast(toastElement.querySelector('.toast'));
    toast.show();
    
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}