# UfaFlow

UfaFlow — лёгкий L4 (TCP) / базовый L7 (через TCP) балансировщик на Python.

Цели проекта:
- Быстрая итерация: MVP TCP-прокси с round-robin / least-connections.
- Модульность: легко добавить L7‑логики, TLS, метрики и admin API.
- Поддержка высокой производительности: uvloop + multi-process (далее).

Quickstart (локально)
1. Создайте виртуальное окружение и установите зависимости:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Запустите простые HTTP backend'ы:
   ```
   python -m http.server 8001 &
   python -m http.server 8002 &
   ```

3. Отредактируйте `config.yaml` при необходимости и запустите UfaFlow:
   ```
   python lb.py config.yaml
   ```

4. Проверьте:
   ```
   curl http://localhost:8080/
   ```

Структура репозитория
- lb.py — основной MVP-скрипт для проксирования TCP.
- config.yaml — пример конфигурации frontends/backends.
- requirements.txt — зависимости.
- README.md, LICENSE, .gitignore

Дальше (планы)
- Добавить multi-process с SO_REUSEPORT и systemd/docker unit.
- Перейти к L7 (HTTP parsing, keep-alive, connection pooling).
- TLS termination/SNI, admin API, Prometheus метрики.

Контрибуция
- Открытые PR и issues приветствуются. Пожалуйста, добавляйте тесты и краткое описание изменений.