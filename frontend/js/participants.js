/**
 * Управление участниками
 */

async function loadParticipants() {
    const search = document.getElementById('searchInput')?.value || '';
    const role = document.getElementById('roleFilter')?.value || '';
    let arr = await API.getParticipants(search);

    if (role) arr = arr.filter(p => p.role === role);

    const tbody = document.querySelector('#partTable tbody');
    if (!tbody) return;

    tbody.innerHTML = arr.map(p => `
        <tr class="fade-in">
            <td><strong>#${p.id}</strong></td>
            <td>${p.lastName} ${p.firstName}</td>
            <td>${p.organization || '—'}</td>
            <td><a href="mailto:${p.email}">${p.email}</a></td>
            <td><span class="status registered">${roleEmoji(p.role)} ${p.role}</span></td>
            <td>${p.badgePrinted
            ? '<span class="status printed">✓</span>'
            : `<button class="btn success btn-sm" onclick="printBadge(${p.id})">🖨️</button>`}
            </td>
            <td>
                <button class="btn danger btn-sm" onclick="delParticipant(${p.id})">🗑️</button>
            </td>
        </tr>
    `).join('');

    if (arr.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#999">Нет данных</td></tr>';
    }
}

async function addParticipant(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    try {
        await API.createParticipant(data);
        showToast('✅ Участник зарегистрирован');
        form.reset();
        loadParticipants();
    } catch (err) { }
}

async function delParticipant(id) {
    if (!confirm('Удалить участника?')) return;
    try {
        await API.deleteParticipant(id);
        showToast('🗑️ Удалён', 'warning');
        loadParticipants();
    } catch (err) { }
}

async function printBadge(id) {
    try {
        await API.printBadge(id);
        showToast('🏷️ Бейдж напечатан');
        loadParticipants();
    } catch (err) { }
}

// Экспорт функций
window.loadParticipants = loadParticipants;
window.addParticipant = addParticipant;
window.delParticipant = delParticipant;
window.printBadge = printBadge;