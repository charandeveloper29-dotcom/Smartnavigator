/**
 * Smart Navigator - Services JavaScript
 * Handles service button clicks and tracking
 */

document.addEventListener('DOMContentLoaded', function() {
    initServiceButtons();
});

/**
 * Initialize service buttons with click handlers
 */
function initServiceButtons() {
    const serviceButtons = document.querySelectorAll('.service-btn');
    
    serviceButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Get service details
            const service = this.dataset.service;
            const placeId = this.dataset.placeId;
            const city = this.dataset.city;
            
            // Add loading state
            this.classList.add('loading');
            
            // Track the click (optional analytics)
            trackServiceClick(service, placeId, city);
            
            // Remove loading state after a short delay
            setTimeout(() => {
                this.classList.remove('loading');
            }, 1000);
        });
    });
}

/**
 * Track service button clicks for analytics
 */
function trackServiceClick(service, placeId, city) {
    fetch(`/api/services/${service}/url?city=${encodeURIComponent(city || '')}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log(`✅ ${service} service clicked:`, data);
                
                // Optional: Send analytics to your backend
                sendAnalytics(service, placeId, city);
            }
        })
        .catch(error => {
            console.error('Error tracking service click:', error);
        });
}

/**
 * Send analytics data to backend (optional)
 */
function sendAnalytics(service, placeId, city) {
    fetch('/api/services/track', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            service: service,
            place_id: placeId,
            city: city,
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Analytics sent:', data);
    })
    .catch(error => {
        console.error('Analytics error:', error);
    });
}

/**
 * Get user's location and suggest nearby services
 */
function suggestNearbyServices(latitude, longitude, city) {
    fetch(`/api/services/nearby?lat=${latitude}&lng=${longitude}&city=${encodeURIComponent(city)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Nearby services:', data.services);
                // You can update UI here to show availability
            }
        })
        .catch(error => {
            console.error('Error fetching nearby services:', error);
        });
}