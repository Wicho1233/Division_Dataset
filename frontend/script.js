// Configuración
const API_BASE_URL = '/api';

// Estado global
let currentDatasets = [];
let currentSplits = [];

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    console.log('NSL-KDD Dataset Manager iniciado');
    loadDatasets();
    loadSplits();
    setupEventListeners();
});

// Configuración de event listeners
function setupEventListeners() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    document.getElementById('split-dataset-select').addEventListener('change', function() {
        const datasetId = this.value;
        if (datasetId) {
            loadStratificationColumns(datasetId);
        } else {
            document.getElementById('stratify-column').disabled = true;
            document.getElementById('split-btn').disabled = true;
        }
    });
}

// Manejo de archivos
function handleFileSelect(file) {
    if (!file.name.toLowerCase().endsWith('.arff')) {
        showNotification('Solo se permiten archivos .arff', 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showNotification('El archivo es demasiado grande. Máximo 10MB.', 'error');
        return;
    }
    
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const uploadBtn = document.getElementById('upload-btn');
    
    fileName.textContent = `${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
    uploadPlaceholder.style.display = 'none';
    fileInfo.style.display = 'flex';
    uploadBtn.disabled = false;
}

function clearFile() {
    const fileInput = document.getElementById('file-input');
    const uploadPlaceholder = document.getElementById('upload-placeholder');
    const fileInfo = document.getElementById('file-info');
    const uploadBtn = document.getElementById('upload-btn');
    const datasetNameInput = document.getElementById('dataset-name');
    
    fileInput.value = '';
    uploadPlaceholder.style.display = 'block';
    fileInfo.style.display = 'none';
    uploadBtn.disabled = true;
    datasetNameInput.value = '';
}

// Funciones de API
async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
        showLoading(true);
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const contentType = response.headers.get('content-type');
        let data;
        
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = {
                status: response.ok ? 'success' : 'error',
                message: `HTTP ${response.status}: ${response.statusText}`
            };
        }
        
        if (!response.ok) {
            throw new Error(data.message || data.detail || `Error ${response.status}: ${response.statusText}`);
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        let userMessage = error.message;
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            userMessage = 'No se pudo conectar con el servidor. Verifica tu conexión.';
        }
        showNotification(userMessage, 'error');
        throw error;
    } finally {
        showLoading(false);
    }
}

// Funciones de datasets
async function uploadDataset() {
    const fileInput = document.getElementById('file-input');
    const datasetNameInput = document.getElementById('dataset-name');
    
    if (!fileInput.files.length) {
        showNotification('Selecciona un archivo primero', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', datasetNameInput.value || file.name.replace('.arff', ''));
    
    try {
        showLoading(true);
        const response = await fetch(`${API_BASE_URL}/datasets/upload/`, {
            method: 'POST',
            body: formData
        });
        
        let data;
        try {
            data = await response.json();
        } catch (e) {
            data = { message: `Error ${response.status}: ${response.statusText}` };
        }
        
        if (!response.ok) {
            throw new Error(data.message || data.detail || 'Error al subir el archivo');
        }
        
        showNotification('Dataset subido exitosamente', 'success');
        clearFile();
        loadDatasets();
        
    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        showLoading(false);
    }
}

async function loadDatasets() {
    try {
        const data = await apiCall('/datasets/');
        currentDatasets = data.datasets || [];
        renderDatasetsTable();
        updateSplitDatasetSelect();
        
        document.getElementById('datasets-section').style.display = 
            currentDatasets.length > 0 ? 'block' : 'none';
            
    } catch (error) {
        currentDatasets = [];
        renderDatasetsTable();
    }
}

function renderDatasetsTable() {
    const tbody = document.getElementById('datasets-tbody');
    
    if (currentDatasets.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay datasets disponibles</td></tr>';
        return;
    }
    
    tbody.innerHTML = currentDatasets.map(dataset => `
        <tr>
            <td>${dataset.name}</td>
            <td>${dataset.rows || 'N/A'}</td>
            <td>${dataset.columns || 'N/A'}</td>
            <td>${new Date(dataset.uploaded_at).toLocaleDateString()}</td>
            <td>
                <button class="btn btn-secondary btn-small" onclick="showDatasetInfo(${dataset.id})">
                    Info
                </button>
            </td>
        </tr>
    `).join('');
}

async function showDatasetInfo(datasetId) {
    try {
        const data = await apiCall(`/datasets/${datasetId}/info/`);
        const modal = document.getElementById('dataset-info-modal');
        const content = document.getElementById('dataset-info-content');
        
        let basicInfo = '<p>Información no disponible</p>';
        let stratificationContent = '<p>No se pudieron cargar las columnas</p>';
        
        if (data.info && data.info.basic_info) {
            basicInfo = `
                <div class="info-item">
                    <span class="info-label">Filas:</span>
                    <span class="info-value">${data.info.basic_info.shape?.[0] || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Columnas:</span>
                    <span class="info-value">${data.info.basic_info.shape?.[1] || 'N/A'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Uso de memoria:</span>
                    <span class="info-value">${data.info.basic_info.memory_usage ? (data.info.basic_info.memory_usage / 1024 / 1024).toFixed(2) + ' MB' : 'N/A'}</span>
                </div>
            `;
        }
        
        if (data.stratification_columns) {
            stratificationContent = Object.entries(data.stratification_columns)
                .slice(0, 10)
                .map(([col, info]) => `
                    <div class="info-item">
                        <span class="info-label">${col}:</span>
                        <span class="info-value">${info.unique_values || 'N/A'} valores únicos ${info.recommended ? '✓' : ''}</span>
                    </div>
                `).join('');
            
            if (Object.keys(data.stratification_columns).length > 10) {
                stratificationContent += `<div class="info-item"><em>... y ${Object.keys(data.stratification_columns).length - 10} columnas más</em></div>`;
            }
        }
        
        content.innerHTML = `
            <div class="dataset-info">
                <div class="info-section">
                    <h4>Información Básica</h4>
                    ${basicInfo}
                </div>
                <div class="info-section">
                    <h4>Columnas para Estratificación</h4>
                    ${stratificationContent}
                </div>
            </div>
        `;
        
        modal.style.display = 'block';
        
    } catch (error) {
        showNotification('Error al cargar la información del dataset', 'error');
    }
}

// Funciones de splits
async function splitDataset() {
    const datasetSelect = document.getElementById('split-dataset-select');
    const stratifyColumn = document.getElementById('stratify-column');
    const randomState = document.getElementById('random-state');
    const shuffle = document.getElementById('shuffle');
    const generatePlots = document.getElementById('generate-plots');
    
    if (!datasetSelect.value) {
        showNotification('Selecciona un dataset primero', 'error');
        return;
    }
    
    if (!stratifyColumn.value) {
        if (!confirm('¿Continuar sin estratificación? Esto puede afectar la distribución de los datos.')) {
            return;
        }
    }
    
    const payload = {
        dataset_file_id: parseInt(datasetSelect.value),
        stratify_column: stratifyColumn.value || null,
        random_state: parseInt(randomState.value) || 42,
        shuffle: shuffle.checked,
        generate_plots: generatePlots.checked
    };
    
    try {
        const data = await apiCall('/splits/create/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        showNotification('Dataset dividido exitosamente', 'success');
        loadSplits();
        stratifyColumn.value = '';
        document.getElementById('split-btn').disabled = true;
        
    } catch (error) {
        console.error('Error splitting dataset:', error);
    }
}

async function loadSplits() {
    try {
        const data = await apiCall('/splits/');
        currentSplits = data.splits || [];
        renderSplitsTable();
        
        document.getElementById('splits-section').style.display = 
            currentSplits.length > 0 ? 'block' : 'none';
            
    } catch (error) {
        currentSplits = [];
        renderSplitsTable();
    }
}

function renderSplitsTable() {
    const tbody = document.getElementById('splits-tbody');
    
    if (currentSplits.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">No hay divisiones guardadas</td></tr>';
        return;
    }
    
    tbody.innerHTML = currentSplits.map(split => `
        <tr>
            <td>${split.name}</td>
            <td>${split.dataset_file_name || 'N/A'}</td>
            <td>${split.stratify_column || 'Ninguna'}</td>
            <td>${split.train_size || 'N/A'}</td>
            <td>${split.validation_size || 'N/A'}</td>
            <td>${split.test_size || 'N/A'}</td>
            <td>${split.created_at ? new Date(split.created_at).toLocaleDateString() : 'N/A'}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn btn-secondary btn-small" onclick="downloadSplitFile(${split.id}, 'train')">
                        Train
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="downloadSplitFile(${split.id}, 'validation')">
                        Validation
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="downloadSplitFile(${split.id}, 'test')">
                        Test
                    </button>
                    ${(split.distribution_plot_url || split.comparison_plot_url) ? `
                    <button class="btn btn-secondary btn-small" onclick="loadPlots(${split.id})">
                        Gráficas
                    </button>
                    ` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

async function downloadSplitFile(splitId, fileType) {
    try {
        const downloadUrl = `${API_BASE_URL}/splits/${splitId}/download/${fileType}/`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = `${fileType}_split.arff`;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        showNotification(`Iniciando descarga: ${fileType}`, 'success');
        
    } catch (error) {
        showNotification('Error al descargar el archivo', 'error');
    }
}

// Funciones de utilidad
function updateSplitDatasetSelect() {
    const select = document.getElementById('split-dataset-select');
    select.innerHTML = '<option value="">Selecciona un dataset</option>' +
        currentDatasets.map(dataset => 
            `<option value="${dataset.id}">${dataset.name} (${dataset.rows} filas, ${dataset.columns} columnas)</option>`
        ).join('');
    
    document.getElementById('split-section').style.display = 
        currentDatasets.length > 0 ? 'block' : 'none';
}

async function loadStratificationColumns(datasetId) {
    try {
        const data = await apiCall(`/datasets/${datasetId}/info/`);
        const select = document.getElementById('stratify-column');
        
        let options = '<option value="">Selecciona una columna (opcional)</option>';
        
        if (data.stratification_columns) {
            const recommendedColumns = Object.entries(data.stratification_columns)
                .filter(([col, info]) => info.recommended)
                .map(([col, info]) => col);
            
            if (recommendedColumns.length > 0) {
                options += '<optgroup label="Recomendadas">';
                options += recommendedColumns.map(col => 
                    `<option value="${col}">${col}</option>`
                ).join('');
                options += '</optgroup>';
            }
            
            const otherColumns = Object.keys(data.stratification_columns)
                .filter(col => !recommendedColumns.includes(col));
            
            if (otherColumns.length > 0) {
                options += '<optgroup label="Otras columnas">';
                options += otherColumns.map(col => 
                    `<option value="${col}">${col}</option>`
                ).join('');
                options += '</optgroup>';
            }
        } else {
            options += '<option value="">No hay columnas categóricas disponibles</option>';
        }
        
        select.innerHTML = options;
        select.disabled = false;
        document.getElementById('split-btn').disabled = false;
        
    } catch (error) {
        const select = document.getElementById('stratify-column');
        select.innerHTML = '<option value="">Error al cargar columnas</option>';
        select.disabled = false;
        document.getElementById('split-btn').disabled = false;
    }
}

async function loadPlots(splitId) {
    try {
        const split = currentSplits.find(s => s.id === splitId);
        if (!split) {
            showNotification('División no encontrada', 'error');
            return;
        }
        
        const container = document.getElementById('plots-container');
        let plotsHTML = '';
        
        if (split.distribution_plot_url) {
            plotsHTML += `
                <div class="plot-item">
                    <h4>Distribución - ${split.stratify_column || 'Dataset'}</h4>
                    <img src="${split.distribution_plot_url}" alt="Distribución">
                </div>
            `;
        }
        
        if (split.comparison_plot_url) {
            plotsHTML += `
                <div class="plot-item">
                    <h4>Comparación entre Splits</h4>
                    <img src="${split.comparison_plot_url}" alt="Comparación">
                </div>
            `;
        }
        
        if (!plotsHTML) {
            plotsHTML = '<p>No hay gráficas disponibles para esta división</p>';
        }
        
        container.innerHTML = plotsHTML;
        document.getElementById('plots-section').style.display = 'block';
        document.getElementById('plots-section').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        showNotification('Error al cargar las gráficas', 'error');
    }
}

// Utilidades de UI
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}

function showLoading(show) {
    document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

window.addEventListener('click', function(event) {
    const modals = document.getElementsByClassName('modal');
    for (let modal of modals) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    }
});