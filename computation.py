import pandas as pd
import os
import difflib
import logging
import numpy as np
from scipy.stats import nbinom


BASE_DIR = os.path.dirname(os.path.abspath(__file__))    #Папка scripts
PROJECT_ROOT = os.path.dirname(BASE_DIR)    #Папка flashscore
FONBET_PARSE_DIR = os.path.join(PROJECT_ROOT, 'Fonbet_Parse')
DATA_DIR = os.path.join(FONBET_PARSE_DIR, 'data')    #Папка data


def load_excel_file(file_path):
    """
    Загрузка таблицы
    :param file_path:
    :return:
    """
    try:
        return pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
    except Exception as e:
        logging.error("Ошибка", f"Не удалось загрузить файл: {e}")
        return None

def calculate_averages(team_data, home_data, away_data):
    """
    Среднее количество забитых и пропущенных голов команды
    :param team_data:
    :param home_data:
    :param away_data:
    :return:
    """
    try:
        total_matches = team_data['Матчей сыграно']
        home_matches = home_data['Матчей сыграно']
        away_matches = away_data['Матчей сыграно']

        avg_scored = (
                home_data['Забитые голы'] / home_matches * 0.4 +
                away_data['Забитые голы'] / away_matches * 0.4 +
                team_data['Забитые голы'] / total_matches * 0.2
        )

        avg_conceded = (
                home_data['Пропущенные голы'] / home_matches * 0.4 +
                away_data['Пропущенные голы'] / away_matches * 0.4 +
                team_data['Пропущенные голы'] / total_matches * 0.2
        )

        return avg_scored, avg_conceded
    except:
        return 0.0, 0.0

def negative_binomial(mean, dispersion=1.2):
    """
    Моделирование количества событий (например, голов в хоккее), когда вероятность успеха изменяется
    :param mean:
    :param dispersion:
    :return:
    """
    p = 1 / (1 + mean / dispersion)
    n = mean * p / (1 - p)
    return nbinom(n, p)

def simulate_matches(home_avg, away_avg, simulations=100000):
    """
    Симуляция матчей
    :param home_avg:
    :param away_avg:
    :param simulations:
    :return:
    """
    try:
        home_dist = negative_binomial(home_avg[0])
        away_dist = negative_binomial(away_avg[0])

        home_goals = home_dist.rvs(simulations)
        away_goals = away_dist.rvs(simulations)

        total_goals = home_goals + away_goals
        diff_goals = home_goals - away_goals

        home_win = np.mean(home_goals > away_goals)     #Расчет основных исходов
        away_win = np.mean(away_goals > home_goals)
        draw = np.mean(home_goals == away_goals)    #Ограничение котировки на ничью

        results = {
            "П1": home_win,
            "П2": away_win,
            "Ничья": draw,

            #Форы
            "Хозяева -1.5": np.mean(diff_goals > 1.5),
            "Хозяева +1.5": np.mean(diff_goals >= -1.5),
            "Гости -1.5": np.mean(-diff_goals > 1.5),
            "Гости +1.5": np.mean(-diff_goals >= -1.5),

            #Общие тоталы
            **{f"Тотал {x} больше": np.mean(total_goals > x) for x in [4.5, 5.5, 6.5]},
            **{f"Тотал {x} меньше": np.mean(total_goals <= x) for x in [4.5, 5.5, 6.5]},

            #Индивидуальные тоталы
            **{f"Хозяева ИТБ {x}": np.mean(home_goals > x) for x in [1.5, 2.5, 3.5]},
            **{f"Хозяева ИТМ {x}": np.mean(home_goals <= x) for x in [1.5, 2.5, 3.5]},
            **{f"Гости ИТБ {x}": np.mean(away_goals > x) for x in [1.5, 2.5, 3.5]},
            **{f"Гости ИТМ {x}": np.mean(away_goals <= x) for x in [1.5, 2.5, 3.5]}
        }
        return {k: v for k, v in results.items() if v > 0}
    except Exception as e:
        logging.error(f"Ошибка симуляции: {e}")
        print(f"Ошибка симуляции: {e}")
        return {}

