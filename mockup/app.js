// GIS2BIM OpenAnalysis - Mockup JavaScript

// State
let map;
let marker;
let boundingBox; // Changed from radiusCircle to square bounding box
let selectedLocation = null;
let baseLayers = {}; // For layer control
let currentPage = 0;
let loadedPages = [];
let activeDrawings = [];
let settings = {
    paperSize: 'A3',
    orientation: 'landscape',
    radius: 500,
    defaultLayers: []
};
let savedReports = [];
let serverStatuses = {}; // Track server health status
let generatedPdfBlob = null; // Store generated PDF for download

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadSettings();
    loadSavedReports();
    initActiveDrawings();
    initMap();
    initDrawingsList();
    initEventListeners();
    initResizableColumns();
    initDragDrop();
    initServersList();
});

// Initialize active drawings from standard report or saved settings
function initActiveDrawings() {
    if (settings.defaultLayers && settings.defaultLayers.length > 0) {
        // Use saved configuration
        activeDrawings = settings.defaultLayers.map(id => {
            const layer = AVAILABLE_LAYERS.find(l => l.id === id);
            return layer ? { ...layer } : null;
        }).filter(Boolean);
    } else if (window.STANDARD_REPORT) {
        // Use standard report configuration with 15 pages
        activeDrawings = STANDARD_REPORT.pages.map(page => {
            const baseLayer = AVAILABLE_LAYERS.find(l => l.id === page.layerId);
            return {
                id: page.id,
                layerId: page.layerId,
                name: page.title,
                description: page.description,
                subtitle: page.subtitle,
                scale: page.scale,
                overlayLayers: page.overlayLayers || [],
                isSummary: page.isSummary || false,
                category: baseLayer?.category || 'thematisch',
                source: baseLayer?.source || 'PDOK',
                color: baseLayer?.color || '#666',
                type: baseLayer?.type || 'WMS',
                url: baseLayer?.url || ''
            };
        });
    } else {
        // Fallback to default layers
        activeDrawings = AVAILABLE_LAYERS.filter(l => l.default).map(l => ({ ...l }));
    }
}

function initMap() {
    // Default location: Grote Kerk Dordrecht
    const defaultLat = 51.8133;
    const defaultLng = 4.6601;

    map = L.map('map').setView([defaultLat, defaultLng], 17);

    // Define base layers
    baseLayers = {
        'Luchtfoto': L.tileLayer('https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0/Actueel_orthoHR/EPSG:3857/{z}/{x}/{y}.jpeg', {
            attribution: '&copy; <a href="https://www.kadaster.nl">Kadaster</a>',
            maxZoom: 19
        }),
        'TOP10NL': L.tileLayer('https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/standaard/EPSG:3857/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.kadaster.nl">Kadaster</a>',
            maxZoom: 19
        }),
        'OpenStreetMap': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19
        })
    };

    // Add Luchtfoto as default layer
    baseLayers['Luchtfoto'].addTo(map);

    // Add layer control to map
    L.control.layers(baseLayers, null, {
        position: 'topright',
        collapsed: false
    }).addTo(map);

    map.on('click', function(e) {
        setLocation(e.latlng.lat, e.latlng.lng);
        reverseGeocode(e.latlng.lat, e.latlng.lng);
    });

    // Set default location on load
    setTimeout(() => {
        setLocation(defaultLat, defaultLng);
        updateLocationInfo('Grote Kerk, Dordrecht', 'Dordrecht', `${defaultLat.toFixed(5)}, ${defaultLng.toFixed(5)}`);
    }, 500);
}

function initDrawingsList() {
    const list = document.getElementById('layers-list');
    if (!list) return;
    list.innerHTML = '';

    activeDrawings.forEach((drawing, index) => {
        const item = document.createElement('div');
        item.className = 'drawing-item';
        item.dataset.index = index;
        item.dataset.id = drawing.id;
        item.draggable = true;
        item.onclick = (e) => {
            if (!e.target.closest('.drawing-checkbox') && !e.target.closest('.drag-handle')) {
                selectDrawingItem(index);
            }
        };

        item.innerHTML = `
            <div class="drag-handle">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                    <circle cx="4" cy="4" r="1.5"/>
                    <circle cx="12" cy="4" r="1.5"/>
                    <circle cx="4" cy="8" r="1.5"/>
                    <circle cx="12" cy="8" r="1.5"/>
                    <circle cx="4" cy="12" r="1.5"/>
                    <circle cx="12" cy="12" r="1.5"/>
                </svg>
            </div>
            <div class="drawing-checkbox">
                <input type="checkbox" checked onclick="event.stopPropagation(); updateSelectedCount();">
            </div>
            <div class="drawing-color" style="background: ${drawing.color || '#666'}"></div>
            <div class="drawing-number">${index + 1}</div>
            <div class="drawing-info">
                <h4>${drawing.name}</h4>
                <p>${drawing.subtitle || drawing.description || ''}</p>
            </div>
            <div class="drawing-scale">${drawing.scale ? '1:' + drawing.scale.toLocaleString('nl-NL') : ''}</div>
            <div class="drawing-source">${drawing.source || ''}</div>
            <button class="drawing-remove" onclick="event.stopPropagation(); removeDrawing(${index});" title="Verwijderen">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="4" y1="4" x2="12" y2="12"/>
                    <line x1="12" y1="4" x2="4" y2="12"/>
                </svg>
            </button>
            <div class="drawing-status"></div>
        `;

        list.appendChild(item);
    });

    updateDrawingCount();
}

function updateDrawingCount() {
    const countEl = document.getElementById('drawing-count');
    if (countEl) {
        countEl.textContent = `${activeDrawings.length} tekeningen`;
    }
}

function initEventListeners() {
    document.getElementById('address-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') searchAddress();
    });

    document.getElementById('radius-input').addEventListener('input', function() {
        settings.radius = parseInt(this.value);
        document.getElementById('radius-value').textContent = this.value;
        // Update bounding box if location is selected
        // Bounding box breedte wordt gedeeld door 2 voor half-width berekening
        if (boundingBox && selectedLocation) {
            const lat = selectedLocation.lat;
            const lng = selectedLocation.lng;
            const metersPerDegreeLat = 111320;
            const metersPerDegreeLng = 111320 * Math.cos(lat * Math.PI / 180);
            const halfWidth = settings.radius / 2;  // Breedte / 2 = half-width
            const halfSizeLat = halfWidth / metersPerDegreeLat;
            const halfSizeLng = halfWidth / metersPerDegreeLng;
            const bounds = [
                [lat - halfSizeLat, lng - halfSizeLng],
                [lat + halfSizeLat, lng + halfSizeLng]
            ];
            boundingBox.setBounds(bounds);
        }
    });

    // Close modals on background click
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });
}

