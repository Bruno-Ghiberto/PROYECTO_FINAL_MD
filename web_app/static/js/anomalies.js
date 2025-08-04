// Anomalies page functionality
let currentPage = 1;
let currentAnomalyType = '';
let anomaliesData = [];
let anomalyExplanations = {};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadAnomalies();
});

// Load anomalies data
async function loadAnomalies(page = 1) {
    currentPage = page;
    
    try {
        const params = new URLSearchParams({
            page: page,
            page_size: 12,
            anomaly_type: currentAnomalyType
        });
        
        const response = await fetch(`/api/anomalies?${params}`);
        const result = await response.json();
        
        if (result.success) {
            anomaliesData = result.data;
            anomalyExplanations = result.explanations || {};
            
            // Update statistics
            updateStatistics(result.statistics);
            
            // Update filter options
            updateFilterOptions(result.anomaly_types);
            
            // Update explanations
            updateExplanations();
            
            // Display anomalies
            displayAnomalies(result.data);
            
            // Update pagination
            updatePagination(result.pagination);
            
            // Update result count
            document.getElementById('resultCount').textContent = result.pagination.total;
        } else {
            showError('Error al cargar anomalías: ' + result.error);
        }
    } catch (error) {
        console.error('Error loading anomalies:', error);
        showError('Error al conectar con el servidor');
    }
}

// Update statistics cards
function updateStatistics(stats) {
    // Calculate total
    const total = Object.values(stats).reduce((sum, count) => sum + count, 0);
    document.getElementById('totalAnomalies').textContent = total;
    
    // Update specific counts
    document.getElementById('dbscanCount').textContent = stats['DBSCAN_Outlier'] || 0;
    document.getElementById('eccentricityCount').textContent = stats['High_Eccentricity'] || 0;
    document.getElementById('inclinationCount').textContent = stats['High_Inclination'] || 0;
}

// Update filter options
function updateFilterOptions(anomalyTypes) {
    const select = document.getElementById('anomalyTypeFilter');
    select.innerHTML = '<option value="">Todos los tipos</option>';
    
    anomalyTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = formatAnomalyType(type);
        if (type === currentAnomalyType) {
            option.selected = true;
        }
        select.appendChild(option);
    });
    
    // Add change event listener
    select.onchange = function() {
        currentAnomalyType = this.value;
        loadAnomalies(1);
    };
}

// Update explanations panel
function updateExplanations() {
    const container = document.getElementById('anomalyExplanations');
    
    if (currentAnomalyType && anomalyExplanations[currentAnomalyType]) {
        container.innerHTML = `
            <div class="alert alert-info mb-0">
                <h6 class="alert-heading">${formatAnomalyType(currentAnomalyType)}</h6>
                <p class="mb-0">${anomalyExplanations[currentAnomalyType]}</p>
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="small">
                <p class="mb-2"><strong>Tipos de anomalías detectadas:</strong></p>
                <ul class="mb-0">
                    ${Object.entries(anomalyExplanations).map(([type, desc]) => 
                        `<li><strong>${formatAnomalyType(type)}:</strong> ${desc}</li>`
                    ).join('')}
                </ul>
            </div>
        `;
    }
}

