/**
 * Глобальные утилиты приложения
 */

// Экспорт данных
async function exportData() {
    try {
        await API.exportData();
        showToast('📥 Данные экспортированы');
    } catch (e) { }
}

// Сброс всех данных
async function clearAll() {
    if (!confirm('⚠️ Удалить ВСЕ данные? Это действие необратимо!')) return;
    try {
        await API.importData({ participants: [], sections: [], attendance: [] });
        showToast('🗑️ Данные сброшены', 'warning');
        location.reload();
    } catch (e) { }
}

// Форматирование даты
function formatDate(str) {
    if (!str) return '—';
    return new Date(str).toLocaleString('ru-RU', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
    });
}

// Эмодзи для ролей
function roleEmoji(role) {
    return { 'докладчик': '🎤', 'слушатель': '👂', 'организатор': '⚙️' }[role] || '👤';
}

// Загрузка участников в select
async function loadParticipantsForSelect() {
    const sel = document.querySelector('select[name="participantId"]');
    if (!sel) return;
    const arr = await API.getParticipants();
    sel.innerHTML = '<option value="">Выберите участника</option>' +
        arr.map(p => `<option value="${p.id}">${p.lastName} ${p.firstName}</option>`).join('');
}

// Загрузка секций в select
async function loadSectionsForSelect() {
    const sel = document.querySelector('select[name="sectionId"]');
    if (!sel) return;
    const arr = await API.getSections();
    sel.innerHTML = '<option value="">Выберите секцию</option>' +
        arr.map(s => `<option value="${s.id}">${s.title} (${s.room})</option>`).join('');
}

// Закрытие модального окна
function closeModal(id) {
    document.getElementById(id)?.classList.remove('active');
}

// Инициализация модальных окон
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', e => {
            if (e.target === overlay) overlay.classList.remove('active');
        });
    });
});