// Resizable Columns
function initResizableColumns() {
    const leftPanel = document.getElementById('left-panel');
    const rightPanel = document.getElementById('preview-panel');
    const leftHandle = document.getElementById('left-resize');
    const rightHandle = document.getElementById('right-resize');
    const mainContainer = document.querySelector('.main');

    if (!leftHandle || !rightHandle || !mainContainer) {
        console.error('Resize elements not found:', { leftHandle, rightHandle, mainContainer });
        return;
    }

    let isResizing = false;
    let currentHandle = null;
    let startX = 0;
    let startWidth = 0;

    function startResize(e, handle) {
        isResizing = true;
        currentHandle = handle;
        startX = e.clientX;

        if (handle === 'left') {
            startWidth = leftPanel.offsetWidth;
        } else {
            startWidth = rightPanel.offsetWidth;
        }

        document.body.classList.add('resizing');
        e.preventDefault();
        e.stopPropagation();
    }

    function doResize(e) {
        if (!isResizing) return;

        const deltaX = e.clientX - startX;

        if (currentHandle === 'left') {
            const newWidth = Math.max(280, Math.min(500, startWidth + deltaX));
            leftPanel.style.width = newWidth + 'px';
            leftPanel.style.flexShrink = '0';
            leftPanel.style.flexGrow = '0';
        } else if (currentHandle === 'right') {
            const newWidth = Math.max(300, Math.min(600, startWidth - deltaX));
            rightPanel.style.width = newWidth + 'px';
            rightPanel.style.flexShrink = '0';
            rightPanel.style.flexGrow = '0';
        }

        // Trigger map resize
        if (map) {
            map.invalidateSize();
        }
    }

    function stopResize() {
        if (isResizing) {
            isResizing = false;
            currentHandle = null;
            document.body.classList.remove('resizing');
        }
    }

    leftHandle.addEventListener('mousedown', (e) => startResize(e, 'left'));
    rightHandle.addEventListener('mousedown', (e) => startResize(e, 'right'));
    document.addEventListener('mousemove', doResize);
    document.addEventListener('mouseup', stopResize);
}

// Drag and Drop for Layers
function initDragDrop() {
    const list = document.getElementById('layers-list');
    if (!list) return;
    let draggedItem = null;
    let draggedIndex = null;

    list.addEventListener('dragstart', (e) => {
        const item = e.target.closest('.drawing-item');
        if (!item) return;

        draggedItem = item;
        draggedIndex = parseInt(item.dataset.index);
        item.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    });

    list.addEventListener('dragend', (e) => {
        const item = e.target.closest('.drawing-item');
        if (item) {
            item.classList.remove('dragging');
        }
        document.querySelectorAll('.drawing-item').forEach(i => i.classList.remove('drag-over'));
        draggedItem = null;
        draggedIndex = null;
    });

    list.addEventListener('dragover', (e) => {
        e.preventDefault();
        const item = e.target.closest('.drawing-item');
        if (item && item !== draggedItem) {
            const rect = item.getBoundingClientRect();
            const midY = rect.top + rect.height / 2;

            document.querySelectorAll('.drawing-item').forEach(i => i.classList.remove('drag-over'));
            item.classList.add('drag-over');
        }
    });

    list.addEventListener('drop', (e) => {
        e.preventDefault();
        const targetItem = e.target.closest('.drawing-item');
        if (!targetItem || targetItem === draggedItem) return;

        const targetIndex = parseInt(targetItem.dataset.index);

        // Reorder activeDrawings
        const [moved] = activeDrawings.splice(draggedIndex, 1);
        activeDrawings.splice(targetIndex, 0, moved);

        // Rebuild list
        initDrawingsList();

        // Re-init drag/drop
        initDragDrop();

        // Regenerate if location selected
        if (selectedLocation) {
            generateReportPreview();
        }
    });
}

// Remove drawing
function removeDrawing(index) {
    activeDrawings.splice(index, 1);
    initDrawingsList();
    initDragDrop();

    if (selectedLocation && activeDrawings.length > 0) {
        generateReportPreview();
    } else if (activeDrawings.length === 0) {
        // Reset viewer
        document.getElementById('viewer-empty').classList.remove('hidden');
        document.getElementById('page-container').classList.remove('visible');
        document.getElementById('page-thumbnails').classList.remove('visible');
    }
}

// Layer Modal
function openLayerModal() {
    const modal = document.getElementById('layer-modal');
    modal.classList.add('active');

    renderAvailableLayers();
    renderCategoryFilters();
}

function closeLayerModal() {
    document.getElementById('layer-modal').classList.remove('active');
}

function renderAvailableLayers(filter = '', category = '') {
    const container = document.getElementById('available-layers');
    container.innerHTML = '';

    const filtered = AVAILABLE_LAYERS.filter(layer => {
        const matchesFilter = !filter ||
            layer.name.toLowerCase().includes(filter.toLowerCase()) ||
            layer.description?.toLowerCase().includes(filter.toLowerCase());
        const matchesCategory = !category || layer.category === category;
        const notActive = !activeDrawings.find(d => d.id === layer.id);
        return matchesFilter && matchesCategory && notActive;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<div class="no-results">Geen lagen gevonden</div>';
        return;
    }

    filtered.forEach(layer => {
        const item = document.createElement('div');
        item.className = 'layer-option';
        item.dataset.id = layer.id;

        item.innerHTML = `
            <div class="layer-option-checkbox">
                <input type="checkbox" id="layer-${layer.id}">
            </div>
            <div class="layer-option-color" style="background: ${layer.color || '#666'}"></div>
            <div class="layer-option-info">
                <div class="layer-option-name">${layer.name}</div>
                <div class="layer-option-desc">${layer.description || ''}</div>
            </div>
            <div class="layer-option-source">${layer.source}</div>
        `;

        item.addEventListener('click', (e) => {
            if (e.target.type !== 'checkbox') {
                const cb = item.querySelector('input[type="checkbox"]');
                cb.checked = !cb.checked;
            }
            item.classList.toggle('selected', item.querySelector('input').checked);
        });

        container.appendChild(item);
    });
}

function renderCategoryFilters() {
    const container = document.getElementById('category-filters');
    container.innerHTML = '';

    const categories = [...new Set(AVAILABLE_LAYERS.map(l => l.category))];

    const allBtn = document.createElement('button');
    allBtn.className = 'category-btn active';
    allBtn.textContent = 'Alle';
    allBtn.onclick = () => filterByCategory('');
    container.appendChild(allBtn);

    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = 'category-btn';
        btn.textContent = cat.charAt(0).toUpperCase() + cat.slice(1);
        btn.onclick = () => filterByCategory(cat);
        container.appendChild(btn);
    });
}

function filterLayers() {
    const searchInput = document.getElementById('layer-search');
    const activeCategory = document.querySelector('.category-btn.active')?.dataset?.category || '';
    renderAvailableLayers(searchInput.value, activeCategory);
}

function filterByCategory(category) {
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase() === (category || 'alle'));
        btn.dataset.category = category;
    });

    const searchInput = document.getElementById('layer-search');
    renderAvailableLayers(searchInput?.value || '', category);
}