def get_team_data(team_name, league_data):
    """
    Поиск в таблицах нужных команд
    :param team_name:
    :return:
    """
    sheets = {
        "total": "Общие матчи (Все матчи)",
        "home": "Домашние матчи (Все матчи)",
        "away": "Гостевые матчи (Все матчи)"
    }
    data = {}
    for key, sheet in sheets.items():
        df = league_data.get(sheet)    #Безопасно получаем DataFrame
        if df is not None and "Команда" in df.columns:    #Ищем самую похожую команду (если точного совпадения нет)
            team_list = df["Команда"].dropna().tolist()    #Убираем NaN и берём список команд
            best_match = difflib.get_close_matches(team_name, team_list, n=1, cutoff=0.5)

            if best_match:
                team_row = df[df["Команда"] == best_match[0]]
                data[key] = team_row.iloc[0] if not team_row.empty else None
            else:
                data[key] = None
        else:
            data[key] = None    #Если таблицы нет, ставим None
    return data

def fonbet_line(team_1, team_2, file_name):
    """
    Выборка от фонбет по линии
    Сюда приходит 2 команды, выведенные в матчах по линии, рассчитываются кф от флешскор и добавляются в словарь
    :return:
    """
    try:
        data_dir = os.path.join(DATA_DIR)
        file_path = os.path.join(data_dir, file_name)

        data = load_excel_file(file_path)
        league_data = data
        home_team = team_1
        away_team = team_2
        home_data = get_team_data(home_team, league_data)       #КОМАНДА 1
        away_data = get_team_data(away_team, league_data)    #КОМАНДА 2
        home_avg = calculate_averages(home_data["total"], home_data["home"], home_data["away"])
        away_avg = calculate_averages(away_data["total"], away_data["away"], away_data["home"])
        results = simulate_matches(home_avg, away_avg)
        new_results = {}
        for i, outcome in enumerate(["П1", "П2", "Ничья"], start=1):    #Преобразуем ключи и рассчитываем кэфы
            outcome_key = f"k{i}"   #k1, k2, k3 - ничья
            prob = results.get(outcome, 0)    #Получаем вероятность для текущего исхода
            odds = 1 / prob if prob > 0 else 0    #Вычисляем кэф (ставочный коэффициент)
            new_results[outcome_key] =f"{odds:.2f}"    #Записываем кэф в новый словарь
        return new_results

    except Exception as e:
        logging.error("Ошибка", str(e))
        print("Ошибка", str(e))


def merge_excel_files(file_1, file_2, out_file):
    """
    Объединяет два Excel-файла, суммируя числовые значения.
    :param file1: Путь к первому файлу
    :param file2: Путь ко второму файлу
    :param output_file: Путь для сохранения объединённого файла
    """
    data_dir = os.path.join(DATA_DIR)
    file1 = os.path.join(data_dir, file_1)
    file2 = os.path.join(data_dir, file_2)
    output_file = os.path.join(data_dir, out_file)

    df1 = pd.read_excel(file1, sheet_name=None)    #Все листы из первого файла
    df2 = pd.read_excel(file2, sheet_name=None)    #Все листы из второго файла

    merged_data = {}

    """Обрабатываем каждый лист в обоих файлах"""
    for sheet in df1.keys():
        if sheet in df2:
            df1_sheet = df1[sheet]
            df2_sheet = df2[sheet]
            df_combined = pd.concat([df1_sheet, df2_sheet])    #Объединяем данные по названию команды и суммируем числовые значения
            df_sum = df_combined.groupby('Команда', as_index=False).sum(numeric_only=True)    #Группируем по команде и суммируем числовые данные
            merged_data[sheet] = df_sum
        else:
            merged_data[sheet] = df1[sheet]    #Если листа нет во втором файле, добавляем из первого

    with pd.ExcelWriter(output_file) as writer:    #Сохраняем результат в новый файл
        for sheet_name, df in merged_data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    if file1 != output_file:
        os.remove(file1)
    os.remove(file2)