// Display anomalies grid
function displayAnomalies(anomalies) {
    const container = document.getElementById('anomaliesContainer');
    
    if (anomalies.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <p class="text-muted">No se encontraron anomalías con los filtros seleccionados</p>
            </div>
        `;
        return;
    }
    
    const anomaliesHtml = anomalies.map(anomaly => {
        const reasons = anomaly.specific_reasons || [];
        const reasonsHtml = reasons.length > 0 
            ? reasons.map(r => `<span class="badge bg-warning text-dark me-1">${r}</span>`).join('')
            : '<span class="text-muted">Características inusuales</span>';
        
        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card h-100 border-warning anomaly-card" onclick="showAnomalyDetail('${anomaly.id}')">
                    <div class="card-header bg-warning bg-opacity-10">
                        <h6 class="mb-0">
                            ${anomaly.display_name || anomaly.name}
                            <span class="badge bg-secondary float-end">${anomaly.ui_category || 'Objeto'}</span>
                        </h6>
                    </div>
                    <div class="card-body">
                        <p class="small text-muted mb-2">
                            <i class="bi bi-tag"></i> ${formatAnomalyType(anomaly.anomaly_type)}
                        </p>
                        <div class="mb-3">
                            ${reasonsHtml}
                        </div>
                        <div class="row small">
                            <div class="col-6">
                                <strong>Tamaño:</strong><br>
                                ${formatSize(anomaly)}
                            </div>
                            <div class="col-6">
                                <strong>Órbita:</strong><br>
                                ${formatOrbit(anomaly)}
                            </div>
                        </div>
                        ${anomaly.rarity_score !== null && anomaly.rarity_score !== undefined ? 
                            `<div class="mt-2">
                                <small class="text-muted">Rareza:</small>
                                <div class="progress" style="height: 10px;">
                                    <div class="progress-bar bg-warning" style="width: ${anomaly.rarity_score * 100}%"></div>
                                </div>
                            </div>` : ''
                        }
                    </div>
                    <div class="card-footer bg-transparent">
                        <button class="btn btn-sm btn-warning w-100">
                            <i class="bi bi-search"></i> Ver detalles
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `<div class="row">${anomaliesHtml}</div>`;
}

// Format anomaly type for display
function formatAnomalyType(type) {
    const typeMap = {
        'DBSCAN_Outlier': 'Outlier DBSCAN',
        'High_Eccentricity': 'Alta Excentricidad',
        'High_Inclination': 'Alta Inclinación',
        'Large_Size': 'Tamaño Grande',
        'Fast_Rotation': 'Rotación Rápida',
        'Unusual_Composition': 'Composición Inusual'
    };
    return typeMap[type] || type;
}

// Format size information
function formatSize(anomaly) {
    if (anomaly.mean_radius_km) {
        return `${anomaly.mean_radius_km.toFixed(1)} km radio`;
    } else if (anomaly.diameter_km) {
        return `${anomaly.diameter_km.toFixed(1)} km diám.`;
    }
    return 'Desconocido';
}

// Format orbit information
function formatOrbit(anomaly) {
    const parts = [];
    if (anomaly.eccentricity !== null && anomaly.eccentricity !== undefined) {
        parts.push(`e=${anomaly.eccentricity.toFixed(3)}`);
    }
    if (anomaly.inclination_deg !== null && anomaly.inclination_deg !== undefined) {
        parts.push(`i=${anomaly.inclination_deg.toFixed(1)}°`);
    }
    return parts.join(', ') || 'Sin datos';
}

// Show anomaly detail modal
async function showAnomalyDetail(objectId) {
    const modal = new bootstrap.Modal(document.getElementById('anomalyDetailModal'));
    const modalTitle = document.getElementById('anomalyModalTitle');
    const modalBody = document.getElementById('anomalyModalBody');
    
    // Find anomaly in current data
    const anomaly = anomaliesData.find(a => a.id == objectId);
    if (!anomaly) {
        return;
    }
    
    modalTitle.textContent = anomaly.display_name || anomaly.name;
    modalBody.innerHTML = '<div class="text-center"><div class="spinner-border"></div></div>';
    modal.show();
    
    try {
        // Fetch detailed data
        const response = await fetch(`/api/objects/${objectId}`);
        const result = await response.json();
        
        if (result.success) {
            const data = result.data;
            
            modalBody.innerHTML = `
                <div class="row">
                    <div class="col-md-4 text-center mb-3">
                        ${data.image ? 
                            `<img src="${data.image.url}" alt="${data.name}" class="img-fluid rounded" style="max-height: 200px;">` :
                            '<div class="bg-secondary rounded p-5"><i class="bi bi-image fs-1 text-light"></i></div>'
                        }
                    </div>
                    <div class="col-md-8">
                        <h6>Información de Anomalía</h6>
                        <p class="mb-2">
                            <span class="badge bg-warning text-dark">${formatAnomalyType(anomaly.anomaly_type)}</span>
                        </p>
                        <p class="small">${anomaly.anomaly_explanation || 'Características inusuales detectadas'}</p>
                        
                        ${anomaly.specific_reasons && anomaly.specific_reasons.length > 0 ? `
                            <h6>Razones Específicas:</h6>
                            <ul class="small">
                                ${anomaly.specific_reasons.map(r => `<li>${r}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                </div>
                
                <hr>
                
                <div class="row">
                    <div class="col-md-6">
                        <h6>Propiedades Físicas</h6>
                        <table class="table table-sm">
                            <tr>
                                <td>Tipo:</td>
                                <td>${data.ui_category || data.object_type || 'Desconocido'}</td>
                            </tr>
                            ${data.mean_radius_km ? `
                                <tr>
                                    <td>Radio:</td>
                                    <td>${data.mean_radius_km.toFixed(1)} km</td>
                                </tr>
                            ` : ''}
                            ${data.mass_kg ? `
                                <tr>
                                    <td>Masa:</td>
                                    <td>${data.mass_kg.toExponential(2)} kg</td>
                                </tr>
                            ` : ''}
                            ${data.density_g_cm3 ? `
                                <tr>
                                    <td>Densidad:</td>
                                    <td>${data.density_g_cm3.toFixed(2)} g/cm³</td>
                                </tr>
                            ` : ''}
                        </table>
                    </div>
                    <div class="col-md-6">
                        <h6>Propiedades Orbitales</h6>
                        <table class="table table-sm">
                            ${data.semimajor_axis_au ? `
                                <tr>
                                    <td>Semieje mayor:</td>
                                    <td>${data.semimajor_axis_au.toFixed(3)} AU</td>
                                </tr>
                            ` : ''}
                            ${data.eccentricity !== null && data.eccentricity !== undefined ? `
                                <tr>
                                    <td>Excentricidad:</td>
                                    <td>${data.eccentricity.toFixed(4)}</td>
                                </tr>
                            ` : ''}
                            ${data.inclination_deg !== null && data.inclination_deg !== undefined ? `
                                <tr>
                                    <td>Inclinación:</td>
                                    <td>${data.inclination_deg.toFixed(2)}°</td>
                                </tr>
                            ` : ''}
                            ${data.orbital_period_days ? `
                                <tr>
                                    <td>Periodo orbital:</td>
                                    <td>${(data.orbital_period_days / 365.25).toFixed(2)} años</td>
                                </tr>
                            ` : ''}
                        </table>
                    </div>
                </div>
                
                <div class="text-center mt-3">
                    <a href="#" onclick="viewObjectDetail('${objectId}')" class="btn btn-primary">
                        <i class="bi bi-eye"></i> Ver detalles completos
                    </a>
                </div>
            `;
        }
    } catch (error) {
        modalBody.innerHTML = '<div class="alert alert-danger">Error al cargar los detalles</div>';
    }
}

// View full object details
function viewObjectDetail(objectId) {
    // This would navigate to the main object detail view
    window.location.href = `/?object=${objectId}`;
}

// Update pagination
function updatePagination(pagination) {
    const container = document.getElementById('anomaliesPagination');
    const totalPages = pagination.total_pages;
    const currentPage = pagination.page;
    
    let html = '';
    
    // Previous button
    html += `
        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadAnomalies(${currentPage - 1}); return false;">
                <i class="bi bi-chevron-left"></i>
            </a>
        </li>
    `;
    
    // Page numbers
    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
        if (i === currentPage) {
            html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else {
            html += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="loadAnomalies(${i}); return false;">${i}</a>
                </li>
            `;
        }
    }
    
    // Next button
    html += `
        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" onclick="loadAnomalies(${currentPage + 1}); return false;">
                <i class="bi bi-chevron-right"></i>
            </a>
        </li>
    `;
    
    container.innerHTML = html;
}

// Show error message
function showError(message) {
    const container = document.getElementById('anomaliesContainer');
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle"></i> ${message}
        </div>
    `;
}

// Sort functionality
document.getElementById('sortBy').addEventListener('change', function() {
    // This would require backend sorting implementation
    // For now, just reload the data
    loadAnomalies(currentPage);
});