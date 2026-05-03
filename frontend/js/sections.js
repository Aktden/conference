/**
 * Управление секциями
 */

async function loadSections() {
    const arr = await API.getSections();
    const tbody = document.querySelector('#secTable tbody');
    if (!tbody) return;

    tbody.innerHTML = arr.map(s => `
        <tr class="fade-in">
            <td><strong>#${s.id}</strong></td>
            <td>${s.title}</td>
            <td>${s.room || '—'}</td>
            <td>${s.startTime || '—'}</td>
            <td>${s.capacity}</td>
            <td><button class="btn danger btn-sm" onclick="delSection(${s.id})">🗑️</button></td>
        </tr>
    `).join('');

    if (arr.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999">Нет секций</td></tr>';
    }
}

async function addSection(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    data.capacity = +data.capacity;
    try {
        await API.createSection(data);
        showToast('✅ Секция создана');
        form.reset();
        loadSections();
    } catch (err) { }
}

async function delSection(id) {
    if (!confirm('Удалить секцию?')) return;
    try {
        await API.deleteSection(id);
        showToast('🗑️ Удалено', 'warning');
        loadSections();
    } catch (err) { }
}

window.loadSections = loadSections;
window.addSection = addSection;
window.delSection = delSection;