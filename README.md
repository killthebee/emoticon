 Emoticon
---

Возвращает эмотиконы на запращиваемую стрингу





## Локальный запуск
Зупустите конейнеры 
```
docker-compose up -d --build
```
Зайдите в контейнер с бэкэндом:
```
docker-compose exec server bash
```
Запустите миграции:
```
alembic upgrade head
```


После чего запуститься бэк. 

Если отправить GET запрос с заголовком  ```"Authorization": f"Bearer {токен}"```по адрессу

http://127.0.0.1:80/api/fetch_emoticon/{стринга}

то ответ получите 301 ответ и PNG эмотикон соотвествующий этой стринге

Чтобы получить токен надо отправить POST запрос по ```/api/users/register_user/``` в дате запроса указать желаемый пароль
и логин. эндпоинт чтобы залогинеться с уже существующей учеткой и получить access_token тоже, кстати, реализован


## Python скрипт
Поскольку хороших способов проверять авторизация по токену без фронта придумать трудно, ниже есть питонячий скрипт 
который регестрирует юзера, получает токен, а затем получает эмотикон

```
import requests
import json


data = {
  "new_user": {
    "password": "tesatsatastsat",
    "username": "strinasdasfsfasfg"
  }
}

res = requests.post("http://127.0.0.1/api/users/register_user/", data=json.dumps(data))
headers = {
        "Authorization": f"Bearer {res['access_token']['access_token']}",
    }
res = requests.get("http://127.0.0.1/api/fetch_emoticon/kek", headers=headers)
print(res.text)
```