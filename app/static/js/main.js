// Global Notification Toast System
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container-custom';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'glass-toast';
    
    // Choose icon based on type
    let iconClass = 'fa-check-circle text-success';
    if (type === 'danger' || type === 'error') iconClass = 'fa-times-circle text-danger';
    else if (type === 'warning') iconClass = 'fa-exclamation-triangle text-warning';
    else if (type === 'info') iconClass = 'fa-info-circle text-info';

    toast.innerHTML = `
        <div class="d-flex align-items-center gap-2">
            <i class="fas ${iconClass} fa-lg"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close btn-close-white ms-3" onclick="this.parentElement.remove()" style="font-size: 0.8rem; opacity: 0.7;"></button>
    `;

    container.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease-in reverse';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 4000);
}

// Favorite Stop Management (AJAX version)
async function toggleFavorite(routeId, stopName, direction, buttonElement) {
    const isFavorited = buttonElement.classList.contains('favorited') || buttonElement.dataset.action === 'delete';
    const url = isFavorited ? '/favorites/delete' : '/favorites/add';
    
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                route_id: routeId,
                stop_name: stopName,
                direction: direction
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            
            if (isFavorited) {
                // Change UI state to not favorited
                buttonElement.classList.remove('favorited');
                if (buttonElement.dataset.action === 'delete') {
                    // If in homepage grid list, animate card out
                    const card = buttonElement.closest('.favorite-card');
                    if (card) {
                        card.classList.add('removing');
                        setTimeout(() => {
                            card.remove();
                            // Check if there are no cards left, show empty message
                            const grid = document.getElementById('favorites-grid');
                            if (grid && grid.querySelectorAll('.favorite-card').length === 0) {
                                grid.innerHTML = `
                                    <div class="col-12 text-center py-5 text-muted">
                                        <i class="fas fa-bookmark fa-3x mb-3 text-secondary-color" style="opacity: 0.3;"></i>
                                        <p>目前尚無收藏站牌</p>
                                    </div>
                                `;
                            }
                        }, 400);
                    }
                } else {
                    // Just change icon/text on bus status page
                    buttonElement.innerHTML = '<i class="far fa-bookmark"></i> 收藏此站牌';
                    buttonElement.classList.replace('btn-gradient', 'btn-glass');
                }
            } else {
                // Change UI state to favorited
                buttonElement.classList.add('favorited');
                buttonElement.innerHTML = '<i class="fas fa-bookmark text-warning"></i> 已收藏';
                buttonElement.classList.replace('btn-glass', 'btn-gradient');
            }
        } else {
            showToast(data.message || '操作失敗，請稍後再試。', 'warning');
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
        showToast('與伺服器連線失敗。', 'danger');
    }
}

// Remove favorite stop directly (For homepage buttons)
async function removeFavorite(routeId, stopName, direction, buttonElement) {
    await toggleFavorite(routeId, stopName, direction, buttonElement);
}

// Real-Time Bus Status Update logic
let busStatusTimer = null;
function initBusStatusPolling(routeId, favoritesList = []) {
    // Perform initial fetch
    fetchBusStatus(routeId, favoritesList);
    
    // Set interval for every 10 seconds
    busStatusTimer = setInterval(() => {
        fetchBusStatus(routeId, favoritesList);
    }, 10000);
}

// Convert seconds into human-readable text
function formatEstimateTime(seconds, status) {
    if (status === 1) return '<span class="status-badge inactive">尚未起飛</span>';
    if (status === 2) return '<span class="status-badge inactive">交管中</span>';
    if (status === 3) return '<span class="status-badge inactive">末班車已過</span>';
    if (status === 4) return '<span class="status-badge inactive">今日停駛</span>';
    
    if (seconds === null || seconds === undefined) {
        return '<span class="status-badge inactive">未發車</span>';
    }
    
    if (seconds <= 30) {
        return '<span class="status-badge arriving"><i class="fas fa-bullhorn text-success me-1 pulse"></i>進站中</span>';
    }
    if (seconds <= 90) {
        return '<span class="status-badge incoming"><i class="fas fa-spinner fa-spin text-pink me-1"></i>即將到站</span>';
    }
    
    const minutes = Math.ceil(seconds / 60);
    return `<span class="status-badge normal">${minutes} 分鐘</span>`;
}

