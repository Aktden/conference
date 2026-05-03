/**
 * API-клиент для Python бэкенда
 */
const API = {
    BASE: '/api',

    async request(endpoint, options = {}) {
        const config = {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        };

        try {
            const res = await fetch(`${this.BASE}${endpoint}`, config);

            if (options.blob) {
                return res;
            }

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data?.error || `Ошибка ${res.status}`);
            }
            return data;
        } catch (e) {
            console.error('API Error:', e);
            showToast(e.message, 'error');
            throw e;
        }
    },

    // Участники
    async getParticipants(query = '') {
        return this.request(`/participants${query ? '?search=' + encodeURIComponent(query) : ''}`);
    },

    async createParticipant(data) {
        return this.request('/participants', { method: 'POST', body: JSON.stringify(data) });
    },

    async updateParticipant(id, data) {
        return this.request(`/participants/${id}`, { method: 'PUT', body: JSON.stringify(data) });
    },

    async deleteParticipant(id) {
        return this.request(`/participants/${id}`, { method: 'DELETE' });
    },

    // Секции
    async getSections() {
        return this.request('/sections');
    },

    async createSection(data) {
        return this.request('/sections', { method: 'POST', body: JSON.stringify(data) });
    },

    async deleteSection(id) {
        return this.request(`/sections/${id}`, { method: 'DELETE' });
    },

    // Посещение
    async getAttendance() {
        return this.request('/attendance');
    },

    async registerAttendance(data) {
        return this.request('/attendance', { method: 'POST', body: JSON.stringify(data) });
    },

    async updateAttendance(pid, sid, attended) {
        return this.request(`/attendance/${pid}/${sid}`, {
            method: 'PUT',
            body: JSON.stringify({ attended })
        });
    },

    // Бейджи
    async printBadge(id) {
        return this.request(`/badges/${id}/print`, { method: 'POST' });
    },

    async printAllBadges() {
        return this.request('/badges/print-all', { method: 'POST' });
    },

    // Статистика
    async getStats() {
        return this.request('/stats');
    },

    // Экспорт/Импорт
    async exportData() {
        const res = await fetch(`${this.BASE}/export`);
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conference-export-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    },

    async importData(data) {
        return this.request('/import', { method: 'POST', body: JSON.stringify(data) });
    }
};

// Toast уведомления
function showToast(msg, type = 'success') {
    const icons = { success: '✓', error: '✕', warning: '⚠' };
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<span>${icons[type] || '•'}</span> ${msg}`;
    document.body.appendChild(t);
    setTimeout(() => {
        t.style.opacity = '0';
        t.style.transform = 'translateY(10px)';
        setTimeout(() => t.remove(), 300);
    }, 3000);
}

// Утилиты
function roleEmoji(role) {
    return { 'докладчик': '🎤', 'слушатель': '👥', 'организатор': '⚙️' }[role] || '👤';
}

function roleClass(role) {
    return { 'докладчик': 'blue', 'слушатель': 'purple', 'организатор': 'cyan' }[role] || '';
}

function formatDate(str) {
    if (!str) return '—';
    return new Date(str).toLocaleString('ru-RU');
}

// Глобальные функции
window.exportData = async function() {
    try {
        await API.exportData();
        showToast('Данные экспортированы');
    } catch(e) {
        showToast('Ошибка экспорта', 'error');
    }
};

window.clearAll = async function() {
    if (!confirm('⚠️ Удалить ВСЕ данные? Это необратимо!')) return;
    try {
        await API.importData({ participants: [], sections: [], attendance: [] });
        showToast('Данные сброшены', 'warning');
        setTimeout(() => location.reload(), 1000);
    } catch(e) {
        showToast('Ошибка сброса', 'error');
    }
};

window.loadParticipantsForSelect = async function() {
    const sel = document.querySelector('select[name="participantId"]');
    if (!sel) return;
    const arr = await API.getParticipants();
    sel.innerHTML = '<option value="">Выберите участника...</option>' +
        arr.map(p => `<option value="${p.id}">${p.lastName} ${p.firstName}</option>`).join('');
};

window.loadSectionsForSelect = async function() {
    const sel = document.querySelector('select[name="sectionId"]');
    if (!sel) return;
    const arr = await API.getSections();
    sel.innerHTML = '<option value="">Выберите секцию...</option>' +
        arr.map(s => `<option value="${s.id}">${s.title}${s.room ? ' · ' + s.room : ''}</option>`).join('');
};