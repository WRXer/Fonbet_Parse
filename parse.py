import requests


sent_events = {}    #Словарь для отслеживания отправленных событий


def fetch_and_display_events():
    """
    Находим и выводим события
    :return:
    """
    with open('sport_ids.txt', 'r') as f:
        sport_ids = [int(line.strip()) for line in f if line.strip().isdigit()]

    s = requests.Session()
    s.headers = {
        'Accept': 'application/json',
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }

    response = s.get(
        'https://line52w.bk6bba-resources.com/events/list?lang=ru&version=36403772709&scopeMarket=1600'
    )
    data = response.json()

    events = data.get('events', [])    #Список событий
    custom_factors = data.get('customFactors', [])    #Список коэффициентов

    filtered_events = [
        event for event in events
        if event.get('place') == 'live' and
           event.get('sportId') in sport_ids and
           event.get('level') == 1
    ]   #Фильтруем нужные нам события

    new_events = [
        event for event in filtered_events
        if event['id'] not in sent_events
    ]   #Добавляем новые события в отправленные, чтобы не повторялась отправка
    print(new_events)
    if new_events:
        message_matches = ""
        for event in new_events:
            event_name = f"{event.get('team1')} - {event.get('team2')}"
            event_factors = next((info for info in custom_factors if info.get('e') == event['id']), None)    #Поиск коэффициентов для данного события
            if event_factors:
                factors = {factor['f']: factor['v'] for factor in event_factors.get('factors', [])}
                p1 = factors.get(921, "—")  # П1
                x = factors.get(922, "—")  # Х
                p2 = factors.get(923, "—")  # П2
                message_matches += f"{event_name}: П1 {p1}  |  X {x}  |  П2 {p2}\n"


            sent_events[event['id']] = event  #Отмечаем событие как отправленное
        return message_matches
    else:
        return None