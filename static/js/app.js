// Main JavaScript for Rummy Score Tracker

const utils = {
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; top: 1rem; right: 1rem; padding: 0.75rem 1.25rem;
            border-radius: 10px; z-index: 200; font-size: 0.875rem; font-weight: 500;
            font-family: 'DM Sans', sans-serif;
            animation: fadeInUp 0.3s ease-out;
            backdrop-filter: blur(12px);
        `;

        if (type === 'success') {
            toast.style.background = 'rgba(39, 174, 96, 0.2)';
            toast.style.border = '1px solid rgba(39, 174, 96, 0.3)';
            toast.style.color = '#6ddb9e';
        } else {
            toast.style.background = 'rgba(192, 57, 43, 0.2)';
            toast.style.border = '1px solid rgba(192, 57, 43, 0.3)';
            toast.style.color = '#e88a82';
        }

        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s ease';
            setTimeout(() => {
                if (toast.parentNode) document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) target.scrollIntoView({ behavior: 'smooth' });
        });
    });
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = utils;
}
