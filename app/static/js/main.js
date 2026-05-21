// Interactivity & Swap Control for Taichung Bus 2.0

document.addEventListener('DOMContentLoaded', () => {
    // 1. Swap button for start and end inputs
    const swapBtn = document.getElementById('swap-btn');
    if (swapBtn) {
        swapBtn.addEventListener('click', () => {
            const startInput = document.getElementById('start-input');
            const endInput = document.getElementById('end-input');
            if (startInput && endInput) {
                const temp = startInput.value;
                startInput.value = endInput.value;
                endInput.value = temp;
                
                // Add micro-animation effect
                swapBtn.style.transform = 'rotate(180deg)';
                setTimeout(() => {
                    swapBtn.style.transform = 'rotate(0deg)';
                }, 300);
            }
        });
    }

    // 2. Auto-geolocation helper (for demonstration)
    const geoBtn = document.getElementById('geo-btn');
    if (geoBtn) {
        geoBtn.addEventListener('click', () => {
            if (navigator.geolocation) {
                geoBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>定位中...';
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        console.log(`Current position: ${lat}, ${lng}`);
                        // In a real app we might set hidden input fields or redirect
                        geoBtn.innerHTML = '📍 定位成功！';
                        setTimeout(() => {
                            geoBtn.innerHTML = '📍 取得目前位置';
                        }, 2000);
                    },
                    (error) => {
                        console.error(error);
                        geoBtn.innerHTML = '❌ 定位失敗';
                        setTimeout(() => {
                            geoBtn.innerHTML = '📍 取得目前位置';
                        }, 2000);
                    }
                );
            } else {
                alert('您的瀏覽器不支援定位功能。');
            }
        });
    }
});