function addSelectedLayers() {
    const selected = document.querySelectorAll('#available-layers .layer-option input:checked');

    selected.forEach(checkbox => {
        const layerId = checkbox.closest('.layer-option').dataset.id;
        const layer = AVAILABLE_LAYERS.find(l => l.id === layerId);
        if (layer && !activeDrawings.find(d => d.id === layer.id)) {
            activeDrawings.push({ ...layer });
        }
    });

    closeLayerModal();
    initDrawingsList();
    initDragDrop();

    if (selectedLocation) {
        generateReportPreview();
    }
}

// Settings Modal
function openSettingsModal() {
    const modal = document.getElementById('settings-modal');
    modal.classList.add('active');

    // Populate default layers checklist
    renderDefaultLayersSettings();
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.remove('active');
}

function renderDefaultLayersSettings() {
    const container = document.getElementById('default-layers-list');
    if (!container) return;

    container.innerHTML = '';

    AVAILABLE_LAYERS.forEach(layer => {
        const isDefault = settings.defaultLayers.includes(layer.id) ||
            (settings.defaultLayers.length === 0 && layer.default);

        const item = document.createElement('div');
        item.className = 'settings-layer-item';
        item.innerHTML = `
            <input type="checkbox" id="default-${layer.id}" value="${layer.id}" ${isDefault ? 'checked' : ''}>
            <label for="default-${layer.id}">${layer.name}</label>
        `;
        container.appendChild(item);
    });
}

function saveSettings() {
    // Collect default layers
    const defaultLayers = [];
    document.querySelectorAll('#default-layers-list input:checked').forEach(cb => {
        defaultLayers.push(cb.value);
    });

    settings.defaultLayers = defaultLayers;

    // Save to localStorage
    localStorage.setItem('gis2bim-settings', JSON.stringify(settings));

    closeSettingsModal();
    showNotification('Instellingen opgeslagen');
}

function resetSettings() {
    settings = {
        paperSize: 'A3',
        orientation: 'landscape',
        radius: 500,
        defaultLayers: []
    };

    localStorage.removeItem('gis2bim-settings');

    // Re-init with defaults
    initActiveDrawings();
    initDrawingsList();
    initDragDrop();

    closeSettingsModal();
    showNotification('Instellingen gereset naar standaard');
}

function loadSettings() {
    const saved = localStorage.getItem('gis2bim-settings');
    if (saved) {
        try {
            const parsed = JSON.parse(saved);
            settings = { ...settings, ...parsed };
        } catch (e) {
            console.error('Error loading settings:', e);
        }
    }
}

// Save Report Modal
function saveCurrentReport() {
    if (activeDrawings.length === 0) {
        showNotification('Geen lagen om op te slaan');
        return;
    }

    const modal = document.getElementById('save-modal');
    modal.classList.add('active');

    // Populate current layers in modal
    const layersList = document.getElementById('save-layers-list');
    if (layersList) {
        layersList.innerHTML = activeDrawings.map(d => `<li>${d.name}</li>`).join('');
    }
}

function closeSaveModal() {
    document.getElementById('save-modal').classList.remove('active');
}

function confirmSaveReport() {
    const nameInput = document.getElementById('report-name');
    const name = nameInput?.value.trim() || `Rapport ${new Date().toLocaleDateString('nl-NL')}`;

    const report = {
        id: Date.now().toString(),
        name: name,
        layers: activeDrawings.map(d => d.id),
        settings: { ...settings },
        createdAt: new Date().toISOString()
    };

    savedReports.push(report);
    localStorage.setItem('gis2bim-saved-reports', JSON.stringify(savedReports));

    closeSaveModal();
    renderSavedReports();
    showNotification(`Rapport "${name}" opgeslagen`);

    if (nameInput) nameInput.value = '';
}

function loadSavedReports() {
    const saved = localStorage.getItem('gis2bim-saved-reports');
    if (saved) {
        try {
            savedReports = JSON.parse(saved);
        } catch (e) {
            console.error('Error loading saved reports:', e);
            savedReports = [];
        }
    }
    renderSavedReports();
}

function renderSavedReports() {
    const container = document.getElementById('saved-reports-list');
    if (!container) return;

    if (savedReports.length === 0) {
        container.innerHTML = '<div class="no-saved-reports">Geen opgeslagen rapporten</div>';
        return;
    }

    container.innerHTML = savedReports.map(report => `
        <div class="saved-report-item" data-id="${report.id}">
            <div class="saved-report-info">
                <div class="saved-report-name">${report.name}</div>
                <div class="saved-report-meta">${report.layers.length} lagen &bull; ${new Date(report.createdAt).toLocaleDateString('nl-NL')}</div>
            </div>
            <div class="saved-report-actions">
                <button class="btn-icon" onclick="loadReport('${report.id}')" title="Laden">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 10v4H2v-4M8 2v8M5 7l3 3 3-3"/>
                    </svg>
                </button>
                <button class="btn-icon" onclick="deleteReport('${report.id}')" title="Verwijderen">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="4" y1="4" x2="12" y2="12"/>
                        <line x1="12" y1="4" x2="4" y2="12"/>
                    </svg>
                </button>
            </div>
        </div>
    `).join('');
}

function loadReport(reportId) {
    const report = savedReports.find(r => r.id === reportId);
    if (!report) return;

    // Load layers
    activeDrawings = report.layers.map(id => {
        const layer = AVAILABLE_LAYERS.find(l => l.id === id);
        return layer ? { ...layer } : null;
    }).filter(Boolean);

    // Load settings
    if (report.settings) {
        settings = { ...settings, ...report.settings };
        document.getElementById('radius-input').value = settings.radius;
        document.getElementById('radius-value').textContent = settings.radius;
    }

    initDrawingsList();
    initDragDrop();

    if (selectedLocation) {
        generateReportPreview();
    }

    showNotification(`Rapport "${report.name}" geladen`);
}

function deleteReport(reportId) {
    if (!confirm('Weet je zeker dat je dit rapport wilt verwijderen?')) return;

    savedReports = savedReports.filter(r => r.id !== reportId);
    localStorage.setItem('gis2bim-saved-reports', JSON.stringify(savedReports));
    renderSavedReports();
    showNotification('Rapport verwijderd');
}

// Notifications
function showNotification(message) {
    // Simple notification - could be enhanced with a proper notification system
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        z-index: 10000;
        animation: fadeIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 2500);
}