async function fetchBusStatus(routeId, favoritesList = []) {
    try {
        const response = await fetch(`/api/bus/${routeId}`);
        if (!response.ok) throw new Error('API response error');
        
        const data = await response.json();
        const timeline = document.getElementById('bus-timeline');
        const reportBadgeContainer = document.getElementById('report-badges');
        
        if (!timeline) return;
        
        // 1. Render Reports (Driver Status)
        if (reportBadgeContainer) {
            reportBadgeContainer.innerHTML = '';
            if (data.reports && data.reports.length > 0) {
                // Show only reports within the last 15 minutes
                data.reports.forEach(report => {
                    const timeStr = report.created_at ? report.created_at.substring(11, 16) : '';
                    const badge = document.createElement('div');
                    
                    let statusColor = 'text-warning';
                    let icon = 'fa-exclamation-circle';
                    let borderClass = 'border-danger';
                    let leftBorderColor = 'var(--accent-pink)';
                    let bgOpacityClass = 'bg-danger';
                    
                    if (report.status.includes('延誤')) {
                        statusColor = 'text-warning';
                        icon = 'fa-clock';
                    } else if (report.status.includes('滿載')) {
                        statusColor = 'text-pink';
                        icon = 'fa-users';
                    } else if (report.status.includes('事故') || report.status.includes('故障')) {
                        statusColor = 'text-danger';
                        icon = 'fa-times-circle';
                    } else if (report.status.includes('正常')) {
                        statusColor = 'text-success';
                        icon = 'fa-check-circle';
                        borderClass = 'border-success';
                        leftBorderColor = '#198754';
                        bgOpacityClass = 'bg-success';
                    }
                    
                    badge.className = `glass-card p-3 mb-2 ${borderClass} d-flex justify-content-between align-items-center`;
                    badge.style.borderLeft = `4px solid ${leftBorderColor}`;
                    
                    badge.innerHTML = `
                        <div class="d-flex align-items-center gap-3">
                            <div class="${bgOpacityClass} bg-opacity-20 p-2 rounded-circle">
                                <i class="fas ${icon} ${statusColor} fa-lg"></i>
                            </div>
                            <div>
                                <h6 class="mb-0 text-white font-weight-bold">司機回報：${report.status}</h6>
                                <small class="text-muted">司機 ${report.driver_name} 於 ${timeStr} 提交</small>
                            </div>
                        </div>
                        ${report.latitude ? `<a href="https://maps.google.com/?q=${report.latitude},${report.longitude}" target="_blank" class="btn btn-sm btn-glass"><i class="fas fa-map-marker-alt text-pink"></i> 地圖</a>` : ''}
                    `;
                    reportBadgeContainer.appendChild(badge);
                });
            } else {
                reportBadgeContainer.innerHTML = `
                    <div class="text-muted small py-2">
                        <i class="fas fa-info-circle me-1"></i> 目前此路線無司機回報特殊路況。
                    </div>
                `;
            }
        }
        
        // 2. Render Timeline
        if (data.stops && data.stops.length > 0) {
            const activeTab = document.querySelector('.direction-tab.active');
            const currentDirection = activeTab ? parseInt(activeTab.dataset.direction) : 0;
            
            const stopsForDirection = data.stops.filter(stop => parseInt(stop.Direction) === currentDirection);
            
            let activeStopIndex = -1;
            let timelineHtml = `
                <div class="timeline-line"></div>
                <div class="timeline-line-active" id="active-line"></div>
            `;
            
            if (stopsForDirection.length > 0) {
                stopsForDirection.forEach((stop, index) => {
                    const stopName = stop.StopName.Zh_tw;
                    const seconds = stop.EstimateTime;
                    const status = stop.StopStatus;
                    
                    // Determine node state
                    let nodeClass = '';
                    if (seconds !== null && seconds <= 90) {
                        nodeClass = 'active';
                        if (activeStopIndex === -1) {
                            activeStopIndex = index;
                        }
                    } else if (seconds !== null && seconds > 90) {
                        nodeClass = 'passed'; // Already passed or further down
                    }
                    
                    // Check if stop is in favorites list
                    const isSaved = favoritesList.some(f => f.route_id === routeId && f.stop_name === stopName && parseInt(f.direction) === parseInt(stop.Direction));
                    
                    timelineHtml += `
                        <div class="timeline-item d-flex justify-content-between align-items-center">
                            <div class="timeline-node ${nodeClass}"></div>
                            <div class="d-flex align-items-center gap-3">
                                <span class="fs-5 fw-bold text-white">${stopName}</span>
                            </div>
                            <div class="d-flex align-items-center gap-2">
                                ${formatEstimateTime(seconds, status)}
                                
                                <button class="btn btn-sm ${isSaved ? 'btn-gradient favorited' : 'btn-glass'}" 
                                        onclick="toggleFavorite('${routeId}', '${stopName}', '${stop.Direction}', this)">
                                    <i class="${isSaved ? 'fas fa-bookmark text-warning' : 'far fa-bookmark'}"></i> 
                                    ${isSaved ? '已收藏' : '收藏此站'}
                                </button>
                            </div>
                        </div>
                    `;
                });
            } else {
                timelineHtml += `
                    <div class="text-center py-5 text-muted">
                        <i class="fas fa-exclamation-triangle fa-2x mb-3 text-secondary-color"></i>
                        <p>此方向暫無站牌資訊</p>
                    </div>
                `;
            }
            
            timeline.innerHTML = timelineHtml;
            
            // Adjust active timeline line height dynamically
            setTimeout(() => {
                const activeLine = document.getElementById('active-line');
                const items = timeline.querySelectorAll('.timeline-item');
                if (activeLine && items.length > 0) {
                    if (activeStopIndex !== -1) {
                        // Height matches down to the active stop
                        const activeItem = items[activeStopIndex];
                        const offsetTop = activeItem.offsetTop;
                        activeLine.style.height = `${offsetTop + 10}px`;
                    } else {
                        activeLine.style.height = '0px';
                    }
                }
            }, 100);
            
        } else {
            timeline.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="fas fa-exclamation-triangle fa-3x mb-3 text-secondary-color"></i>
                    <p>目前查無到站預估時間</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching bus status:', error);
        showToast('無法取得即時動態，請檢查網路連線。', 'danger');
    }
}

// Setup search suggestions for route search bar
function setupSearchSuggestions() {
    const input = document.getElementById('route-search');
    const suggestions = document.getElementById('search-suggestions');
    if (!input || !suggestions) return;
    
    const mockRoutes = [
        { id: '300', desc: '300路：台中車站 - 靜宜大學 (優化公車專用道)' },
        { id: '301', desc: '301路: 新民高中 - 中興大學' },
        { id: '302', desc: '302路: 台中航空站 - 台中公園' },
        { id: '303', desc: '303路: 港區藝術中心 - 新民高中' },
        { id: '304', desc: '304路: 港區藝術中心 - 新民高中 (經五權路)' },
        { id: '305', desc: '305路: 大甲 - 鹿寮 - 台中車站' }
    ];
    
    input.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        suggestions.innerHTML = '';
        
        if (!val) {
            suggestions.classList.add('d-none');
            return;
        }
        
        const filtered = mockRoutes.filter(r => r.id.includes(val) || r.desc.includes(val));
        
        if (filtered.length > 0) {
            filtered.forEach(route => {
                const item = document.createElement('div');
                item.className = 'suggestion-item text-white';
                item.textContent = route.desc;
                item.addEventListener('click', () => {
                    input.value = route.id;
                    suggestions.classList.add('d-none');
                    // Automatically redirect to bus page
                    window.location.href = `/bus/${route.id}`;
                });
                suggestions.appendChild(item);
            });
            suggestions.classList.remove('d-none');
        } else {
            suggestions.classList.add('d-none');
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (e.target !== input && e.target !== suggestions) {
            suggestions.classList.add('d-none');
        }
    });
}

