# conference

# Система регистрации участников конференции

> Учебная практика ПМ.02, раздел 3.3 «Осуществление интеграции программных модулей»  
> Тема №50: *Система регистрации участников конференции*
<img width="1920" height="995" alt="{066C842D-A426-4E03-832F-C0C321134BA2}" src="https://github.com/user-attachments/assets/fe056a94-5bcb-40dc-80cd-a202d09ea4db" />

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Лицензия](https://img.shields.io/badge/Лицензия-MIT-green)](LICENSE)

---

##  О проекте

Веб-приложение для автоматизации управления участниками конференции: регистрация, распределение по секциям, учёт посещения, генерация бейджей и формирование аналитических отчётов.

**Стек:** Python · FastAPI · Pydantic · Uvicorn · HTML/CSS/JavaScript · JSON-хранилище

---

##  Функциональность

| Модуль | Возможности |
|---|---|
|  **Участники** | Регистрация, поиск, фильтрация по роли, удаление |
|  **Секции** | Создание секций с залом, временем и вместимостью |
|  **Посещение** | Запись участников на секции, отметка присутствия / отсутствия |
|  **Бейджи** | Генерация и печать именных бейджей |
|  **Отчёты** | Статистика, графики заполненности, экспорт в TXT |
|  **Дашборд** | Сводка показателей в реальном времени |

---

##  Архитектура

```
conference-app/
├── main.py               # FastAPI бэкенд — все эндпоинты и модели данных
├── data/                 # JSON-хранилище (создаётся автоматически)
│   ├── participants.json
│   ├── sections.json
│   └── attendance.json
├── static/
│   ├── index.html        # Дашборд
│   ├── participants.html # Управление участниками
│   ├── sections.html     # Управление секциями
│   ├── attendance.html   # Учёт посещения
│   ├── badges.html       # Бейджи
│   ├── reports.html      # Отчёты и аналитика
│   ├── css/
│   │   ├── main.css      # Основные стили
│   │   └── components.css
│   └── js/
│       ├── api.js        # REST API-клиент + утилиты
│       ├── app.js        # Глобальные утилиты
│       ├── participants.js
│       ├── sections.js
│       ├── attendance.js
│       ├── badges.js
│       └── reports.js
```

---

##  REST API

| Метод | Эндпоинт | Описание |
|---|---|---|
| `GET` | `/api/participants` | Список участников (с поиском) |
| `POST` | `/api/participants` | Регистрация участника |
| `DELETE` | `/api/participants/{id}` | Удаление участника |
| `GET` | `/api/sections` | Список секций |
| `POST` | `/api/sections` | Создание секции |
| `DELETE` | `/api/sections/{id}` | Удаление секции |
| `GET` | `/api/attendance` | Записи о посещении |
| `POST` | `/api/attendance` | Запись участника на секцию |
| `PUT` | `/api/attendance/{pid}/{sid}` | Отметить присутствие |
| `POST` | `/api/badges/{id}/print` | Печать бейджа |
| `POST` | `/api/badges/print-all` | Печать всех бейджей |
| `GET` | `/api/stats` | Сводная статистика |
| `GET` | `/api/export` | Экспорт данных в JSON |
| `POST` | `/api/import` | Импорт / сброс данных |

Интерактивная документация доступна по адресу **`/docs`** (Swagger UI).

---

##  Запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/<username>/conference-app.git
cd conference-app
```

### 2. Установить зависимости

```bash
pip install fastapi uvicorn[standard] pydantic[email]
```

### 3. Запустить сервер

```bash
uvicorn main:app --reload
```

Приложение будет доступно по адресу: **`http://localhost:8000`**

---

##  Модели данных

```python
class Participant(BaseModel):
    id: Optional[int]
    lastName: str
    firstName: str
    organization: str = ""
    email: EmailStr
    role: str  # докладчик | слушатель | организатор
    badgePrinted: bool = False
    createdAt: Optional[str]

class Section(BaseModel):
    id: Optional[int]
    title: str
    room: str = ""
    startTime: str = ""
    capacity: int
    createdAt: Optional[str]

class Attendance(BaseModel):
    id: Optional[int]
    participantId: int
    sectionId: int
    status: str = "зарегистрирован"  # зарегистрирован | присутствовал | отсутствовал
    registeredAt: Optional[str]
    updatedAt: Optional[str]
```

---

##  Валидация и обработка ошибок

- Валидация данных через **Pydantic** (тип роли, формат email, минимальная длина полей)
- Проверка уникальности email при регистрации → **HTTP 409**
- Проверка вместимости секции при записи → **HTTP 400**
- **HTTP 404** при обращении к несуществующим сущностям
- Защита от деления на ноль при расчёте посещаемости
- Обработка `JSONDecodeError` при чтении файлов хранилища

---

##  Тестирование

Тестирование проводилось через **Postman** (коллекция из 12 запросов) и ручным прохождением 15 тест-кейсов.

| Сценарий | Результат |
|---|---|
| Регистрация участника с валидными данными | ✅ Пройден |
| Регистрация с дублирующимся email | ✅ Пройден |
| Регистрация с недопустимой ролью | ✅ Пройден |
| Поиск участника по имени | ✅ Пройден |
| Создание и удаление секции | ✅ Пройден |
| Запись участника на секцию | ✅ Пройден |
| Повторная запись на одну секцию | ✅ Пройден |
| Отметка присутствия / отсутствия | ✅ Пройден |
| Запись сверх вместимости секции | ✅ Пройден |
| Печать бейджа / массовая печать | ✅ Пройден |
| Формирование отчёта и экспорт | ✅ Пройден |
| Сброс всех данных через импорт | ✅ Пройден |

---

##  Профессиональные компетенции

Проект подтверждает освоение компетенций ПМ.02:

| Компетенция | Как подтверждается в проекте |
|---|---|
| **ПК 2.1** | Разработаны требования к 6 программным модулям на основе ТЗ и анализа предметной области |
| **ПК 2.2** | Реализована интеграция frontend и backend через REST API; модули собраны в единое приложение |
| **ПК 2.3** | Выполнена отладка с помощью Uvicorn-логов и DevTools, исправлены 4 критических дефекта |
| **ПК 2.4** | Разработано 15 тест-кейсов, проведено тестирование через Postman, зафиксированы дефекты |
| **ПК 2.5** | Проведена инспекция кода по чек-листу, применены ruff и flake8, код приведён к единому стилю |

---

##  Работа проекта
<img width="1920" height="995" alt="{066C842D-A426-4E03-832F-C0C321134BA2}" src="https://github.com/user-attachments/assets/6231ad04-1f90-4510-8a28-b50b683b8d14" />

<img width="1920" height="992" alt="{9DB53094-E736-4952-B313-99A1AA582113}" src="https://github.com/user-attachments/assets/a00b3de0-ad34-47c6-8c57-b7ab7750dce7" />

<img width="1920" height="992" alt="{93AF5FB0-8A43-4DE6-B56C-7DCD654E0FC0}" src="https://github.com/user-attachments/assets/381e1540-e5ac-46df-aafb-70e5597fc239" />

<img width="1920" height="992" alt="{A09199B5-5900-4C2C-AF0B-1A46141F88D9}" src="https://github.com/user-attachments/assets/073f715c-598c-40d4-a0ab-1fe5737aa6dd" />

<img width="1920" height="987" alt="{D6C9FD7D-3095-450E-906A-15B17DBA8119}" src="https://github.com/user-attachments/assets/f5f51881-c530-49e3-af16-6a5a8670a601" />

<img width="1920" height="991" alt="{F90EA47A-2E93-4275-B4F5-1B8A72C37EF3}" src="https://github.com/user-attachments/assets/a700b36c-55b1-4052-9d46-ba9bfcef189b" />

<img width="1920" height="991" alt="{CF03E3A0-5C84-4445-8D54-0C2E6D37A2D2}" src="https://github.com/user-attachments/assets/1c13ff72-2041-4b5f-8a87-549a20375376" />

<img width="1920" height="990" alt="{930B0717-81B3-4221-AA5D-9B681366331B}" src="https://github.com/user-attachments/assets/ca36cc53-ba81-40fa-963c-92820ea3a522" />

<img width="1919" height="990" alt="{BEE6D6E1-A86C-4A3D-9CF2-0B61938AAB8B}" src="https://github.com/user-attachments/assets/15bba049-77d4-4737-b4a2-afab2c73a956" />

<img width="1920" height="989" alt="{6AFD1A48-6B4F-47EB-9B1F-2B8E718A16EF}" src="https://github.com/user-attachments/assets/c46bbd22-a6fe-4c0e-8c2d-0a691bb47fc3" />

<img width="1920" height="990" alt="{0FAE9636-434C-4BDD-8457-95C87AD366C2}" src="https://github.com/user-attachments/assets/cb5675ee-81cb-40b8-9e7c-cbe54ea37c73" />

<img width="443" height="111" alt="{9608F7F6-1B66-4224-AADD-FBE43EA4F9B3}" src="https://github.com/user-attachments/assets/11968adb-e77a-4bb4-b7ef-4a49fc27d0ea" />

<img width="444" height="101" alt="{6DC9A59B-9C46-4B22-BC3E-0FCDD75C3527}" src="https://github.com/user-attachments/assets/4fd91e80-0a85-4253-ad21-f211e64373d8" />

<img width="697" height="157" alt="{16058D9C-DEC3-4644-9CE4-D961AAE6BE01}" src="https://github.com/user-attachments/assets/bcd6f0a8-c70e-4524-b887-5a9a0ef8f22c" />













