# Foobar

`vasiniyo-chat-bot` - телеграм бот, написанный на `pyTelegramBotAPI`

## Установка
Установите Docker для своей система: https://docs.docker.com/get-started/get-docker/<br>
Получите последний образ:

```bash
    docker pull ghcr.io/vasiniyo/vasiniyo-bot:latest
```

Также вы можете собрать образ из исходников:<br>
Скачайте репозиторий<br>
Сделать это можно, например, вот так:
```bash
  `git clone git@github.com:Vasiniyo/vasiniyo-chat-bot.git`
```
```bash
  `git clone https://github.com/Vasiniyo/vasiniyo-chat-bot.git`
```
Перейдите в директорию с ботом и пропишите команду
```bash
  docker build -t "vasiniyo-bot" --no-cache .
```
После этого создастся образ с именем `vasiniyo-bot`, который можно будет использовать, чтобы поднять контейнер


## Использование
Для использования бота необходимо получить токен (`BOT_API_TOKEN`)<br>
Для его получения можно перейти в следующего бота: https://t.me/BotFather<br>
`/start`<br>
`/newbot`<br>
`Вводим имя вашего бота`<br>
После этого создастся бот, и вам напишут его токен, который нужно скопировать в переменную окружения `BOT_API_TOKEN`<br>
Чтобы бот мог правильно работать в чате, ему необходимо выдать права администратора.

Чтобы узнать ID комнаты, в котором вы хотите пользоваться ботом, можно воспользоваться следующим ботом: https://t.me/FIND_MY_ID_BOT<br>
Пригласите его в чат и напишите команду `/id@FIND_MY_ID_BOT`<br>
Вставьте этот ID в переменную окружения `ACCESS_ID_GROUP`

Поднять контейнер можно при помощи следующей команды:

```bash
    docker run --env BOT_API_TOKEN="YOUR_API_TOKEN"\
               --env ACCESS_ID_GROUP="YOUR_ACCESS_ID"\
               ghcr.io/vasiniyo/vasiniyo-bot:latest
```
Вы прекрасны, бот успешно работает


## Содействие

Вы можете внести свой вклад в бота. Для этого можете открыть имеющиеся `issues`,
либо придумывать свои и отправлять`Pull Request`с соответствующими изменениями.
Обязательно создавайте новый issue, если вы обнаружили баг, либо у вас есть крутые идеи
