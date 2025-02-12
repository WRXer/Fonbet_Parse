import requests
import json


sent_events = {}    #Словарь для отслеживания отправленных событий

def fetch_and_display_line_events(file_name):
    """
    Находим и выводим события
    :return:
    """
    with open('sport_ids.json', 'r') as f:
        #sport_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
        sport_ids = json.load(f)
    sport_id = sport_ids.get(file_name)
    language = sport_id['language']
    sport_id = sport_id['sport_id']
    s = requests.Session()
    s.headers = {
        'Accept': 'application/json',
        'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    response = s.get(
        f'https://line52w.bk6bba-resources.com/events/list?lang={language}&version=36403772709&scopeMarket=1600'
    )
    data = response.json()
    events = data.get('events', [])    #Список событий
    custom_factors = data.get('customFactors', [])    #Список коэффициентов
    filtered_events = [
        event for event in events
        if event.get('place') == 'line' and
           event.get('sportId') == sport_id and
           event.get('level') == 1
    ]   #Фильтруем нужные нам события
    new_events = [
        event for event in filtered_events
        if event['id'] not in sent_events
    ]   #Добавляем новые события в отправленные, чтобы не повторялась отправка
    if new_events:
        matches_info = []
        message_matches = ""
        for event in new_events:
            team_1 = event.get('team1')
            team_2 = event.get('team2')

            event_factors = next((info for info in custom_factors if info.get('e') == event['id']), None)    #Поиск коэффициентов для данного события
            #flashscore_info = fonbet_line(team_1, team_2, file_name)
            if event_factors:
                factors = {factor['f']: (factor['v'], factor.get('pt', '')) for factor in
                           event_factors.get('factors', [])}
                p1, pt_p1 = factors.get(921, ("—", ""))    #П1
                x, pt_x = factors.get(922, ("—", ""))    #Х
                p2, pt_p2 = factors.get(923, ("—", ""))    #П2
                """Список нужных значений f"""
                target_fora_team1 = {910, 927, 989, 1569, 1672, 1677, 1680, 1683, 1686}
                target_fora_team2 = {912, 928, 991, 1572, 1675, 1678, 1681, 1684, 1687}
                """Ищем Фору среди нужных f, если pt = +1.5 или -1,5"""
                fplus15k1 = next((factor['v'] for factor in event_factors.get('factors', [])
                           if factor['f'] in target_fora_team1 and factor.get('pt') == "+1.5"), "—")
                fminus15k1 = next((factor['v'] for factor in event_factors.get('factors', [])
                              if factor['f'] in target_fora_team1 and factor.get('pt') == "-1.5"), "—")
                fplus15k2 = next((factor['v'] for factor in event_factors.get('factors', [])
                                  if factor['f'] in target_fora_team2 and factor.get('pt') == "+1.5"), "—")
                fminus15k2 = next((factor['v'] for factor in event_factors.get('factors', [])
                                   if factor['f'] in target_fora_team2 and factor.get('pt') == "-1.5"), "—")

                #if float(flashscore_info['k1']) + 0.15 < float(p1) or float(flashscore_info['k2']) + 0.15 < float(p2):
                     #team_1, float(flashscore_info['k1']) , p1, team_2, float(flashscore_info['k2']), p2

                match = {
                    "team_1": team_1,

                    "p1": p1,
                    "fplus15k1": fplus15k1,
                    "fminus15k1": fminus15k1,
                    "team_2": team_2,

                    "p2": p2,
                    "fplus15k2": fplus15k2,
                    "fminus15k2": fminus15k2,
                "x": x}
                matches_info.append(match)

        return matches_info
    else:
        return None