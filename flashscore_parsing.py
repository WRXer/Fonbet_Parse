import requests
import pandas as pd
import os, json
import logging
from project_logging import flashscore_logging
from concurrent.futures import ThreadPoolExecutor


BASE_DIR = os.path.dirname(os.path.abspath(__file__))    #Папка scripts
PROJECT_ROOT = os.path.dirname(BASE_DIR)    #Папка flashscore
FONBET_PARSE_DIR = os.path.join(PROJECT_ROOT, 'Fonbet_Parse')
DATA_DIR = os.path.join(FONBET_PARSE_DIR, 'data')    #Папка data
os.makedirs(DATA_DIR, exist_ok=True)    #Создаем папку data, если ее нет
flashscore_logging()    #Вызываем функцию для настройки логирования

headers = {
    "x-fsign": "SW9D1eZo",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def parse_matches(block):
    """
    Обработка блока данных о команде и выделение из него информации о матчах
    :param block:
    :return:
    """
    lines = block.strip().split('¬')
    matches = []
    current_match = {}
    for line in lines:
        if '÷' in line:
            key, value = line.split('÷', 1)
            if key == "~LMS":
                if current_match and "Домашняя_команда" in current_match and "Гостевая_команда" in current_match:
                    matches.append(current_match)
                current_match = {"Результат": value}
            elif key == "LMJ":
                current_match["Домашняя_команда"] = value
            elif key == "LMK":
                current_match["Гостевая_команда"] = value
            elif key == "LMF":
                current_match["Забитые_голы"] = value
            elif key == "LMG":
                current_match["Пропущенные_голы"] = value
            elif key == "LMU":
                current_match["Статус"] = value
    if current_match and "Домашняя_команда" in current_match and "Гостевая_команда" in current_match:
        matches.append(current_match)
    return matches

def parse_team_data_with_matches(block):
    """
    Обработка блока данных о команде и выделение из него информации о матчах
    :param block:
    :return:
    """
    lines = block.strip().split('¬')
    team_data = {}
    matches_block = []
    for line in lines:
        if '÷' in line:
            key, value = line.split('÷', 1)
            if key.startswith("~LM") or key in {"LMJ", "LMK", "LMF", "LMG", "LMU"}:
                matches_block.append(line)
            else:
                team_data[key] = value
    matches = parse_matches("¬".join(matches_block))
    team_data["Матчи"] = matches
    return team_data

def calculate_aggregates(matches, last_n=None):
    """
    Вычисление статистики по матчам
    :param matches:
    :param last_n:
    :return:
    """
    total_matches = 0
    total_scored = 0
    total_conceded = 0
    if last_n:
        matches = matches[-last_n:]
    for match in matches:
        if match.get("Результат") != "?":
            total_matches += 1
            total_scored += int(match.get("Забитые_голы", 0))
            total_conceded += int(match.get("Пропущенные_голы", 0))
    return {
        "Матчей сыграно": total_matches,
        "Забитые голы": total_scored,
        "Пропущенные голы": total_conceded
    }

def fetch_and_process_data(league, base_url):
    try:
        logging.info(f"Начинаю обработку данных для лиги: {league}")
        all_data = {}
        if league == 'KHL':
            MAX_TEAMS = 23  # Максимальное количество команд
        elif league == 'COHL':
            MAX_TEAMS = 20  # Максимальное количество команд
        elif league == 'NHL':
            MAX_TEAMS = 32
        elif league == 'WHL':
            MAX_TEAMS = 22
        else:
            MAX_TEAMS = 50  # Максимальное количество команд
        urls = {
            "Общие матчи": f"{base_url}_1",
            "Домашние матчи": f"{base_url}_2",
            "Гостевые матчи": f"{base_url}_3",
            "Последние 5 матчей": f"{base_url}_5",
            "Последние 5 матчей дома": f"{base_url}_8",
            "Последние 5 матчей на выезде": f"{base_url}_9"
        }
        for category, url in urls.items():     #Обработка всех матчей (используем данные из TG)
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.text
                blocks = data.split('~TR÷')[1:]
                all_teams = []
                team_count = 0    #Инициализация счетчика

                for block in blocks:
                    if team_count >= MAX_TEAMS:    #Проверка лимита
                        break
                    team_data = parse_team_data_with_matches(block)
                    if category in ["Последние 5 матчей", "Последние 5 матчей дома", "Последние 5 матчей на выезде"]:
                        if team_data.get("TM") == "5":
                            all_teams.append({
                                "Команда": team_data.get("TN"),
                                "ID команды": team_data.get("TI"),
                                "Лига": team_data.get("CTT"),
                                "Матчей сыграно": team_data.get("TM"),
                                "Побед": team_data.get("TW"),
                                "Побед в основное время": team_data.get("TWR"),
                                "Побед за пределами основного времени": team_data.get("TWA"),
                                "Поражений": team_data.get("TL"),
                                "Поражений в основное время": team_data.get("TLR"),
                                "Забитые голы": team_data.get("TG", "").split(":")[0],
                                "Пропущенные голы": team_data.get("TG", "").split(":")[1] if ":" in team_data.get("TG", "") else ""
                            })
                            team_count += 1
                    else:
                        all_teams.append({
                            "Команда": team_data.get("TN"),
                            "ID команды": team_data.get("TI"),
                            "Лига": team_data.get("CTT"),
                            "Матчей сыграно": team_data.get("TM"),
                            "Побед": team_data.get("TW"),
                            "Побед в основное время": team_data.get("TWR"),
                            "Побед за пределами основного времени": team_data.get("TWA"),
                            "Поражений": team_data.get("TL"),
                            "Поражений в основное время": team_data.get("TLR"),
                            "Забитые голы": team_data.get("TG", "").split(":")[0],
                            "Пропущенные голы": team_data.get("TG", "").split(":")[1] if ":" in team_data.get("TG", "") else ""
                        })
                        team_count += 1
                all_data[f"{category} (Все матчи)"] = pd.DataFrame(all_teams[:MAX_TEAMS])
            else:
                print(f"Ошибка для {category}: {response.status_code}")

        output_path = os.path.join(DATA_DIR, f"{league}_data.xlsx")    #Сохранение в Excel
        with pd.ExcelWriter(output_path) as writer:
            for sheet_name, df in all_data.items():
                sheet_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        logging.info(f"Данные успешно записаны в {output_path}")
        print(f"Данные успешно записаны в {output_path}")
    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        print(f"Произошла ошибка: {e}")

class ParseUpdater:
    """
    Параллельный парсинг
    """
    def __init__(self, max_threads):
        self.max_threads = max_threads

    def fetch_data_for_leagues(self, json_data):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            executor.map(lambda league_base_url: fetch_and_process_data(league_base_url[0], league_base_url[1]['flashscore_link']),
                         json_data.items())     #Параллельная обработка каждой лиги

def flashscore_parse():
    """
    Основная функция для запуска парсера
    """
    try:
        logging.info("Начинаю обработку лиг.")
        with open('league_data.json', 'r') as f:    #Загружаем JSON файл
            json_data = json.load(f)
        updater = ParseUpdater(max_threads=5)    #Создаем экземпляр ParseUpdater и запускаем обработку
        updater.fetch_data_for_leagues(json_data)
    except Exception as e:
        logging.error(f"Произошла ошибка в основной функции: {e}")