// Geolocation fetcher for driver reporting
function fetchDriverLocation() {
    const latInput = document.getElementById('report-latitude');
    const lngInput = document.getElementById('report-longitude');
    const locStatus = document.getElementById('location-status');
    
    if (!latInput || !lngInput) return;
    
    if (navigator.geolocation) {
        locStatus.innerHTML = '<i class="fas fa-spinner fa-spin text-indigo me-1"></i>正在取得目前 GPS 位置...';
        navigator.geolocation.getCurrentPosition(
            (position) => {
                latInput.value = position.coords.latitude;
                lngInput.value = position.coords.longitude;
                locStatus.innerHTML = `<i class="fas fa-map-marker-alt text-success me-1"></i>已取得 GPS 位置 (${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)})`;
            },
            (error) => {
                console.warn('Geolocation error:', error);
                locStatus.innerHTML = '<i class="fas fa-exclamation-circle text-warning me-1"></i>無法讀取 GPS，將僅送出路線狀態';
            },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else {
        locStatus.innerHTML = '<i class="fas fa-exclamation-circle text-warning me-1"></i>瀏覽器不支援 GPS 位置讀取';
    }
}

// Nearby Stops finder for passengers
async function findNearbyStops() {
    const section = document.getElementById('nearby-stops-section');
    const loading = document.getElementById('nearby-stops-loading');
    const list = document.getElementById('nearby-stops-list');
    
    if (!section || !loading || !list) return;
    
    // Show section and loading, hide previous list
    section.classList.remove('d-none');
    loading.classList.remove('d-none');
    list.innerHTML = '';
    
    // Helper to fetch and render
    const fetchStops = async (lat = '', lng = '') => {
        try {
            const url = (lat && lng) ? `/api/nearby-stops?lat=${lat}&lng=${lng}` : '/api/nearby-stops';
            const response = await fetch(url);
            if (!response.ok) throw new Error('API response error');
            const data = await response.json();
            
            loading.classList.add('d-none');
            
            if (data.status === 'success' && data.stops && data.stops.length > 0) {
                data.stops.forEach(stop => {
                    // Create cards
                    const col = document.createElement('div');
                    col.className = 'col-md-6 mb-3';
                    
                    let routeTags = stop.routes.map(r => 
                        `<a href="/bus/${r}" class="badge bg-primary bg-opacity-20 text-gradient text-decoration-none px-2 py-1 me-1 mb-1 border border-primary border-opacity-20 font-weight-bold">${r}路</a>`
                    ).join('');
                    
                    col.innerHTML = `
                        <div class="glass-card p-3 h-100 d-flex flex-column justify-content-between" style="border-left: 3px solid var(--accent-pink);">
                            <div>
                                <h6 class="text-white fw-bold mb-1">${stop.name}</h6>
                                <p class="text-muted small mb-2"><i class="fas fa-walking me-1 text-pink"></i> 距離約 ${stop.distance} 公尺</p>
                            </div>
                            <div class="mt-2">
                                <small class="text-muted d-block mb-1">行經路線：</small>
                                <div class="d-flex flex-wrap">
                                    ${routeTags}
                                </div>
                            </div>
                        </div>
                    `;
                    list.appendChild(col);
                });
            } else {
                list.innerHTML = `
                    <div class="col-12 text-center py-3 text-muted">
                        <i class="fas fa-exclamation-circle me-1"></i> 找不到附近的公車站牌。
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error fetching nearby stops:', error);
            loading.classList.add('d-none');
            showToast('取得附近站牌失敗，請稍後再試。', 'danger');
            list.innerHTML = `
                <div class="col-12 text-center py-3 text-danger">
                    <i class="fas fa-exclamation-triangle me-1"></i> 連線伺服器失敗
                </div>
            `;
        }
    };

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                fetchStops(position.coords.latitude, position.coords.longitude);
            },
            (error) => {
                console.warn('Geolocation denied or failed, using default center:', error);
                showToast('無法取得您的精確定位，改以預設台中市區中心搜尋。', 'info');
                fetchStops();
            },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else {
        showToast('您的瀏覽器不支援定位，已使用預設台中市區中心搜尋。', 'info');
        fetchStops();
    }
}

// DOM Content Loaded Handler
document.addEventListener('DOMContentLoaded', () => {
    setupSearchSuggestions();
    
    // If we have auto-refresh toasts (Flask flash messages), hook them
    const flashes = document.querySelectorAll('.flash-message-data');
    flashes.forEach(flash => {
        const msg = flash.dataset.message;
        const category = flash.dataset.category || 'info';
        showToast(msg, category);
    });
});
