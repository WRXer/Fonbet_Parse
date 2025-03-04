# Анализатор матчей

Для расчета возможных вероятностей в хоккейных матчах со сравнением с fonbet.
Сделано на базе графической библиотеки Tk.

У Вас имеется возможность парсить данные с flashscore, дополнительно сравнивать коэффициенты с БК Fonbet.

##ЗАПУСК ПРИЛОЖЕНИЯ.

Склонировать себе репозиторий

Установить зависимости pip install -r requirements.txt

Создать .env файл, в нем прописать все свои данные, что есть в .env_ex

Запустить сервер python sim.py


![Screenshot 2025-03-04 124723](https://github.com/user-attachments/assets/e1ea08d0-fbe8-4c02-9782-b88a62363b1c)

Для начала работы, требуется внести данные лиги, для этого нажмите "Добавить лигу"

![Screenshot 2025-03-04 124745](https://github.com/user-attachments/assets/546e5c9d-5e48-4985-8689-25da655e6964)

1 строка: Введите название лиги на латинице

2 строка: Потребуется выбрать язык ru/en для более простого поиска платформе. "Ру" выбирать только для русских, белорусских лиг! 

3 строка: Ссылка таблицы с flashscore. 

Откройте лигу на сайте flashscore как на скриншоте, нажмите таблица
![Screenshot 2025-03-04 125623](https://github.com/user-attachments/assets/9232e662-5938-45f0-890c-7bf12b46f593)

После у вас откроется окно, из него копируете ссылку и вставляете в данную строку
![Screenshot 2025-03-04 125650](https://github.com/user-attachments/assets/7f25bac9-e0c8-415b-ab12-97253ae9c24d)

4 строка: Ссылка с fonbet

Открываете лигу, либо матч , относящийся к нужной вам лиге, копируете ссылку и вставляете в данную строку
![Screenshot 2025-03-04 130014](https://github.com/user-attachments/assets/a949fa20-48da-428d-8984-b419e39fa5a3)

После всех манипуляций Сохранить лигу.


Далее кликаете обновить flashscore и ожидаете окно с уведомлением о завершении обновления 

![Screenshot 2025-03-04 130304](https://github.com/user-attachments/assets/63241ae7-d18e-4f38-9ae7-a8bc79f08b7d)

Теперь можно сравнивать с фонбет. Для этого вам нужно в верхней вкладке основной панели выбрать файл с нужной вам лигой и после кликаем "Свести Фонбет".

Также имеется ручная симуляция, в который вы сами можете подставить команды из выбранной лиги и сделать расчет вероятностей!


