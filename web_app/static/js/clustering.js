// Clustering visualization functionality
let clusteringData = null;
let scatterData = [];
let clusterStats = {};

// Color palette for clusters
const clusterColors = {
    '-1': '#ff4444',  // Red for outliers
    '0': '#2196F3',   // Blue
    '1': '#4CAF50',   // Green
    '2': '#FF9800',   // Orange
    '3': '#9C27B0',   // Purple
    '4': '#00BCD4',   // Cyan
    '5': '#FFEB3B'    // Yellow
};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    loadClusteringData();
});

// Load clustering data
async function loadClusteringData() {
    try {
        const response = await fetch('/api/clustering');
        const result = await response.json();
        
        if (result.success) {
            clusteringData = result;
            scatterData = result.scatter_data;
            clusterStats = result.cluster_stats;
            
            // Update statistics
            updateStatistics();
            
            // Create visualization
            createScatterPlot();
            
            // Update cluster details
            updateClusterDetails();
            
            // Create cluster tabs
            createClusterTabs();
            
            // Update PCA info if available
            if (result.pca_info) {
                document.getElementById('pca1Info').textContent = result.pca_info.component_1;
                document.getElementById('pca2Info').textContent = result.pca_info.component_2;
            }
        } else {
            showError('Error al cargar datos de clustering: ' + result.error);
        }
    } catch (error) {
        console.error('Error loading clustering data:', error);
        showError('Error al conectar con el servidor');
    }
}

// Update statistics cards
function updateStatistics() {
    document.getElementById('totalObjects').textContent = clusteringData.total_objects || 0;
    document.getElementById('numClusters').textContent = clusteringData.num_clusters || 0;
    
    // Count outliers
    const outlierCount = clusterStats['-1'] ? clusterStats['-1'].count : 0;
    document.getElementById('outlierCount').textContent = outlierCount;
}

// Create interactive scatter plot using Plotly
function createScatterPlot() {
    const plotDiv = document.getElementById('clusteringPlot');
    
    // Group data by cluster
    const traces = [];
    const clusterGroups = {};
    
    // Group scatter data by cluster
    scatterData.forEach(point => {
        const cluster = point.cluster.toString();
        if (!clusterGroups[cluster]) {
            clusterGroups[cluster] = [];
        }
        clusterGroups[cluster].push(point);
    });
    
    // Create a trace for each cluster
    Object.keys(clusterGroups).sort((a, b) => parseInt(a) - parseInt(b)).forEach(cluster => {
        const points = clusterGroups[cluster];
        const clusterName = cluster === '-1' ? 'Outliers' : `Cluster ${cluster}`;
        
        const trace = {
            x: points.map(p => p.x),
            y: points.map(p => p.y),
            mode: 'markers',
            type: 'scatter',
            name: clusterName,
            text: points.map(p => {
                let text = `<b>${p.name}</b><br>`;
                text += `Categoría: ${p.category}<br>`;
                if (p.radius) text += `Radio: ${p.radius.toFixed(1)} km<br>`;
                if (p.rarity !== null && p.rarity !== undefined) {
                    text += `Rareza: ${(p.rarity * 100).toFixed(1)}%`;
                }
                return text;
            }),
            customdata: points.map(p => p.id),
            hovertemplate: '%{text}<extra></extra>',
            marker: {
                color: clusterColors[cluster] || '#666666',
                size: points.map(p => {
                    // Size based on object radius (log scale)
                    if (p.radius) {
                        return Math.max(5, Math.min(20, Math.log10(p.radius) * 5));
                    }
                    return 8;
                }),
                opacity: 0.7,
                line: {
                    color: 'white',
                    width: 1
                }
            }
        };
        
        traces.push(trace);
    });
    
    // Layout configuration
    const layout = {
        title: {
            text: 'Distribución de Objetos en el Espacio PCA',
            font: { size: 18 }
        },
        xaxis: {
            title: 'Componente Principal 1',
            zeroline: true,
            zerolinecolor: '#cccccc',
            gridcolor: '#eeeeee'
        },
        yaxis: {
            title: 'Componente Principal 2',
            zeroline: true,
            zerolinecolor: '#cccccc',
            gridcolor: '#eeeeee'
        },
        hovermode: 'closest',
        showlegend: true,
        legend: {
            x: 1,
            y: 1,
            xanchor: 'left',
            bgcolor: 'rgba(255, 255, 255, 0.8)'
        },
        plot_bgcolor: '#fafafa',
        paper_bgcolor: 'white'
    };
    
    // Config
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToAdd: ['select2d', 'lasso2d'],
        modeBarButtonsToRemove: ['pan2d', 'autoScale2d']
    };
    
    // Create plot
    Plotly.newPlot(plotDiv, traces, layout, config);
    
    // Add click event
    plotDiv.on('plotly_click', function(data) {
        const point = data.points[0];
        const objectId = point.customdata;
        showObjectDetail(objectId);
    });
}

