/**
 * Генерация отчётов и аналитики
 */

async function loadReports() {
    try {
        // Безопасная обёртка для запросов
        const safeFetch = async (url) => {
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return await res.json();
        };

        const stats = await safeFetch('/api/stats');
        const [parts, secs, att] = await Promise.all([
            safeFetch('/api/participants'),
            safeFetch('/api/sections'),
            safeFetch('/api/attendance')
        ]);

        // Заполнение сводки
        const summary = document.getElementById('summaryStats');
        if (summary) {
            summary.innerHTML = `
                <div class="summary-item"><div class="summary-value">${stats.participants || 0}</div><small>Всего участников</small></div>
                <div class="summary-item"><div class="summary-value">${stats.sections || 0}</div><small>Секций</small></div>
                <div class="summary-item"><div class="summary-value">${stats.attended || 0}/${stats.attendance_records || 0}</div><small>Присутствовали</small></div>
                <div class="summary-item"><div class="summary-value">${stats.attendance_rate || 0}%</div><small>Посещаемость</small></div>
                <div class="summary-item"><div class="summary-value">${stats.badges_printed || 0}</div><small>Бейджей</small></div>
            `;
        }

        // Заглушки для диаграмм (текстовые данные вместо пустых графиков)
        document.getElementById('chartRoles')?.innerHTML =
            `🎤 Докладчики: ${parts.filter(p => p.role === 'докладчик').length}<br>` +
            `👂 Слушатели: ${parts.filter(p => p.role === 'слушатель').length}<br>` +
            `⚙️ Организаторы: ${parts.filter(p => p.role === 'организатор').length}`;

        document.getElementById('chartSections')?.innerHTML =
            secs.map(s => {
                const count = att.filter(a => a.sectionId === s.id).length;
                return `<b>${s.title}</b>: ${count}/${s.capacity} мест`;
            }).join('<br>') || 'Нет секций';

        document.getElementById('chartAttendance')?.innerHTML =
            `✅ Присутствовали: ${stats.attended || 0}<br>❌ Отсутствовали: ${(stats.attendance_records || 0) - (stats.attended || 0)}`;

        document.getElementById('chartBadges')?.innerHTML =
            `🏷️ Напечатано: ${stats.badges_printed || 0}<br>⏳ Осталось: ${(stats.participants || 0) - (stats.badges_printed || 0)}`;

    } catch (e) {
        console.error('Reports load error:', e);
        document.querySelectorAll('.chart-placeholder').forEach(el =>
            el.innerHTML = `<span style="color:#ef476f">⚠️ Ошибка загрузки данных: ${e.message}</span>`
        );
    }
}

async function generateReport() {
    const [parts, secs, att] = await Promise.all([
        API.getParticipants(), API.getSections(), API.getAttendance()
    ]);

    const partMap = Object.fromEntries(parts.map(p => [p.id, p]));
    const secMap = Object.fromEntries(secs.map(s => [s.id, s]));

    let report = '=== ОТЧЁТ ПО КОНФЕРЕНЦИИ ===\n';
    report += `Дата: ${new Date().toLocaleString('ru-RU')}\n\n`;

    report += '👥 УЧАСТНИКИ:\n';
    parts.forEach(p => {
        report += `  #${p.id} ${p.lastName} ${p.firstName} [${p.role}] ${p.badgePrinted ? '✓' : '✗'}\n`;
    });

    report += '\n📚 СЕКЦИИ:\n';
    secs.forEach(s => {
        const count = att.filter(a => a.sectionId === s.id).length;
        report += `  #${s.id} ${s.title} (${count}/${s.capacity})\n`;
    });

    report += '\n📋 ПОСЕЩЕНИЕ:\n';
    att.forEach(r => {
        const p = partMap[r.participantId] || {};
        const s = secMap[r.sectionId] || {};
        report += `  ${p.lastName || '?'} → ${s.title || '?'}: ${r.status}\n`;
    });

    document.getElementById('reportOutput').textContent = report;
    showToast('📊 Отчёт сформирован');
}

function exportReport() {
    const text = document.getElementById('reportOutput')?.textContent || '';
    if (!text) { showToast('Сначала сгенерируйте отчёт', 'error'); return; }

    const blob = new Blob([text], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `report-${Date.now()}.txt`; a.click();
    URL.revokeObjectURL(url);
    showToast('📥 Отчёт скачан');
}

window.loadReports = loadReports;
window.generateReport = generateReport;
window.exportReport = exportReport;