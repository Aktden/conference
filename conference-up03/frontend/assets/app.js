"use strict";

const $ = (s, root = document) => root.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const paths = {
  dashboard:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  users:'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M16 3a4 4 0 0 1 0 8 M22 21v-2a4 4 0 0 0-3-3.87 M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
  sections:'M3 5h18v15H3z M7 2v6 M17 2v6 M3 11h18 M7 15h3 M14 15h3',
  check:'M20 6 9 17l-5-5',
  attendance:'M9 3H4v18h16V3h-5 M9 2h6v4H9z M8 13l3 3 5-6',
  badge:'M4 5h16v16H4z M9 2h6v5H9z M8 17h8 M14 11a2 2 0 1 1-4 0 2 2 0 0 1 4 0',
  chart:'M3 3v18h18 M7 17v-5 M12 17V7 M17 17v-8',
  plus:'M12 5v14 M5 12h14',
  search:'M21 21l-5-5 M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0',
  arrow:'M5 12h14 M13 6l6 6-6 6',
  logout:'M9 4H3v16h6 M9 12h12 M17 8l4 4-4 4',
  close:'M6 6l12 12 M6 18 18 6',
  edit:'m15 5 4 4 M4 20l4-1L21 6l-4-4L4 15z',
  trash:'M3 6h18 M5 6l1 15h12l1-15 M9 6V3h6v3 M10 10v7 M14 10v7',
  clock:'M12 8v5l3 2 M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0',
  pin:'M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0 M15 10a3 3 0 1 1-6 0 3 3 0 0 1 6 0',
  download:'M12 3v12 M7 10l5 5 5-5 M4 16v5h16v-5',
  shield:'M12 2 3 6v6c0 6 9 10 9 10s9-4 9-10V6z M8 12l3 3 5-6',
  print:'M6 9V3h12v6 M6 18H3V9h18v9h-3 M6 14h12v8H6z',
  menu:'M4 6h16 M4 12h16 M4 18h16',
};
const icon = (n) => `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="${paths[n] || paths.check}"/></svg>`;
const roles = {admin:"Администратор",operator:"Оператор",viewer:"Наблюдатель"};
const pages = {dashboard:["Обзор","dashboard"],participants:["Участники","users"],sections:["Секции","sections"],attendance:["Посещаемость","attendance"],badges:["Бейджи","badge"],reports:["Отчёты","chart"],audit:["Журнал действий","shield"]};
let state = {user:null,csrf:"",demo:false,participants:[],sections:[],attendance:[],stats:{},audit:[],search:"",filter:"",page:1};
let toastTimer, renderVersion = 0;
const staff = () => state.user && state.user.role !== "viewer";
const admin = () => state.user?.role === "admin";
const pageName = () => location.hash.slice(1).split("?")[0] || "dashboard";
const canView = p => state.user && (p !== "audit" || admin()) && (!["participants","attendance","badges"].includes(p) || staff());
function toast(message) { $("#toast").textContent = message; clearTimeout(toastTimer); toastTimer = setTimeout(() => $("#toast").textContent = "", 4500); }
async function api(path, method = "GET", data) {
  const response = await fetch(`/api${path}`, {
    method, credentials:"same-origin", headers:{"Content-Type":"application/json",...(state.csrf ? {"X-CSRF-Token":state.csrf} : {})},
    ...(data === undefined ? {} : {body:JSON.stringify(data)})
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/login") { state.user = null; showLogin(); }
    throw new Error(typeof body.detail === "string" ? body.detail : `Ошибка запроса (${response.status})`);
  }
  return body;
}
const badgeRole = role => `<span class="pill ${role === "докладчик" ? "speaker" : role === "организатор" ? "organizer" : ""}">${esc(role)}</span>`;
const initials = p => esc((p.firstName?.[0] || "") + (p.lastName?.[0] || ""));
const person = p => `<div class="person"><span class="avatar">${initials(p)}</span><div><strong>${esc(p.lastName)} ${esc(p.firstName)}</strong><small>${esc(p.email || p.organization)}</small></div></div>`;
const empty = (title, sub="Попробуйте изменить поиск или добавить новую запись.") => `<div class="empty"><strong>${esc(title)}</strong>${esc(sub)}</div>`;
const button = (label, action, ico="plus", cls="primary", attrs="") => `<button class="btn ${cls}" data-action="${action}" ${attrs}>${icon(ico)}${label}</button>`;
function showLogin(message = "") {
  renderVersion++;
  $("#modal").close();
  $("#root").innerHTML = `<div class="login-page"><section class="login-story"><div><div class="brand"><div class="brand-mark">К</div><div><strong>Конференция</strong><small>Центр управления</small></div></div><h1>Хорошие встречи<br>начинаются<br>с порядка.</h1><p>Участники, программа и регистрация — всё, что нужно вашей команде в день конференции.</p></div><div class="story-detail">01 / РЕГИСТРАЦИЯ &nbsp; 02 / СЕКЦИИ &nbsp; 03 / СОБЫТИЯ</div></section><main class="login-form-wrap" id="content"><form id="login-form" class="login-form"><div class="eyebrow">Рабочее пространство команды</div><h2>Добро пожаловать</h2><p class="subtitle">Войдите, чтобы продолжить работу с мероприятием.</p><div class="error" role="alert" id="login-error">${esc(message)}</div><label class="field">Логин<input name="username" autocomplete="username" required maxlength="80" placeholder="Ваш логин"></label><label class="field">Пароль<input type="password" name="password" autocomplete="current-password" required maxlength="256" placeholder="Введите пароль"></label><button type="submit" class="btn primary full">Войти в пространство ${icon("arrow")}</button>${state.demo ? `<details class="demo-details" open><summary>Доступ к учебной демонстрации</summary><p class="hint">Все участники и адреса в демо вымышлены.</p>${[["admin","DemoAdmin!2026"],["operator","DemoOperator!2026"],["viewer","DemoViewer!2026"]].map(([u,p])=>`<div class="demo-account"><span>${roles[u]}</span><code>${u} / ${p}</code></div>`).join("")}</details>` : ""}<footer>Конференция · версия 3.0 · УП.03</footer></form></main></div>`;
  $("#login-form").addEventListener("submit", async e => {
    e.preventDefault(); const form = e.currentTarget; const btn = $("button",form); btn.disabled = true;
    try { const result = await api("/auth/login","POST",Object.fromEntries(new FormData(form))); state.user=result.user; state.csrf=result.csrfToken; await refresh(); }
    catch(err) { $("#login-error").textContent = err.message; }
    finally { btn.disabled=false; }
  });
}
async function refresh() {
  const version = ++renderVersion;
  const [stats,sections,participants,attendance,audit] = await Promise.all([
    api("/stats"),api("/sections"),staff()?api("/participants"):[],staff()?api("/attendance"):[],admin()?api("/audit"):[]
  ]);
  if(version!==renderVersion || !state.user) return;
  Object.assign(state,{stats,sections,participants,attendance,audit}); renderShell();
}
function renderShell() {
  let p = pageName(); if(!pages[p] || !canView(p)) p="dashboard";
  document.title=`${pages[p][0]} — Конференция`;
  $("#root").innerHTML=`<div class="app"><aside class="sidebar" aria-label="Главная навигация"><a href="#dashboard" class="brand"><div class="brand-mark">К</div><div><strong>Конференция</strong><small>Центр управления</small></div></a><div class="nav-label">Рабочее пространство</div><nav class="nav">${Object.entries(pages).filter(([key])=>canView(key)).map(([key,[label,ico]])=>`<a href="#${key}" class="${key===p?"active":""}" ${key===p?'aria-current="page"':""}>${icon(ico)}${label}${key==="participants"?`<span class="count">${state.stats.participants}</span>`:""}</a>`).join("")}</nav><div class="sidebar-bottom"><div class="event-card"><span class="dot"></span>Система доступна<strong>Встречи, которые объединяют</strong>Регистрация и сопровождение<br>вашего мероприятия</div><div class="sidebar-footer">Версия 3.0 · ${state.demo?"Учебный стенд":"Рабочий режим"}</div></div></aside><div class="workspace"><header class="topbar"><button class="icon-btn mobile-menu" data-action="menu" aria-label="Открыть меню" aria-expanded="false">${icon("menu")}</button><div class="breadcrumb">Конференция<span>/</span>${pages[p][0]}</div><div class="top-right">${state.demo?'<span class="env-label">Демо-данные</span>':""}<div class="profile"><span class="avatar">${esc(state.user.display_name[0])}</span><div class="profile-text"><strong>${esc(state.user.display_name)}</strong><small>${roles[state.user.role]}</small></div></div><button class="icon-btn" data-action="logout" title="Выйти" aria-label="Выйти">${icon("logout")}</button></div></header><main class="main" id="content" tabindex="-1"></main></div></div>`;
  const headings={dashboard:["Обзор конференции","Всё о мероприятии — в одном рабочем пространстве."],participants:["Участники","Управляйте регистрацией и данными гостей."],sections:["Программа и секции","Расписание, аудитории и свободные места."],attendance:["Посещаемость","Записывайте участников на секции и отмечайте визиты."],badges:["Именные бейджи","Подготовьте бейджи к печати и отметьте выдачу."],reports:["Отчёты и данные","Статистика мероприятия, выгрузка и восстановление."],audit:["Журнал действий","Последние 100 операций в системе. Время указано в UTC."]};
  const [title,sub]=headings[p];
  const action=p==="participants"?button("Добавить участника","new-participant"):p==="sections"&&admin()?button("Создать секцию","new-section"):p==="attendance"?button("Записать на секцию","new-attendance"):p==="dashboard"&&staff()?button("Новый участник","new-participant"):p==="badges"?button("Печатать все","print-all","print"):"";
  $("#content").innerHTML=`<div class="page-head"><div><div class="eyebrow">${p==="dashboard"?"Мероприятие под контролем":"Конференция / "+pages[p][0]}</div><h1>${title}</h1><p class="subtitle">${sub}</p></div>${action}</div><div id="page-body"></div><footer class="statusline"><span>Конференция · Учёт и сопровождение мероприятия</span><span><span class="dot"></span>Данные обновлены ${new Date().toLocaleTimeString("ru-RU",{hour:"2-digit",minute:"2-digit"})}</span></footer>`;
  ({dashboard:renderDashboard,participants:renderParticipants,sections:renderSections,attendance:renderAttendance,badges:renderBadges,reports:renderReports,audit:renderAudit}[p])();
}
function metrics() {
  const s=state.stats;
  return `<div class="metrics">${[["Участников",s.participants,"users","В общем списке регистрации"],["Секции программы",s.sections,"sections","Направления конференции"],["Посещаемость",`${s.attendance_rate}%`,"attendance",`${s.attended} из ${s.attendance_records} регистраций`],["Бейджи выданы",s.badges_printed,"badge",`${Math.max(0,s.participants-s.badges_printed)} ожидают выдачи`]].map(([l,v,i,t])=>`<article class="metric"><div class="metric-top">${l}<span class="metric-icon">${icon(i)}</span></div><div class="metric-value">${v}</div><div class="metric-note">${t}</div></article>`).join("")}</div>`;
}
function renderDashboard() {
  const s=state.stats,rate=s.attendance_rate;
  $("#page-body").innerHTML=`<section class="hero"><div><div class="eyebrow">Команда на одной волне</div><h2>Всё готово к продуктивному дню</h2><p>Следите за регистрацией, распределяйте гостей по секциям и уделяйте больше времени живому общению.</p></div><svg class="hero-symbol" viewBox="0 0 120 100" aria-hidden="true"><circle cx="65" cy="49" r="38"/><circle cx="65" cy="49" r="25"/><path d="M0 49h115 M65 0v100"/><circle class="solid" cx="65" cy="49" r="9"/><circle class="solid" cx="103" cy="49" r="5"/><circle class="solid" cx="65" cy="11" r="5"/></svg></section>${metrics()}<div class="grid-two"><section class="panel"><div class="panel-heading"><div><h2>Программа конференции</h2><p>Секции в порядке начала</p></div><a class="text-link" href="#sections">Все секции →</a></div>${state.sections.length?state.sections.slice(0,4).map(x=>`<div class="section-row"><div class="time">${esc(x.startTime||"—")}</div><div><strong>${esc(x.title)}</strong><small>${esc(x.room||"Аудитория не указана")}</small></div><div class="capacity">${x.registered} / ${x.capacity} мест<progress value="${x.registered}" max="${x.capacity}" aria-label="Заполненность ${esc(x.title)}"></progress></div></div>`).join(""):empty("Пока нет секций")}</section><section class="panel"><div class="panel-heading"><div><h2>Участие в секциях</h2><p>По отметкам команды регистрации</p></div></div><div class="attendance-visual"><svg class="ring" viewBox="0 0 120 120" role="img" aria-label="Посещаемость ${rate} процентов"><circle cx="60" cy="60" r="48" fill="none" stroke="#e7eddf" stroke-width="11"/><circle cx="60" cy="60" r="48" fill="none" stroke="#497858" stroke-width="11" stroke-dasharray="${rate*3.016} 302" transform="rotate(-90 60 60)" stroke-linecap="round"/><text x="60" y="61" text-anchor="middle">${rate}%</text><text x="60" y="77" class="subtext" text-anchor="middle">ПОСЕЩАЕМОСТЬ</text></svg><div class="legend"><div><span class="bullet"></span>Присутствовали<strong>${s.attended}</strong></div><div><span class="bullet pale"></span>Без отметки присутствия<strong>${s.attendance_records-s.attended}</strong></div></div></div><div class="panel-foot">Один участник может посетить несколько секций.</div></section></div>${staff()?`<section class="panel"><div class="panel-heading"><div><h2>Последние регистрации</h2><p>Недавно добавленные участники</p></div><a class="text-link" href="#participants">Все участники →</a></div>${participantTable(state.participants.slice(0,5),false)}</section>`:""}`;
}
function participantTable(items, editable=true) {
  if(!items.length)return empty("Участники не найдены");
  return `<div class="table-wrap"><table><thead><tr><th>Участник</th><th>Организация</th><th>Роль</th><th>Бейдж</th>${editable?"<th>Действия</th>":""}</tr></thead><tbody>${items.map(p=>`<tr><td>${person(p)}</td><td class="muted">${esc(p.organization||"—")}</td><td>${badgeRole(p.role)}</td><td><span class="pill ${p.badgePrinted?"success":"pending"}">${p.badgePrinted?"Выдан":"Ожидает"}</span></td>${editable?`<td><div class="actions"><button class="icon-btn" data-action="edit-participant" data-id="${p.id}" aria-label="Редактировать ${esc(p.lastName)}">${icon("edit")}</button>${admin()?`<button class="icon-btn" data-action="delete-participant" data-id="${p.id}" aria-label="Удалить ${esc(p.lastName)}">${icon("trash")}</button>`:""}</div></td>`:""}</tr>`).join("")}</tbody></table></div>`;
}
const searchInput = label=>`<label class="search">${icon("search")}<input id="search" aria-label="${label}" placeholder="${label}" value="${esc(state.search)}"></label>`;
function renderParticipants() {
  $("#page-body").innerHTML=`<section class="panel"><div class="toolbar">${searchInput("Поиск по имени, email или организации")}<select id="filter" aria-label="Роль участника"><option value="">Все роли</option>${["докладчик","слушатель","организатор"].map(r=>`<option ${state.filter===r?"selected":""}>${r}</option>`).join("")}</select></div><div id="list"></div></section>`;
  const update=()=>{
    const list=state.participants.filter(p=>`${p.lastName} ${p.firstName} ${p.email} ${p.organization}`.toLocaleLowerCase("ru").includes(state.search.toLocaleLowerCase("ru"))&&(!state.filter||p.role===state.filter));
    const total=Math.max(1,Math.ceil(list.length/15));state.page=Math.min(state.page,total);
    $("#list").innerHTML=participantTable(list.slice((state.page-1)*15,state.page*15))+`<div class="pagination"><span>Найдено: ${list.length} · страница ${state.page} из ${total}</span><div class="actions"><button class="btn small" id="prev" ${state.page<=1?"disabled":""}>Назад</button><button class="btn small" id="next" ${state.page>=total?"disabled":""}>Далее</button></div></div>`;
    $("#prev").onclick=()=>{state.page--;update();};$("#next").onclick=()=>{state.page++;update();};
  }; bindFilters(update);update();
}
function bindFilters(update) {
  $("#search")?.addEventListener("input",e=>{state.search=e.target.value;state.page=1;update();});
  $("#filter")?.addEventListener("change",e=>{state.filter=e.target.value;state.page=1;update();});
}
function renderSections() {
  $("#page-body").innerHTML=state.sections.length?`<div class="section-grid">${state.sections.map((s,i)=>`<article class="section-card"><span class="section-number">СЕКЦИЯ ${String(i+1).padStart(2,"0")}</span><h2 class="overflow-name">${esc(s.title)}</h2><div class="section-meta"><span>${icon("clock")}${esc(s.startTime||"Время не указано")}</span><span>${icon("pin")}${esc(s.room||"Аудитория не указана")}</span></div><div class="progress-label"><span>${s.registered} зарегистрировано</span><span class="muted">${s.capacity-s.registered} свободно</span></div><progress value="${s.registered}" max="${s.capacity}" aria-label="Заполненность секции"></progress><div class="actions">${staff()?button("Записать участника","new-attendance","plus","small",`data-id="${s.id}"`):""}${admin()?`<button class="icon-btn" data-action="edit-section" data-id="${s.id}" aria-label="Редактировать секцию">${icon("edit")}</button><button class="icon-btn" data-action="delete-section" data-id="${s.id}" aria-label="Удалить секцию">${icon("trash")}</button>`:""}</div></article>`).join("")}</div>`:empty("Создайте первую секцию");
}
function renderAttendance() {
  $("#page-body").innerHTML=`<section class="panel"><div class="toolbar">${searchInput("Поиск участника")}<select id="filter" aria-label="Выбор секции"><option value="">Все секции</option>${state.sections.map(s=>`<option value="${s.id}" ${state.filter==s.id?"selected":""}>${esc(s.title)}</option>`).join("")}</select></div><div id="list"></div></section>`;
  const update=()=>{
    const items=state.attendance.filter(a=>(!state.filter||a.sectionId==state.filter)&&`${a.lastName} ${a.firstName}`.toLocaleLowerCase("ru").includes(state.search.toLocaleLowerCase("ru")));
    $("#list").innerHTML=items.length?`<div class="table-wrap"><table><thead><tr><th>Участник</th><th>Секция</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${items.map(a=>`<tr><td>${person(a)}</td><td>${esc(a.sectionTitle)}</td><td><span class="pill ${a.status==="присутствовал"?"success":a.status==="отсутствовал"?"absent":"pending"}">${esc(a.status)}</span></td><td><div class="actions">${button(a.status==="присутствовал"?"Отсутствует":"Пришёл","toggle-attendance","check","small",`data-pid="${a.participantId}" data-sid="${a.sectionId}" data-value="${a.status!=="присутствовал"}"`)}<button class="icon-btn" data-action="delete-attendance" data-pid="${a.participantId}" data-sid="${a.sectionId}" aria-label="Отменить запись">${icon("trash")}</button></div></td></tr>`).join("")}</tbody></table></div>`:empty("Записи не найдены");
  };bindFilters(update);update();
}
function badgeMarkup(p) { return `<div class="badge-preview"><div class="badge-event">Конференция / участник</div><div class="badge-id">ID ${String(p.id).padStart(4,"0")}</div><div class="badge-name">${esc(p.firstName)}<br>${esc(p.lastName)}</div><div class="badge-org">${esc(p.organization||"Участник конференции")}</div>${badgeRole(p.role)}</div>`; }
function renderBadges() {
  $("#page-body").innerHTML=`<div class="notice">Печать открывает системное окно браузера. После фактической выдачи нажмите «Выдан»: отмена печати не изменяет статус бейджа.</div><section class="panel"><div class="toolbar">${searchInput("Найти бейдж по имени")}<select id="filter" aria-label="Статус бейджа"><option value="">Все бейджи</option><option value="pending" ${state.filter==="pending"?"selected":""}>Ожидают выдачи</option><option value="issued" ${state.filter==="issued"?"selected":""}>Выданы</option></select></div></section><div id="list"></div>`;
  const update=()=>{
    const people=state.participants.filter(p=>(!state.filter||(state.filter==="issued")===p.badgePrinted)&&`${p.firstName} ${p.lastName}`.toLocaleLowerCase("ru").includes(state.search.toLocaleLowerCase("ru")));
    $("#list").innerHTML=people.length?`<div class="badge-grid">${people.map(p=>`<article class="badge-card">${badgeMarkup(p)}<div class="actions">${button("Печать","print-one","print","small",`data-id="${p.id}"`)}${button(p.badgePrinted?"Выдан · отменить":"Выдан","toggle-badge","check",`small ${p.badgePrinted?"":"primary"}`,`data-id="${p.id}"`)}</div></article>`).join("")}</div>`:empty("Бейджи не найдены");
  };bindFilters(update);update();
}
function renderReports() {
  $("#page-body").innerHTML=`${metrics()}<div class="grid-two"><section class="panel"><div class="panel-heading"><h2>Заполненность секций</h2></div><div class="report-content report-bars">${state.sections.map(s=>`<div class="report-bar"><p><span>${esc(s.title)}</span><span>${s.registered} / ${s.capacity}</span></p><progress value="${s.registered}" max="${s.capacity}" aria-label="${esc(s.title)}"></progress></div>`).join("")||empty("Нет секций")}</div></section><section class="panel"><div class="panel-heading"><h2>Роли участников</h2></div><div class="report-content report-bars">${state.stats.roles.map(r=>`<div class="report-bar"><p><span>${esc(r.role)}</span><span>${r.count}</span></p><progress value="${r.count}" max="${state.stats.participants||1}" aria-label="${esc(r.role)}"></progress></div>`).join("")||empty("Нет участников")}</div></section></div>${admin()?`<section class="panel"><div class="panel-heading"><h2>Экспорт и восстановление</h2><span class="pill organizer">Администратор</span></div><div class="report-content"><p>JSON содержит участников, секции и посещения. CSV подходит для таблиц. Пароли и сессии в экспорт не включаются.</p><div class="actions">${button("Экспорт JSON","export-json","download","")}${button("Участники CSV","export-csv","download","")}${button("Восстановить из JSON","import","shield","")}</div><p class="hint">Восстановление полностью заменит данные мероприятия. Сначала сохраните текущий экспорт. Для полного резервирования базы используйте scripts/backup.bat.</p></div></section>`:'<div class="notice">Экспорт персональных данных и восстановление доступны администратору.</div>'}`;
}
const actionNames={login:"Вход",logout:"Выход",create:"Создание",update:"Изменение",delete:"Удаление",register:"Запись на секцию",attendance_update:"Отметка посещения",unregister:"Отмена записи",badge_mark:"Выдача бейджа",badges_mark_all:"Массовая выдача",export:"Экспорт JSON",export_csv:"Экспорт CSV",import_replace:"Восстановление"};
function renderAudit() {
  $("#page-body").innerHTML=`<section class="panel"><div class="table-wrap"><table class="audit-table"><thead><tr><th>Время UTC</th><th>Пользователь</th><th>Действие</th><th>Объект</th></tr></thead><tbody>${state.audit.map(a=>`<tr><td>${esc(a.created_at)}</td><td>${esc(a.actor)}</td><td>${esc(actionNames[a.action]||a.action)}</td><td>${esc(a.entity)} ${a.entity_id??""}</td></tr>`).join("")}</tbody></table></div></section>`;
}
function modal(title,body,onSubmit,saveLabel="Сохранить") {
  const el=$("#modal");el.innerHTML=`<div class="modal-head"><h2 id="modal-title">${esc(title)}</h2><button class="icon-btn" data-action="close" aria-label="Закрыть">${icon("close")}</button></div><form id="modal-form">${body}<div id="modal-error" class="error modal-error" role="alert"></div><div class="modal-actions"><button type="button" class="btn" data-action="close">Отмена</button><button type="submit" class="btn primary">${saveLabel}</button></div></form>`;
  el.showModal();
  $("#modal-form").addEventListener("submit",async e=>{
    e.preventDefault();const form=e.currentTarget,btn=$("button[type=submit]",form);btn.disabled=true;
    try { await onSubmit(Object.fromEntries(new FormData(form)));el.close();await refresh();toast("Изменения сохранены"); }
    catch(err){if($("#modal-error"))$("#modal-error").textContent=err.message;}
    finally{btn.disabled=false;}
  });
}
function participantForm(id) {
  const p=state.participants.find(x=>x.id===Number(id))||{};
  modal(id?"Редактирование участника":"Новый участник",`<div class="form-grid">${[["lastName","Фамилия",80],["firstName","Имя",80],["organization","Организация",160],["email","Email",254]].map(([key,label,max])=>`<label class="field">${label}<input name="${key}" type="${key==="email"?"email":"text"}" value="${esc(p[key]||"")}" maxlength="${max}" ${key!=="organization"?"required":""}></label>`).join("")}<label class="field span-two">Роль<select name="role">${["слушатель","докладчик","организатор"].map(r=>`<option ${p.role===r?"selected":""}>${r}</option>`).join("")}</select></label></div>`, data=>api(id?`/participants/${id}`:"/participants",id?"PUT":"POST",data));
}
function sectionForm(id) {
  const s=state.sections.find(x=>x.id===Number(id))||{};
  modal(id?"Редактирование секции":"Новая секция",`<div class="form-grid"><label class="field span-two">Название<input name="title" maxlength="160" required value="${esc(s.title||"")}"></label><label class="field span-two">Аудитория<input name="room" maxlength="80" value="${esc(s.room||"")}"></label><label class="field">Время начала<input type="time" name="startTime" value="${esc(s.startTime||"")}"></label><label class="field">Вместимость<input type="number" name="capacity" min="1" max="10000" required value="${s.capacity||20}"></label></div>`,data=>api(id?`/sections/${id}`:"/sections",id?"PUT":"POST",{...data,capacity:Number(data.capacity)}));
}
function attendanceForm(sid) {
  if(!state.participants.length||!state.sections.length){toast("Сначала добавьте участника и секцию");return;}
  modal("Запись на секцию",`<label class="field">Участник<select name="participantId" required><option value="">Выберите участника</option>${state.participants.map(p=>`<option value="${p.id}">${esc(p.lastName)} ${esc(p.firstName)} · ${esc(p.email)}</option>`).join("")}</select></label><label class="field">Секция<select name="sectionId" required><option value="">Выберите секцию</option>${state.sections.map(s=>`<option value="${s.id}" ${s.registered>=s.capacity?"disabled":""} ${s.id==sid?"selected":""}>${esc(s.title)} · свободно ${s.capacity-s.registered}</option>`).join("")}</select></label>`,data=>api("/attendance","POST",{participantId:Number(data.participantId),sectionId:Number(data.sectionId)}),"Записать");
}
function confirmDelete(title,description,path) { modal(title,`<p>${esc(description)}</p>`,()=>api(path,"DELETE"),"Удалить"); }
async function download(kind) {
  const response=await fetch(`/api/export${kind==="csv"?"/csv":""}`,{credentials:"same-origin"});
  if(!response.ok)throw new Error("Экспорт недоступен. Проверьте сессию и права.");
  const url=URL.createObjectURL(await response.blob());const a=document.createElement("a");a.href=url;a.download=kind==="csv"?"participants.csv":"conference-export.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast("Экспорт подготовлен");
}
function importForm() {
  modal("Восстановление данных",`<p class="modal-help">Будут заменены все участники, секции и записи посещений. Сначала сохраните текущий экспорт.</p><label class="field">Экспорт JSON до 10 МБ<input type="file" id="import-file" accept=".json,application/json" required></label><label class="field">Введите ЗАМЕНИТЬ для подтверждения<input name="confirmation" required autocomplete="off" placeholder="ЗАМЕНИТЬ"></label>`,async data=>{
    if(data.confirmation!=="ЗАМЕНИТЬ")throw new Error("Введите слово ЗАМЕНИТЬ без пробелов");
    const file=$("#import-file").files[0];if(!file||file.size>10*1024*1024)throw new Error("Выберите JSON-файл размером до 10 МБ");
    let bundle;try{bundle=JSON.parse(await file.text());}catch{throw new Error("Не удалось прочитать JSON. Файл не изменён.");}
    if(!bundle||typeof bundle!=="object"||Array.isArray(bundle))throw new Error("Неверный формат экспорта");
    await api("/import","POST",{...bundle,confirm:"REPLACE"});
  },"Заменить данные");
}
document.addEventListener("click",async e=>{
  const btn=e.target.closest("[data-action]");if(!btn||btn.disabled)return;
  const {action,id,pid,sid,value}=btn.dataset;
  try {
    if(action==="menu"){const opened=$(".app").classList.toggle("menu-open");btn.setAttribute("aria-expanded",opened);return;}
    if(action==="close"){$("#modal").close();return;}
    if(action==="new-participant"||action==="edit-participant"){participantForm(id);return;}
    if(action==="new-section"||action==="edit-section"){sectionForm(id);return;}
    if(action==="new-attendance"){attendanceForm(id);return;}
    if(action==="delete-participant"){confirmDelete("Удалить участника?","Связанные регистрации на секции также будут удалены.",`/participants/${id}`);return;}
    if(action==="delete-section"){confirmDelete("Удалить секцию?","Все записи участников на эту секцию будут удалены.",`/sections/${id}`);return;}
    if(action==="delete-attendance"){confirmDelete("Отменить запись?","Участник останется в общем списке конференции.",`/attendance/${pid}/${sid}`);return;}
    if(action==="import"){importForm();return;}
    if(action==="print-one"||action==="print-all") {
      const people=action==="print-one"?state.participants.filter(p=>p.id===Number(id)):state.participants;
      if(!people.length){toast("Нет бейджей для печати");return;}
      $("#print-area").innerHTML=people.map(badgeMarkup).join("");window.print();return;
    }
    btn.disabled=true;
    if(action==="export-json"||action==="export-csv"){await download(action==="export-csv"?"csv":"json");return;}
    if(action==="logout"){await api("/auth/logout","POST");state.user=null;state.csrf="";showLogin();return;}
    if(action==="toggle-attendance")await api(`/attendance/${pid}/${sid}`,"PUT",{attended:value==="true"});
    if(action==="toggle-badge"){const p=state.participants.find(x=>x.id===Number(id));await api(`/participants/${id}`,"PUT",{badgePrinted:!p.badgePrinted});}
    await refresh();toast("Изменения сохранены");
  }catch(err){toast(err.message);}finally{btn.disabled=false;}
});
window.addEventListener("hashchange",()=>{state.search="";state.filter="";state.page=1;if(state.user)renderShell();});
window.addEventListener("keydown",e=>{if(e.key==="Escape")$(".app")?.classList.remove("menu-open");});
async function init() {
  try {const health=await api("/health");state.demo=health.demo;}
  catch {showLogin("Сервер недоступен. Проверьте запуск и обновите страницу.");return;}
  try {const session=await api("/auth/me");state.user=session.user;state.csrf=session.csrfToken;await refresh();}
  catch {if(!state.user)showLogin();else showLogin("Не удалось загрузить данные. Попробуйте войти снова.");}
}
init();