// Location
function setLocation(lat, lng) {
    selectedLocation = { lat, lng };

    if (marker) map.removeLayer(marker);
    if (boundingBox) map.removeLayer(boundingBox);

    // Center marker with crosshair design
    const markerIcon = L.divIcon({
        className: 'custom-marker',
        html: `
            <div style="position:relative;width:30px;height:30px;">
                <div style="position:absolute;left:14px;top:0;width:2px;height:30px;background:#2563eb;"></div>
                <div style="position:absolute;top:14px;left:0;width:30px;height:2px;background:#2563eb;"></div>
                <div style="position:absolute;left:10px;top:10px;width:10px;height:10px;background:#2563eb;border:2px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.3);"></div>
            </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    });

    marker = L.marker([lat, lng], { icon: markerIcon }).addTo(map);

    // Calculate square bounding box based on bounding box width
    // Breedte wordt gedeeld door 2 voor de half-width berekening
    const metersPerDegreeLat = 111320;
    const metersPerDegreeLng = 111320 * Math.cos(lat * Math.PI / 180);

    const halfWidth = settings.radius / 2;  // Breedte / 2 = half-width
    const halfSizeLat = halfWidth / metersPerDegreeLat;
    const halfSizeLng = halfWidth / metersPerDegreeLng;

    const bounds = [
        [lat - halfSizeLat, lng - halfSizeLng],  // Southwest corner
        [lat + halfSizeLat, lng + halfSizeLng]   // Northeast corner
    ];

    boundingBox = L.rectangle(bounds, {
        color: '#1d4ed8',
        fillColor: '#3b82f6',
        fillOpacity: 0.20,
        weight: 3,
        dashArray: '8, 4'
    }).addTo(map);

    map.setView([lat, lng], 16);

    // Enable generate button
    const generateBtn = document.getElementById('generate-btn');
    if (generateBtn) {
        generateBtn.disabled = false;
    }

    // Start generating pages
    generateReportPreview();
}

function updateLocationInfo(address, municipality, coords) {
    document.getElementById('selected-address').textContent = address || '-';
    document.getElementById('selected-municipality').textContent = municipality || '-';
    document.getElementById('selected-coords').textContent = coords || '-';
}

async function searchAddress() {
    const input = document.getElementById('address-input').value.trim();
    if (!input) return;

    try {
        const response = await fetch(
            `https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?q=${encodeURIComponent(input)}&rows=1`
        );
        const data = await response.json();

        if (data.response?.docs?.length > 0) {
            const result = data.response.docs[0];
            const coords = result.centroide_ll.match(/POINT\(([\d.]+) ([\d.]+)\)/);

            if (coords) {
                const lng = parseFloat(coords[1]);
                const lat = parseFloat(coords[2]);
                setLocation(lat, lng);
                updateLocationInfo(result.weergavenaam, result.gemeentenaam, `${lat.toFixed(5)}, ${lng.toFixed(5)}`);
            }
        } else {
            alert('Adres niet gevonden.');
        }
    } catch (error) {
        alert('Fout bij zoeken.');
    }
}

async function reverseGeocode(lat, lng) {
    try {
        const response = await fetch(
            `https://api.pdok.nl/bzk/locatieserver/search/v3_1/reverse?lat=${lat}&lon=${lng}&rows=1`
        );
        const data = await response.json();

        if (data.response?.docs?.length > 0) {
            const result = data.response.docs[0];
            updateLocationInfo(result.weergavenaam, result.gemeentenaam, `${lat.toFixed(5)}, ${lng.toFixed(5)}`);
        } else {
            updateLocationInfo('Onbekend', '-', `${lat.toFixed(5)}, ${lng.toFixed(5)}`);
        }
    } catch (error) {
        updateLocationInfo('Locatie', '-', `${lat.toFixed(5)}, ${lng.toFixed(5)}`);
    }
}

// Settings
function setPaperSize(size) {
    settings.paperSize = size;
    document.querySelectorAll('.settings-grid .button-toggle')[0]?.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === size);
    });

    const page = document.getElementById('a3-page');
    if (size === 'A4') {
        page.style.maxWidth = '80%';
    } else {
        page.style.maxWidth = '100%';
    }
}

function setOrientation(orientation) {
    settings.orientation = orientation;
    document.querySelectorAll('.settings-grid .button-toggle')[1]?.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === orientation);
    });

    const page = document.getElementById('a3-page');
    page.classList.toggle('portrait', orientation === 'portrait');
}

// Report Preview Generation
function generateReportPreview() {
    if (activeDrawings.length === 0) return;

    loadedPages = [];
    currentPage = 0;

    // Show viewer, hide empty state
    document.getElementById('viewer-empty').classList.add('hidden');
    document.getElementById('page-container').classList.add('visible');
    document.getElementById('page-thumbnails').classList.add('visible');

    // Reset drawing items
    document.querySelectorAll('.drawing-item').forEach(item => {
        item.classList.remove('ready', 'active', 'loading');
        item.querySelector('.drawing-status').innerHTML = '';
    });

    // Create thumbnails
    createThumbnails();

    // Update page counter
    updatePageCounter();

    // Start loading pages progressively
    loadPagesProgressively();
}

function createThumbnails() {
    const container = document.getElementById('page-thumbnails');
    container.innerHTML = '';

    activeDrawings.forEach((drawing, index) => {
        const thumb = document.createElement('div');
        thumb.className = 'thumb';
        thumb.dataset.index = index;
        thumb.textContent = index + 1;
        thumb.onclick = () => goToPage(index);
        container.appendChild(thumb);
    });
}

function loadPagesProgressively() {
    let currentIndex = 0;

    const loadNext = () => {
        if (currentIndex >= activeDrawings.length) return;

        const drawingItem = document.querySelector(`.drawing-item[data-index="${currentIndex}"]`);
        const thumb = document.querySelector(`.thumb[data-index="${currentIndex}"]`);

        if (!drawingItem || !thumb) {
            currentIndex++;
            loadNext();
            return;
        }

        // Set loading state
        drawingItem.classList.add('loading');
        drawingItem.querySelector('.drawing-status').innerHTML = '<div class="status-spinner"></div>';

        // Simulate loading delay
        setTimeout(() => {
            // Mark as ready
            drawingItem.classList.remove('loading');
            drawingItem.classList.add('ready');
            drawingItem.querySelector('.drawing-status').innerHTML = `
                <svg class="status-check" width="14" height="14" viewBox="0 0 16 16" fill="none">
                    <path d="M13 5l-6 6-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            `;

            thumb.classList.add('ready');
            loadedPages.push(currentIndex);

            // Auto-show first page
            if (currentIndex === 0) {
                goToPage(0);
            }

            // Enable navigation
            updateNavigation();

            currentIndex++;
            loadNext();
        }, 150 + Math.random() * 100);
    };

    loadNext();
}

function selectDrawingItem(index) {
    if (!loadedPages.includes(index)) return;
    goToPage(index);
}

function goToPage(index) {
    if (index < 0 || index >= activeDrawings.length) return;

    currentPage = index;

    // Update active states
    document.querySelectorAll('.drawing-item').forEach((item, i) => {
        item.classList.toggle('active', i === index);
    });

    document.querySelectorAll('.thumb').forEach((thumb, i) => {
        thumb.classList.toggle('active', i === index);
    });

    // Render page
    renderPage(index);
    updatePageCounter();
    updateNavigation();
}

