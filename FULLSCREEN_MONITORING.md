"""
Fullscreen Violation Detection Module for Test Taking Interface

Этот модуль помогает вам реализовать контроль полноэкранного режима в JavaScript фронтенде.

ИСПОЛЬЗОВАНИЕ В HTML/JAVASCRIPT:
================================

1. Инициализируйте монитор при загрузке теста:

    const testMonitor = new FullscreenViolationMonitor({
        testId: 1,
        resultId: 100,
        maxViolations: 3,
        apiBaseUrl: 'http://localhost:8000/api/v1'
    });

    testMonitor.start();


2. HTML код для теста:

    <div id="test-container" class="fullscreen-test">
        <div id="test-content">
            <!-- Содержимое теста -->
            <div class="question">
                <p>Вопрос 1: ...</p>
            </div>
        </div>
        <div id="violation-indicator" class="violation-indicator">
            Нарушений: <span id="violation-count">0</span> / 3
        </div>
    </div>

    <button onclick="enterFullscreen()">Начать тест (полный экран)</button>


3. JavaScript код:

    // Класс для мониторинга нарушений
    class FullscreenViolationMonitor {
        constructor(options) {
            this.testId = options.testId;
            this.resultId = options.resultId;
            this.maxViolations = options.maxViolations;
            this.apiBaseUrl = options.apiBaseUrl;
            this.violations = 0;
            this.isFullscreen = false;
        }

        start() {
            // Слушаем события изменения полноэкранного режима
            document.addEventListener('fullscreenchange', () => {
                this.isFullscreen = document.fullscreenElement !== null;
                if (!this.isFullscreen) {
                    this.recordViolation();
                }
            });

            // Слушаем попытку пользователя покинуть тест (Alt+Tab, и т.д.)
            document.addEventListener('visibilitychange', () => {
                if (document.hidden && this.isFullscreen) {
                    this.recordViolation();
                }
            });

            // Слушаем попытку использовать сочетания клавиш
            document.addEventListener('keydown', (e) => {
                if (this.isFullscreen) {
                    // Блокируем Esc для выхода из полного экрана
                    if (e.key === 'Escape') {
                        e.preventDefault();
                    }
                    // Блокируем Alt+Tab
                    if ((e.altKey || e.metaKey) && e.key === 'Tab') {
                        e.preventDefault();
                    }
                }
            });
        }

        recordViolation() {
            this.violations++;
            this.updateViolationIndicator();

            // Отправляем на сервер
            this.reportToServer();

            if (this.violations >= this.maxViolations) {
                this.failTest();
            }
        }

        async reportToServer() {
            try {
                const response = await fetch(
                    `${this.apiBaseUrl}/tests/${this.testId}/results/${this.resultId}/violation`,
                    { method: 'POST' }
                );
                
                if (response.status === 400) {
                    this.failTest();
                }
            } catch (error) {
                console.error('Error reporting violation:', error);
            }
        }

        updateViolationIndicator() {
            const indicator = document.getElementById('violation-count');
            if (indicator) {
                indicator.textContent = this.violations;
            }
        }

        failTest() {
            alert('Тест провален. Вы вышли из полноэкранного режима более ' + 
                  this.maxViolations + ' раз.');
            document.exitFullscreen();
            // Перенаправляем на результаты
            window.location.href = '/results';
        }
    }

    // Функция для входа в полный экран
    async function enterFullscreen() {
        const container = document.getElementById('test-container');
        
        try {
            await container.requestFullscreen();
            // После входа в полный экран - запускаем монитор
            testMonitor.start();
        } catch (error) {
            alert('Не удалось перейти в полноэкранный режим: ' + error);
        }
    }


СТРУКТУРА API ENDPOINTS:
========================

1. POST /api/v1/tests/{test_id}/start
   Начать тест
   Response: TestResultResponse (с result_id)

2. GET /api/v1/tests/{test_id}/questions
   Получить вопросы теста

3. POST /api/v1/tests/{test_id}/results/{result_id}/answer
   Отправить ответ на вопрос
   Body: {
       "question_id": 1,
       "answer_text": "...",
       "answer_choice": "A"
   }

4. POST /api/v1/tests/{test_id}/results/{result_id}/violation
   Зафиксировать нарушение полноэкранного режима
   (вызывается автоматически от фронтенда)

5. POST /api/v1/tests/{test_id}/results/{result_id}/submit
   Завершить тест
   Response: TestResultResponse (с итоговым score и percentage)

6. GET /api/v1/tests/{test_id}/results/{result_id}
   Получить результаты теста


ПРИМЕЧАНИЯ:
===========
- Все timestamp хранятся в UTC
- По умолчанию тест недоступен вне временного окна (start_date, end_date)
- Каждое нарушение немедленно записывается в базу данных
- Если нарушений более max_fullscreen_violations, тест автоматически провалится
- Результат теста: percentage = (score / max_score) * 100

SECURITY:
=========
- Используйте JWT токены для аутентификации в реальном приложении
- Валидируйте ответы на сервере (не доверяйте клиенту)
- Проверяйте права доступа перед каждой операцией
"""

# Примечание: Фронтенд-код выше - это примеры для HTML/JavaScript приложения
# Для React.js или Vue.js нужна адаптация, но логика остаётся той же

