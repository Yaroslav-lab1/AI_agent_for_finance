# Легенда 2: AI-агент и импорт операций

## Роль

Участник отвечал за AI-часть проекта: пайплайн разбора банковских уведомлений, поддержку текста, CSV и изображений, structured output и проверку качества найденных операций.

## Что сделал

- Реализовал `AgentPipeline`, который объединяет все этапы AI-импорта.
- Добавил `TextInputTool` для нормализации текстовых уведомлений.
- Добавил `CsvInputTool` для чтения CSV-файлов и приведения строк к единому текстовому формату.
- Добавил `ImageOcrTool` для обработки PNG/JPEG/WebP через Pillow, pytesseract и Tesseract OCR.
- Подключил LLM-клиенты: `MockLLMClient`, `OllamaLLMClient`, `OpenAICompatibleLLMClient`.
- Настроил JSON Schema для structured output, чтобы модель возвращала машинно читаемый список операций.
- Реализовал нормализацию суммы и даты после LLM.
- Добавил определение типа операции, классификацию категории и проверку дублей.
- Сохранял ход работы агента в `agent_audit_logs`.

## Что может рассказать на защите

AI-агент работает не как "магическая запись в базу", а как контролируемый пайплайн. Разные источники сначала приводятся к единому тексту, затем LLM возвращает JSON по схеме, а backend дополнительно нормализует и проверяет результат. Пользователь остается финальной точкой контроля.

## Какие файлы знает

- `backend/app/agent/pipeline.py`
- `backend/app/agent/llm_client.py`
- `backend/app/agent/schemas.py`
- `backend/app/agent/tools/text_input.py`
- `backend/app/agent/tools/csv_input.py`
- `backend/app/agent/tools/image_ocr.py`
- `backend/app/agent/tools/normalization.py`
- `backend/app/agent/tools/categorization.py`
- `backend/app/agent/tools/duplicate_detection.py`

## Ответственность за качество

Проверял, что текст, CSV и OCR-текст проходят через общий пайплайн, что LLM-ответ валидируется, а ошибочные или подозрительные результаты не попадают в финальные операции без подтверждения пользователя.