function renderPage(index) {
    const drawing = activeDrawings[index];
    if (!drawing) return;

    const address = document.getElementById('selected-address').textContent;
    const municipality = document.getElementById('selected-municipality').textContent;
    const coords = document.getElementById('selected-coords').textContent;

    // Determine background class based on category
    const bgClass = getBgClass(drawing);

    const page = document.getElementById('a3-page');
    page.innerHTML = `
        <div class="page-content">
            <div class="page-map-area ${bgClass}">
                <div class="page-map-placeholder">${drawing.name}</div>
            </div>
            <div class="page-info-panel">
                <div class="page-title-block">
                    <h3>GIS2BIM OpenAnalysis</h3>
                    <p>Locatie Rapport</p>
                </div>
                <div class="page-details">
                    <div class="page-detail-row">
                        <span class="page-detail-label">Tekening</span>
                        <span class="page-detail-value">${index + 1} / ${activeDrawings.length}</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Type</span>
                        <span class="page-detail-value">${drawing.name}</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Adres</span>
                        <span class="page-detail-value">${address}</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Gemeente</span>
                        <span class="page-detail-value">${municipality}</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Coördinaten</span>
                        <span class="page-detail-value">${coords}</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Bounding box</span>
                        <span class="page-detail-value">${settings.radius}m x ${settings.radius}m</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Schaal</span>
                        <span class="page-detail-value">1:${(drawing.scale || 2500).toLocaleString('nl-NL')}</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Formaat</span>
                        <span class="page-detail-value">${settings.paperSize} ${settings.orientation === 'landscape' ? 'liggend' : 'staand'}</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Bron</span>
                        <span class="page-detail-value">${drawing.source}</span>
                    </div>
                    <div class="page-detail-row">
                        <span class="page-detail-label">Datum</span>
                        <span class="page-detail-value">${new Date().toLocaleDateString('nl-NL')}</span>
                    </div>
                </div>
                <div class="page-footer">
                    GIS2BIM OpenAnalysis &bull; OpenAEC Foundation
                </div>
            </div>
        </div>
    `;
}

function getBgClass(drawing) {
    // Map layer IDs to background classes
    const bgMap = {
        'top10nl': 'bg-top10',
        'kadaster': 'bg-kadaster',
        'bag': 'bg-kadaster',
        'bgt': 'bg-bgt',
        'bestemmingsplan': 'bg-bestemmingsplan',
        'geluid': 'bg-geluid',
        'ahn': 'bg-ahn',
        'luchtfoto': 'bg-luchtfoto',
        'bodem': 'bg-bodem',
        'cultuurhistorie': 'bg-cultuur',
        'waterbeheer': 'bg-water',
        'natura2000': 'bg-natura',
        'energie': 'bg-energie',
        'cbs': 'bg-cbs',
        'kabels': 'bg-kabels'
    };

    // Check if ID matches or contains a key
    for (const [key, bgClass] of Object.entries(bgMap)) {
        if (drawing.id.includes(key)) {
            return bgClass;
        }
    }

    // Default based on category
    const categoryBg = {
        'topografie': 'bg-top10',
        'kadaster': 'bg-kadaster',
        'milieu': 'bg-geluid',
        'infrastructuur': 'bg-kabels',
        'luchtfoto': 'bg-luchtfoto',
        'thematisch': 'bg-cbs'
    };

    return categoryBg[drawing.category] || 'bg-top10';
}

function updatePageCounter() {
    document.getElementById('current-page').textContent = currentPage + 1;
    document.getElementById('total-pages').textContent = activeDrawings.length;
}

function updateNavigation() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    prevBtn.disabled = currentPage === 0;
    nextBtn.disabled = currentPage >= loadedPages.length - 1;
}

function prevPage() {
    if (currentPage > 0) {
        goToPage(currentPage - 1);
    }
}

function nextPage() {
    if (currentPage < loadedPages.length - 1) {
        goToPage(currentPage + 1);
    }
}

// Selection
function toggleSelectAll() {
    const selectAll = document.getElementById('select-all-checkbox');
    document.querySelectorAll('.drawing-item input[type="checkbox"]').forEach(cb => {
        cb.checked = selectAll.checked;
    });
    updateSelectedCount();
}

function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.drawing-item input[type="checkbox"]');
    const checked = Array.from(checkboxes).filter(cb => cb.checked).length;

    const selectAll = document.getElementById('select-all-checkbox');
    if (selectAll) {
        selectAll.checked = checked === checkboxes.length;
        selectAll.indeterminate = checked > 0 && checked < checkboxes.length;
    }
}

// PDF Generation
function generatePDF() {
    if (!selectedLocation) return;

    const overlay = document.getElementById('loading-overlay');
    const progressFill = document.getElementById('progress-fill');
    const statusText = document.getElementById('loading-status');

    overlay.classList.add('active');

    const steps = [
        { progress: 15, text: 'Voorbereiden van kaartlagen...' },
        { progress: 35, text: 'Genereren van kaartbeelden...' },
        { progress: 55, text: 'Samenstellen van layouts...' },
        { progress: 75, text: 'Genereren van PDF...' },
        { progress: 100, text: 'Rapport gereed!' }
    ];

    let step = 0;
    const interval = setInterval(() => {
        if (step < steps.length) {
            progressFill.style.width = steps[step].progress + '%';
            statusText.textContent = steps[step].text;
            step++;
        } else {
            clearInterval(interval);
            setTimeout(() => {
                overlay.classList.remove('active');
                progressFill.style.width = '0%';

                const selectedCount = document.querySelectorAll('.drawing-item input[type="checkbox"]:checked').length;
                alert(`Demo: PDF rapport gegenereerd!\n\nLocatie: ${document.getElementById('selected-address').textContent}\nTekeningen: ${selectedCount}\nFormaat: ${settings.paperSize} ${settings.orientation === 'landscape' ? 'liggend' : 'staand'}`);
            }, 300);
        }
    }, 400);
}

// Geolocation
function gotoCurrentLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                setLocation(pos.coords.latitude, pos.coords.longitude);
                reverseGeocode(pos.coords.latitude, pos.coords.longitude);
            },
            () => alert('Kon locatie niet bepalen.')
        );
    }
}

// Keyboard
document.addEventListener('keydown', function(e) {
    // Don't trigger if in input field
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

    if (e.key === 'ArrowLeft') prevPage();
    if (e.key === 'ArrowRight') nextPage();
    if (e.key === 'Escape') {
        document.getElementById('loading-overlay').classList.remove('active');
        document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
    }
});

// Add CSS for notifications animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-50%) translateY(20px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    @keyframes fadeOut {
        from { opacity: 1; transform: translateX(-50%) translateY(0); }
        to { opacity: 0; transform: translateX(-50%) translateY(20px); }
    }
