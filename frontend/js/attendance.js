/**
 * Модуль учёта посещения секций
 */

// Загрузка записей о посещении
async function loadAttendance() {
    const tbody = document.querySelector('#attTable tbody');
    if (!tbody) return;

    try {
        // Загружаем все данные параллельно
        const [attendance, participants, sections] = await Promise.all([
            fetch('/api/attendance').then(r => r.json()),
            fetch('/api/participants').then(r => r.json()),
            fetch('/api/sections').then(r => r.json())
        ]);

        // Создаём словари для быстрого поиска
        const partMap = Object.fromEntries(participants.map(p => [p.id, p]));
        const secMap = Object.fromEntries(sections.map(s => [s.id, s]));

        tbody.innerHTML = attendance.map(r => {
            const p = partMap[r.participantId] || { lastName: '?', firstName: '?' };
            const s = secMap[r.sectionId] || { title: '?' };

            let statusClass = 'registered';
            if (r.status === 'присутствовал') statusClass = 'attended';
            if (r.status === 'отсутствовал') statusClass = 'absent';

            return `
                <tr>
                    <td>${p.lastName} ${p.firstName}</td>
                    <td>${s.title}</td>
                    <td><span class="status ${statusClass}">${r.status}</span></td>
                    <td>
                        ${r.status === 'зарегистрирован' ? `
                            <button onclick="markAttendance(${r.participantId}, ${r.sectionId}, true)" class="btn success btn-sm">✅</button>
                            <button onclick="markAttendance(${r.participantId}, ${r.sectionId}, false)" class="btn danger btn-sm">❌</button>
                        ` : '<span style="color: #999;">—</span>'}
                    </td>
                </tr>
            `;
        }).join('');

        if (attendance.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px; color: #999;">Нет записей о посещении</td></tr>';
        }
    } catch (error) {
        console.error('Ошибка загрузки посещения:', error);
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px; color: #ef476f;">Ошибка загрузки данных</td></tr>';
    }
}

async function registerAttendance(e) {
    e.preventDefault();

    const form = e.target;
    const pId = parseInt(form.participantId.value);
    const sId = parseInt(form.sectionId.value);

    if (!pId || !sId) {
        alert("⚠️ Выберите участника и секцию");
        return;
    }

    try {
        const response = await fetch('/api/attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ participantId: pId, sectionId: sId })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || `Ошибка сервера: ${response.status}`);
        }

        alert('✅ Участник успешно записан!');
        form.reset();
        loadAttendance();

    } catch (error) {
        console.error('Attendance Error:', error);
        alert('❌ ' + error.message);
    }
}

// Отметка посещаемости (присутствовал/отсутствовал)
async function markAttendance(participantId, sectionId, attended) {
    try {
        const status = attended ? 'присутствовал' : 'отсутствовал';

        const response = await fetch(`/api/attendance/${participantId}/${sectionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ attended })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `Ошибка ${response.status}`);
        }

        alert(`✅ Статус обновлён: ${status}`);
        loadAttendance();

    } catch (error) {
        console.error('Ошибка обновления статуса:', error);
        alert('❌ Ошибка: ' + error.message);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    loadAttendance();
    loadParticipantsForSelect(); // Используем функцию из app.js
    loadSectionsForSelect();     // Используем функцию из app.js

    // Привязываем обработчик к форме
    const form = document.getElementById('attForm');
    if (form) {
        form.addEventListener('submit', registerAttendance);
    }
});