// Update cluster details panel
function updateClusterDetails() {
    const container = document.getElementById('clusterDetails');
    let html = '<div class="accordion" id="clusterAccordion">';
    
    Object.keys(clusterStats).sort((a, b) => parseInt(a) - parseInt(b)).forEach((clusterId, index) => {
        const stats = clusterStats[clusterId];
        const color = clusterColors[clusterId] || '#666666';
        const isExpanded = index === 0;
        
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header">
                    <button class="accordion-button ${!isExpanded ? 'collapsed' : ''}" 
                            type="button" 
                            data-bs-toggle="collapse" 
                            data-bs-target="#cluster${clusterId}">
                        <span class="badge" style="background-color: ${color}; margin-right: 10px;">
                            ${clusterId === '-1' ? 'Outliers' : `Cluster ${clusterId}`}
                        </span>
                        <span class="text-muted">(${stats.count} objetos)</span>
                    </button>
                </h2>
                <div id="cluster${clusterId}" 
                     class="accordion-collapse collapse ${isExpanded ? 'show' : ''}"
                     data-bs-parent="#clusterAccordion">
                    <div class="accordion-body">
                        <p class="small">${stats.description}</p>
                        
                        ${stats.categories ? `
                            <h6>Categorías:</h6>
                            <ul class="small">
                                ${Object.entries(stats.categories)
                                    .sort((a, b) => b[1] - a[1])
                                    .map(([cat, count]) => `<li>${cat}: ${count}</li>`)
                                    .join('')}
                            </ul>
                        ` : ''}
                        
                        ${stats.avg_radius ? `
                            <p class="small mb-1">
                                <strong>Radio promedio:</strong> ${stats.avg_radius.toFixed(1)} km
                            </p>
                        ` : ''}
                        
                        ${stats.avg_eccentricity !== undefined ? `
                            <p class="small mb-1">
                                <strong>Excentricidad promedio:</strong> ${stats.avg_eccentricity.toFixed(3)}
                            </p>
                        ` : ''}
                        
                        ${stats.avg_inclination !== undefined ? `
                            <p class="small mb-1">
                                <strong>Inclinación promedio:</strong> ${stats.avg_inclination.toFixed(1)}°
                            </p>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Create cluster tabs
function createClusterTabs() {
    const tabsContainer = document.getElementById('clusterTabs');
    const tabContent = document.getElementById('clusterTabContent');
    
    let tabsHtml = '';
    let contentHtml = '';
    
    Object.keys(clusterStats).sort((a, b) => parseInt(a) - parseInt(b)).forEach((clusterId, index) => {
        const isActive = index === 0;
        const tabId = `cluster-tab-${clusterId}`;
        const contentId = `cluster-content-${clusterId}`;
        
        // Create tab
        tabsHtml += `
            <li class="nav-item" role="presentation">
                <button class="nav-link ${isActive ? 'active' : ''}" 
                        id="${tabId}" 
                        data-bs-toggle="tab" 
                        data-bs-target="#${contentId}" 
                        type="button">
                    <span class="badge" style="background-color: ${clusterColors[clusterId]};">
                        ${clusterId === '-1' ? 'Outliers' : `Cluster ${clusterId}`}
                    </span>
                    <span class="ms-1">(${clusterStats[clusterId].count})</span>
                </button>
            </li>
        `;
        
        // Create content
        contentHtml += `
            <div class="tab-pane fade ${isActive ? 'show active' : ''}" 
                 id="${contentId}" 
                 role="tabpanel">
                <div class="table-responsive">
                    <table class="table table-sm table-hover">
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Categoría</th>
                                <th>Radio (km)</th>
                                <th>Excentricidad</th>
                                <th>Inclinación</th>
                                <th>Rareza</th>
                                <th>Acciones</th>
                            </tr>
                        </thead>
                        <tbody id="cluster-objects-${clusterId}">
                            <tr>
                                <td colspan="7" class="text-center">
                                    <div class="spinner-border spinner-border-sm"></div>
                                    Cargando...
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });
    
    tabsContainer.innerHTML = tabsHtml;
    tabContent.innerHTML = contentHtml;
    
    // Load objects for each cluster
    Object.keys(clusterStats).forEach(clusterId => {
        loadClusterObjects(clusterId);
    });
}

// Load objects for a specific cluster
function loadClusterObjects(clusterId) {
    const tbody = document.getElementById(`cluster-objects-${clusterId}`);
    const objects = scatterData.filter(obj => obj.cluster == clusterId);
    
    if (objects.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No hay objetos en este cluster</td></tr>';
        return;
    }
    
    const rows = objects.map(obj => `
        <tr>
            <td><strong>${obj.name}</strong></td>
            <td>${obj.category || '-'}</td>
            <td>${obj.radius ? obj.radius.toFixed(1) : '-'}</td>
            <td>${obj.eccentricity !== undefined ? obj.eccentricity.toFixed(3) : '-'}</td>
            <td>${obj.inclination !== undefined ? obj.inclination.toFixed(1) + '°' : '-'}</td>
            <td>
                ${obj.rarity !== null && obj.rarity !== undefined ? 
                    `<div class="progress" style="width: 60px; height: 10px;">
                        <div class="progress-bar bg-warning" style="width: ${obj.rarity * 100}%"></div>
                    </div>` : '-'
                }
            </td>
            <td>
                <button class="btn btn-sm btn-outline-primary" onclick="showObjectDetail('${obj.id}')">
                    <i class="bi bi-eye"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    tbody.innerHTML = rows;
}

// Show object detail modal
async function showObjectDetail(objectId) {
    const modal = new bootstrap.Modal(document.getElementById('objectDetailModal'));
    const modalTitle = document.getElementById('objectModalTitle');
    const modalBody = document.getElementById('objectModalBody');
    
    // Find object in scatter data
    const object = scatterData.find(obj => obj.id == objectId);
    if (!object) return;
    
    modalTitle.textContent = object.name;
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
                        <div class="mt-2">
                            <span class="badge" style="background-color: ${clusterColors[object.cluster]};">
                                ${object.cluster === -1 ? 'Outlier' : `Cluster ${object.cluster}`}
                            </span>
                        </div>
                    </div>
                    <div class="col-md-8">
                        <h6>Información del Cluster</h6>
                        <p class="small">
                            Coordenadas PCA: (${object.x.toFixed(3)}, ${object.y.toFixed(3)})
                        </p>
                        ${object.rarity !== null && object.rarity !== undefined ? 
                            `<p class="small">Puntuación de rareza: ${(object.rarity * 100).toFixed(1)}%</p>` : ''
                        }
                        
                        <hr>
                        
                        <div class="row">
                            <div class="col-6">
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
                                    ${data.diameter_km ? `
                                        <tr>
                                            <td>Diámetro:</td>
                                            <td>${data.diameter_km.toFixed(1)} km</td>
                                        </tr>
                                    ` : ''}
                                </table>
                            </div>
                            <div class="col-6">
                                <h6>Propiedades Orbitales</h6>
                                <table class="table table-sm">
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
                                    ${data.semimajor_axis_au ? `
                                        <tr>
                                            <td>Semieje mayor:</td>
                                            <td>${data.semimajor_axis_au.toFixed(3)} AU</td>
                                        </tr>
                                    ` : ''}
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="text-center mt-3">
                    <a href="/?object=${objectId}" class="btn btn-primary">
                        <i class="bi bi-eye"></i> Ver detalles completos
                    </a>
                </div>
            `;
        }
    } catch (error) {
        modalBody.innerHTML = '<div class="alert alert-danger">Error al cargar los detalles</div>';
    }
}

// Export clustering data
function exportClustering() {
    if (!clusteringData || !clusteringData.data) {
        alert('No hay datos para exportar');
        return;
    }
    
    // Convert to CSV
    const headers = Object.keys(clusteringData.data[0]);
    const csv = [
        headers.join(','),
        ...clusteringData.data.map(row => 
            headers.map(header => {
                const value = row[header];
                // Escape values containing commas
                if (typeof value === 'string' && value.includes(',')) {
                    return `"${value.replace(/"/g, '""')}"`;
                }
                return value;
            }).join(',')
        )
    ].join('\n');
    
    // Download
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'clustering_results.csv';
    link.click();
}

// Show error message
function showError(message) {
    const plotDiv = document.getElementById('clusteringPlot');
    plotDiv.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle"></i> ${message}
        </div>
    `;
}