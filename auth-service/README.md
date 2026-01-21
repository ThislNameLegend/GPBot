# Auth Service (C++)

Модуль авторизации для приложения тестирования и опросов.

## Запуск

### Сборка через CMake
```
mkdir build && cd build
cmake .. && make
./auth_service
```

### Через Docker
```
docker build -t auth-service .
docker run -p 8081:8081 auth-service
```

## API
- `GET /auth/validate?token=<token>` — проверка токена
- `POST /auth/login` — заглушка логина
- `GET /health` — health check

Порт: 8081
