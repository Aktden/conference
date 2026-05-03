/**
 * Генерация и печать бейджей
 */

async function loadBadges() {
    const arr = await API.getParticipants();
    const container = document.getElementById('badgeList');
    if (!container) return;

    container.innerHTML = arr.map(p => `
        <div class="badge-preview fade-in">
            <div class="badge-header">🎓 КОНФЕРЕНЦИЯ 2025</div>
            <div class="badge-name">${p.lastName} ${p.firstName}</div>
            <div>${p.organization || '—'}</div>
            <div class="badge-role">${roleEmoji(p.role)} ${p.role}</div>
            <div style="margin-top:10px;font-family:monospace">ID: #${p.id}</div>
            ${!p.badgePrinted
            ? `<button class="btn success" style="margin-top:15px" onclick="printBadge(${p.id})">🖨️ Печать</button>`
            : '<div style="margin-top:15px;color:#06d6a0;font-weight:500">✓ Напечатан</div>'
        }
        </div>
    `).join('');
}

async function printBadge(id) {
    try {
        await API.printBadge(id);
        showToast('🏷️ Бейдж напечатан');
        loadBadges();
    } catch (err) { }
}

async function printAllBadges() {
    try {
        const res = await API.printAllBadges();
        showToast(`🖨️ Напечатано: ${res.count}`);
        loadBadges();
    } catch (err) { }
}

window.loadBadges = loadBadges;
window.printBadge = printBadge;
window.printAllBadges = printAllBadges;