`;
document.head.appendChild(style);

console.log('GIS2BIM OpenAnalysis Mockup v4 - Adaptive Layers');

// =====================
// Server List Functions
// =====================

// Toggle servers section visibility
function toggleServersSection() {
    const section = document.getElementById('servers-section');
    if (section) {
        section.classList.toggle('collapsed');
    }
}

// Extract unique servers from AVAILABLE_LAYERS
function getUniqueServers() {
    const serverMap = new Map();

    AVAILABLE_LAYERS.forEach(layer => {
        if (layer.url && layer.source) {
            // Extract base URL
            let baseUrl = layer.url;
            try {
                const url = new URL(layer.url);
                baseUrl = url.origin;
            } catch (e) {
                // Keep original if not valid URL
            }

            const key = `${layer.source}-${baseUrl}`;
            if (!serverMap.has(key)) {
                serverMap.set(key, {
                    name: layer.source,
                    url: baseUrl,
                    fullUrl: layer.url,
                    type: layer.type,
                    layerCount: 1
                });
            } else {
                serverMap.get(key).layerCount++;
            }
        }
    });

    return Array.from(serverMap.values()).sort((a, b) => a.name.localeCompare(b.name));
}

function initServersList() {
    const servers = getUniqueServers();
    const container = document.getElementById('servers-list');
    if (!container) return;

    container.innerHTML = '';

    servers.forEach((server, index) => {
        const item = document.createElement('div');
        item.className = 'server-item';
        item.dataset.index = index;
        item.dataset.url = server.fullUrl;

        // Initialize status as unknown
        const statusKey = server.url;
        if (!serverStatuses[statusKey]) {
            serverStatuses[statusKey] = 'unknown';
        }

        item.innerHTML = `
            <div class="server-status ${serverStatuses[statusKey]}" data-url="${server.url}"></div>
            <div class="server-info">
                <div class="server-name">${server.name}</div>
                <div class="server-url" title="${server.url}">${server.url.replace(/^https?:\/\//, '')} (${server.layerCount} lagen)</div>
            </div>
            <button class="server-check-btn" onclick="checkServer('${server.fullUrl}', '${server.url}')" title="Controleer server">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                    <path d="M13.5 8A5.5 5.5 0 118 2.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
            </button>
        `;

        container.appendChild(item);
    });
}

async function checkServer(fullUrl, baseUrl) {
    // Update status to checking
    const statusEl = document.querySelector(`.server-status[data-url="${baseUrl}"]`);
    if (statusEl) {
        statusEl.className = 'server-status checking';
    }

    try {
        // Try to fetch with a timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);

        // For WMS/WMTS, try GetCapabilities
        let testUrl = fullUrl;
        if (fullUrl.includes('wms') || fullUrl.includes('wmts')) {
            const separator = fullUrl.includes('?') ? '&' : '?';
            if (fullUrl.toLowerCase().includes('wmts')) {
                testUrl = `${fullUrl}${separator}service=WMTS&request=GetCapabilities`;
            } else {
                testUrl = `${fullUrl}${separator}service=WMS&request=GetCapabilities`;
            }
        }

        const response = await fetch(testUrl, {
            method: 'HEAD',
            mode: 'no-cors', // Allow cross-origin requests
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        // If we get here without error, server is likely online
        serverStatuses[baseUrl] = 'online';
        if (statusEl) {
            statusEl.className = 'server-status online';
        }
    } catch (error) {
        // Fetch failed - but with no-cors mode, opaque responses look like errors
        // So we'll assume online if it didn't timeout
        if (error.name === 'AbortError') {
            serverStatuses[baseUrl] = 'offline';
            if (statusEl) {
                statusEl.className = 'server-status offline';
            }
        } else {
            // With no-cors, successful opaque response throws an error
            // but the server is actually reachable
            serverStatuses[baseUrl] = 'online';
            if (statusEl) {
                statusEl.className = 'server-status online';
            }
        }
    }
}

async function checkAllServers() {
    const servers = getUniqueServers();
    showNotification('Servers worden gecontroleerd...');

    // Check all servers in parallel
    const checks = servers.map(server => checkServer(server.fullUrl, server.url));
    await Promise.all(checks);

    // Count online servers
    const onlineCount = Object.values(serverStatuses).filter(s => s === 'online').length;
    showNotification(`${onlineCount} van ${servers.length} servers online`);
}

// =====================
// Generate Report & Download PDF Functions
// =====================

// Helper function to update page progress status
function updatePageProgress(index, status) {
    const item = document.getElementById(`page-progress-${index}`);
    if (!item) return;

    // Remove all status classes
    item.classList.remove('pending', 'loading', 'completed', 'error');
    item.classList.add(status);

    // Update status icon
    const statusEl = item.querySelector('.page-progress-status');
    if (status === 'pending') {
        statusEl.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" fill="none"/>
            </svg>
        `;
    } else if (status === 'loading') {
        statusEl.innerHTML = '<div class="page-progress-spinner"></div>';
    } else if (status === 'completed') {
        statusEl.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M13 5l-6 6-3-3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
    } else if (status === 'error') {
        statusEl.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                <path d="M4 4l8 8M12 4l-8 8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
        `;
    }
}

async function generateReport() {
    if (!selectedLocation) {
        showNotification('Selecteer eerst een locatie');
        return;
    }

    if (activeDrawings.length === 0) {
        showNotification('Voeg eerst kaartlagen toe');
        return;
    }

    const overlay = document.getElementById('loading-overlay');
    const progressFill = document.getElementById('progress-fill');
    const statusText = document.getElementById('loading-status');
    const progressList = document.getElementById('page-progress-list');

    overlay.classList.add('active');
    progressFill.style.width = '5%';
    statusText.textContent = 'Voorbereiden van rapportage...';

    // Build page progress list
    progressList.innerHTML = activeDrawings.map((drawing, index) => `
        <div class="page-progress-item pending" id="page-progress-${index}">
            <div class="page-progress-status">
                <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
                    <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" fill="none"/>
                </svg>
            </div>
            <span class="page-progress-name">${index + 1}. ${drawing.name}</span>
            <span class="page-progress-scale">1:${(drawing.scale || 2500).toLocaleString('nl-NL')}</span>
        </div>
    `).join('');

    try {
        // Prepare report data - use layerId for backend, not page id
        const reportData = {
            location: {
                lat: selectedLocation.lat,
                lng: selectedLocation.lng,
                address: document.getElementById('selected-address').textContent,
                municipality: document.getElementById('selected-municipality').textContent
            },
            paper_size: settings.paperSize,
            orientation: settings.orientation,
            pages: activeDrawings.map((drawing, index) => {
                // Use layerId if available (from STANDARD_REPORT), otherwise use id
                const layer_id = drawing.layerId || drawing.id;
                console.log(`[Report] Page ${index + 1}: layer_id='${layer_id}', drawing.layerId='${drawing.layerId}', drawing.id='${drawing.id}'`);
                return {
                    layer_id: layer_id,
                    title: drawing.name,
                    subtitle: drawing.subtitle || drawing.description || '',
                    scale: drawing.scale || 2500,
                    overlay_layers: drawing.overlayLayers || []
                };
            })
        };

        console.log('[Report] Sending request:', JSON.stringify(reportData, null, 2));

        // Start progress simulation for page-by-page feedback
        const totalPages = activeDrawings.length;
        let currentPageIndex = 0;

        const progressInterval = setInterval(() => {
            if (currentPageIndex < totalPages) {
                // Update previous page to completed
                if (currentPageIndex > 0) {
                    updatePageProgress(currentPageIndex - 1, 'completed');
                }
                // Set current page to loading
                updatePageProgress(currentPageIndex, 'loading');
                statusText.textContent = `Pagina ${currentPageIndex + 1}/${totalPages}: ${activeDrawings[currentPageIndex].name}`;
                progressFill.style.width = `${10 + (currentPageIndex / totalPages) * 80}%`;
                currentPageIndex++;
            }
        }, 800); // Estimate ~800ms per page

        // Call the direct (synchronous) backend API
        const response = await fetch('/api/reports/generate-direct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reportData)
        });

        // Stop progress simulation
        clearInterval(progressInterval);

        if (!response.ok) {
            // Mark all remaining as error
            for (let i = 0; i < totalPages; i++) {
                updatePageProgress(i, 'error');
            }
            const errorText = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        // Mark all pages as completed
        for (let i = 0; i < totalPages; i++) {
            updatePageProgress(i, 'completed');
        }

        progressFill.style.width = '95%';
        statusText.textContent = 'PDF wordt gegenereerd...';

        // Get the PDF blob directly
        generatedPdfBlob = await response.blob();

        progressFill.style.width = '100%';
        statusText.textContent = 'Rapport gereed!';

        // Enable download button
        const downloadBtn = document.getElementById('download-pdf-btn');
        if (downloadBtn) {
            downloadBtn.disabled = false;
        }

        // Show PDF preview in the preview panel
        showPdfPreview(generatedPdfBlob);

        setTimeout(() => {
            overlay.classList.remove('active');
            progressFill.style.width = '0%';
            showNotification('Rapport gegenereerd! Preview rechts zichtbaar.');
        }, 500);

    } catch (error) {
        console.error('Error generating report:', error);
        overlay.classList.remove('active');
        progressFill.style.width = '0%';

        // Fallback to demo mode
        showNotification('Backend fout: ' + error.message);
        // generatePDF(); // Use the demo function
    }
}

function downloadPDF() {
    if (generatedPdfBlob) {
        // Download the generated PDF
        const url = URL.createObjectURL(generatedPdfBlob);
        const a = document.createElement('a');
        a.href = url;
        const address = document.getElementById('selected-address').textContent;
        const sanitizedAddress = address.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
        a.download = `GIS2BIM_Rapport_${sanitizedAddress}_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showNotification('PDF gedownload');
    } else {
        showNotification('Genereer eerst een rapportage');
    }
}

