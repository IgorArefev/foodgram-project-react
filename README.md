## Проект [Foodgram](https://djifrost.sytes.net)

![foodgram](https://github.com/IgorArefev/foodgram-project-react/actions/workflows/main.yml/badge.svg?branch=master)

Foodgram - продуктовый помощник с базой кулинарных рецептов.

[Документация к API](https://djifrost.sytes.net/api/docs/)

[Админка](https://djifrost.sytes.net/admin/) -- User: admin Pass: AdminAdmin

### Стек технологий:
- Python 3
- Django
- DRF
- PostgreSQL
- Docker
- Gunicorn
- Nginx

### Шаблон наполнения .env
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=
POSTGRES_USER=
POSTGRES_PASSWORD=
DB_HOST=
DB_PORT=
```

## КАК ЗАПУСТИТЬ ПРОЕКТ:
Для автоматизации развертывания ПО на боевых серверах используется среда виртуализации Docker, а также Docker-compose - инструмент для запуска многоконтейнерных приложений. Docker позволяет «упаковать» приложение со всем его окружением и зависимостями в контейнер, который может быть перенесён на любую Linux -систему, а также предоставляет среду по управлению контейнерами. Таким образом, для разворачивания серверного ПО достаточно чтобы на сервере с ОС семейства Linux были установлены среда Docker и инструмент Docker-compose.
```
sudo apt install docker.io
```
```
sudo apt install docker-compose
```

Так же необходимо установить PostgreSQL
```
sudo apt install postgresql postgresql-contrib -y
```

### Описание команд:
Скопировать на сервер файлы docker-compose.yml, nginx.conf из папки infra (команды выполнять находясь в папке infra):
```
scp docker-compose.yml nginx.conf username@IP:/home/username/
```
где **username** - имя пользователя на сервере, **IP** - публичный IP сервера

Для запуска проекта находясь в директории с ```docker-compose.yaml``` выполняем:
```
sudo docker-compose up -d --build 
```

После сборки контейнеров:
```
sudo docker-compose exec backend python manage.py makemigrations
```
```
sudo docker-compose exec backend python manage.py migrate
```
```
sudo docker-compose exec backend python manage.py createsuperuser
```
```
sudo docker-compose exec backend python manage.py collectstatic --no-input
```

### Команда для заполнения базы данными:

```
sudo docker-compose exec backend python manage.py import_csv
```


Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:
```
DOCKER_PASSWORD         # пароль от Docker Hub
DOCKER_USERNAME         # логин Docker Hub
HOST                    # публичный IP сервера
USER                    # имя пользователя на сервере
PASSPHRASE              # *если ssh-ключ защищен паролем
SSH_KEY                 # приватный ssh-ключ
TELEGRAM_TO             # ID телеграм-аккаунта для посылки сообщения
TELEGRAM_TOKEN          # токен бота, посылающего сообщение

DB_ENGINE               # django.db.backends.postgresql
DB_NAME                  
POSTGRES_USER            
POSTGRES_PASSWORD        
DB_HOST                  
DB_PORT                 
```

Для остановки контейнеров Docker:
```
sudo docker compose down -v      # с их удалением
sudo docker compose stop         # без удаления
```