// Download Kadaster data as DXF
async function downloadDXF() {
    if (!selectedLocation) {
        showNotification('Selecteer eerst een locatie');
        return;
    }

    const dxfBtn = document.getElementById('download-dxf-btn');
    const originalText = dxfBtn.querySelector('span').textContent;

    // Show loading state
    dxfBtn.disabled = true;
    dxfBtn.querySelector('span').textContent = 'Laden...';

    try {
        const response = await fetch('/api/reports/download-dxf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lat: selectedLocation.lat,
                lng: selectedLocation.lng,
                radius: settings.radius / 2,  // Half of bounding box width
                layers: ['Perceel', 'OpenbareRuimteNaam']
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }

        // Get the DXF blob
        const dxfBlob = await response.blob();

        // Download the file
        const url = URL.createObjectURL(dxfBlob);
        const a = document.createElement('a');
        a.href = url;
        const address = document.getElementById('selected-address').textContent;
        const sanitizedAddress = address.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 30);
        a.download = `Kadaster_${sanitizedAddress}_${new Date().toISOString().split('T')[0]}.dxf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification('DXF gedownload - Open in AutoCAD of BricsCAD');

    } catch (error) {
        console.error('Error downloading DXF:', error);
        showNotification('Fout bij downloaden DXF: ' + error.message);
    } finally {
        // Restore button state
        dxfBtn.disabled = false;
        dxfBtn.querySelector('span').textContent = originalText;
    }
}

// Show PDF preview in the preview panel
function showPdfPreview(pdfBlob) {
    const previewContainer = document.getElementById('a3-page');
    const viewerEmpty = document.getElementById('viewer-empty');
    const pageContainer = document.getElementById('page-container');

    if (!previewContainer) return;

    // Hide empty state, show preview container
    if (viewerEmpty) viewerEmpty.classList.add('hidden');
    if (pageContainer) pageContainer.classList.add('visible');

    // Create blob URL for the PDF
    const pdfUrl = URL.createObjectURL(pdfBlob);

    // Replace preview content with PDF embed
    previewContainer.innerHTML = `
        <div class="pdf-preview-container">
            <embed
                src="${pdfUrl}#toolbar=0&navpanes=0&scrollbar=1"
                type="application/pdf"
                width="100%"
                height="100%"
                class="pdf-embed"
            />
        </div>
    `;

    // Store URL for cleanup later
    previewContainer.dataset.pdfUrl = pdfUrl;
}

// Cleanup PDF preview URL when switching views
function cleanupPdfPreview() {
    const previewContainer = document.getElementById('a3-page');
    if (previewContainer && previewContainer.dataset.pdfUrl) {
        URL.revokeObjectURL(previewContainer.dataset.pdfUrl);
        delete previewContainer.dataset.pdfUrl;
    }
}

// =====================
// Server Modal Functions
// =====================

let serversData = null; // Store loaded servers data

// Open server management modal
async function openServerModal() {
    const modal = document.getElementById('server-modal');
    modal.classList.add('active');

    // Show list view, hide detail view
    showServerList();

    // Load servers from API
    await loadServersFromAPI();
}

// Close server modal
function closeServerModal() {
    document.getElementById('server-modal').classList.remove('active');
}

// Show server list view
function showServerList() {
    document.getElementById('server-list-view').style.display = 'block';
    document.getElementById('server-detail-view').style.display = 'none';
    document.getElementById('server-modal-title').textContent = 'WMS Server Beheer';
}

// Load servers from backend API
async function loadServersFromAPI() {
    const listContainer = document.getElementById('server-management-list');

    listContainer.innerHTML = `
        <div class="servers-loading">
            <div class="loading-spinner small"></div>
            <span>Servers laden...</span>
        </div>
    `;

    try {
        const response = await fetch('/api/servers/');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        serversData = await response.json();
        renderServerManagementList();

    } catch (error) {
        console.error('Error loading servers:', error);
        listContainer.innerHTML = `
            <div class="servers-error">
                <p>Kon servers niet laden: ${error.message}</p>
                <button class="btn-secondary" onclick="loadServersFromAPI()">Opnieuw proberen</button>
            </div>
        `;
    }
}

// Render server management list
function renderServerManagementList() {
    const listContainer = document.getElementById('server-management-list');

    if (!serversData || !serversData.servers || serversData.servers.length === 0) {
        listContainer.innerHTML = '<div class="no-servers">Geen servers geconfigureerd</div>';
        return;
    }

    listContainer.innerHTML = serversData.servers.map(server => `
        <div class="server-management-item" data-id="${server.id}" onclick="showServerDetail('${server.id}')">
            <div class="server-management-status ${server.status || 'unknown'}"></div>
            <div class="server-management-info">
                <div class="server-management-name">${server.name}</div>
                <div class="server-management-url">${server.url}</div>
                <div class="server-management-meta">
                    <span class="server-type-badge">${server.type}</span>
                    ${server.layers && server.layers.length > 0 ? `<span>${server.layers.length} lagen</span>` : ''}
                </div>
            </div>
            <div class="server-management-actions">
                <button class="btn-icon" onclick="event.stopPropagation(); editServer('${server.id}')" title="Bewerken">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11.5 2.5l2 2-8 8H3.5v-2l8-8z"/>
                    </svg>
                </button>
                <button class="btn-icon" onclick="event.stopPropagation(); deleteServerConfig('${server.id}')" title="Verwijderen">
                    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="4" y1="4" x2="12" y2="12"/>
                        <line x1="12" y1="4" x2="4" y2="12"/>
                    </svg>
                </button>
            </div>
        </div>
    `).join('');
}

// Show server detail with GetCapabilities
async function showServerDetail(serverId) {
    const server = serversData?.servers?.find(s => s.id === serverId);
    if (!server) return;

    // Switch to detail view
    document.getElementById('server-list-view').style.display = 'none';
    document.getElementById('server-detail-view').style.display = 'block';
    document.getElementById('server-modal-title').textContent = server.name;

    // Populate detail info
    document.getElementById('server-detail-name').textContent = server.name;
    document.getElementById('server-detail-url').textContent = server.url;
    document.getElementById('server-detail-status').textContent = server.status || 'unknown';
    document.getElementById('server-detail-status').className = `server-status-badge ${server.status || 'unknown'}`;

    // Show loading state for capabilities
    const capabilitiesContent = document.getElementById('capabilities-content');
    const capabilitiesLoading = document.querySelector('.capabilities-loading');

    capabilitiesContent.style.display = 'none';
    capabilitiesLoading.style.display = 'flex';

    // Fetch GetCapabilities
    try {
        const response = await fetch(`/api/servers/${serverId}/capabilities`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const capabilities = await response.json();
        renderCapabilities(capabilities);

    } catch (error) {
        console.error('Error fetching capabilities:', error);
        capabilitiesLoading.style.display = 'none';
        capabilitiesContent.style.display = 'block';
        capabilitiesContent.innerHTML = `
            <div class="capabilities-error">
                <p>Kon capabilities niet laden: ${error.message}</p>
            </div>
        `;
    }
}

// Render capabilities info
function renderCapabilities(capabilities) {
    const capabilitiesContent = document.getElementById('capabilities-content');
    const capabilitiesLoading = document.querySelector('.capabilities-loading');

    capabilitiesLoading.style.display = 'none';
    capabilitiesContent.style.display = 'block';

    if (capabilities.error) {
        capabilitiesContent.innerHTML = `
            <div class="capabilities-error">
                <p>Fout: ${capabilities.error}</p>
            </div>
        `;
        return;
    }

    const layersHtml = capabilities.layers && capabilities.layers.length > 0
        ? capabilities.layers.slice(0, 50).map(layer => `
            <div class="capability-layer">
                <div class="capability-layer-name">${layer.name}</div>
                <div class="capability-layer-title">${layer.title || '-'}</div>
            </div>
        `).join('')
        : '<p>Geen lagen gevonden</p>';

    const crsHtml = capabilities.crs && capabilities.crs.length > 0
        ? capabilities.crs.slice(0, 20).map(crs => `<span class="crs-badge">${crs}</span>`).join('')
        : '<p>Geen CRS informatie</p>';

    const formatsHtml = capabilities.formats && capabilities.formats.length > 0
        ? capabilities.formats.map(fmt => `<span class="format-badge">${fmt}</span>`).join('')
        : '<p>Geen formaat informatie</p>';

    capabilitiesContent.innerHTML = `
        <div class="capabilities-section">
            <h5>Service Info</h5>
            ${capabilities.title ? `<p><strong>Titel:</strong> ${capabilities.title}</p>` : ''}
            ${capabilities.abstract ? `<p><strong>Abstract:</strong> ${capabilities.abstract.substring(0, 300)}${capabilities.abstract.length > 300 ? '...' : ''}</p>` : ''}
        </div>

        <div class="capabilities-section">
            <h5>Lagen (${capabilities.layers?.length || 0})</h5>
            <div class="capability-layers-list">
                ${layersHtml}
            </div>
            ${capabilities.layers && capabilities.layers.length > 50 ? `<p class="more-info">+ ${capabilities.layers.length - 50} meer lagen</p>` : ''}
        </div>

        <div class="capabilities-section">
            <h5>Ondersteunde CRS</h5>
            <div class="crs-list">
                ${crsHtml}
            </div>
        </div>

        <div class="capabilities-section">
            <h5>Formaten</h5>
            <div class="formats-list">
                ${formatsHtml}
            </div>
        </div>
    `;
}

// Add new server
function addNewServer() {
    const name = prompt('Server naam:');
    if (!name) return;

    const url = prompt('Server URL (WMS endpoint):');
    if (!url) return;

    const type = prompt('Type (WMS, WMTS, TILE):', 'WMS') || 'WMS';

    const newServer = {
        id: name.toLowerCase().replace(/[^a-z0-9]/g, '-'),
        name: name,
        url: url,
        type: type.toUpperCase(),
        version: type === 'WMS' ? '1.3.0' : '1.0.0',
        layers: [],
        crs: ['EPSG:28992', 'EPSG:4326'],
        status: 'active'
    };

    // Save to backend
    fetch('/api/servers/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newServer)
    })
    .then(response => {
        if (!response.ok) throw new Error('Server toevoegen mislukt');
        return response.json();
    })
    .then(() => {
        showNotification(`Server "${name}" toegevoegd`);
        loadServersFromAPI();
    })
    .catch(error => {
        showNotification('Fout: ' + error.message);
    });
}

// Edit server
function editServer(serverId) {
    const server = serversData?.servers?.find(s => s.id === serverId);
    if (!server) return;

    const newName = prompt('Server naam:', server.name);
    if (!newName) return;

    const newUrl = prompt('Server URL:', server.url);
    if (!newUrl) return;

    const updatedServer = {
        ...server,
        name: newName,
        url: newUrl
    };

    fetch(`/api/servers/${serverId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedServer)
    })
    .then(response => {
        if (!response.ok) throw new Error('Server bijwerken mislukt');
        return response.json();
    })
    .then(() => {
        showNotification(`Server "${newName}" bijgewerkt`);
        loadServersFromAPI();
    })
    .catch(error => {
        showNotification('Fout: ' + error.message);
    });
}

// Delete server configuration
function deleteServerConfig(serverId) {
    const server = serversData?.servers?.find(s => s.id === serverId);
    if (!server) return;

    if (!confirm(`Weet je zeker dat je "${server.name}" wilt verwijderen?`)) return;

    fetch(`/api/servers/${serverId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) throw new Error('Server verwijderen mislukt');
        return response.json();
    })
    .then(() => {
        showNotification(`Server "${server.name}" verwijderd`);
        loadServersFromAPI();
    })
    .catch(error => {
        showNotification('Fout: ' + error.message);
    });
}
