import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import difflib
import os
from scipy.stats import nbinom

from computation import load_excel_file, calculate_averages, simulate_matches
from flashscore_parsing import flashscore_parse
from fonbet_parsing import fetch_and_display_line_events

BASE_DIR = os.path.dirname(os.path.abspath(__file__))    #Папка scripts
PROJECT_ROOT = os.path.dirname(BASE_DIR)    #Папка flashscore
FONBET_PARSE_DIR = os.path.join(PROJECT_ROOT, 'Fonbet_Parse')
DATA_DIR = os.path.join(FONBET_PARSE_DIR, 'data')    #Папка data


class SimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор матчей v0.1")
        self.league_data = None
        self.create_widgets()

    def create_widgets(self):
        self.file_frame = ttk.LabelFrame(self.root, text="Выбор файла данных")
        self.file_frame.pack(padx=10, pady=5, fill=tk.X)

        self.file_combobox = ttk.Combobox(self.file_frame, state="readonly")
        self.file_combobox.pack(padx=5, pady=5, fill=tk.X)


        self.btn_frame = ttk.Frame(self.root)
        self.btn_frame.pack(pady=10)
        self.simulate_btn = ttk.Button(self.btn_frame, text="Запуск симуляции вручную", command=self.manual_simulation)
        self.simulate_btn.pack()

        self.btn_frame = ttk.Frame(self.root)
        self.btn_frame.pack(pady=10)
        self.simulate_btn = ttk.Button(self.btn_frame, text="Обновить flashscore", command=self.flashscore_parse)
        self.simulate_btn.pack()

        self.btn_frame = ttk.Frame(self.root)
        self.btn_frame.pack(pady=10)
        self.simulate_btn = ttk.Button(self.btn_frame, text="Свести Фонбет", command=self.fon_comp)
        self.simulate_btn.pack()

        self.update_file_list()

    def update_file_list(self):
        data_dir = os.path.join(DATA_DIR)
        try:
            files = [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]
        except FileNotFoundError:
            files = []
        self.file_combobox["values"] = files

    def load_teams(self):
        """
        Вывод команд при выборе лиги
        :param event:
        :return:
        """
        data_dir = os.path.join(DATA_DIR)
        file_name = self.file_combobox.get()
        file_path = os.path.join(data_dir, file_name)

        data = load_excel_file(file_path)
        if data and "Общие матчи (Все матчи)" in data:
            teams = sorted(
                data["Общие матчи (Все матчи)"]["Команда"].tolist(),
                key=lambda x: x.lower()
            )
            self.home_team["values"] = teams
            self.away_team["values"] = teams
            self.league_data = data

    def get_team_data(self, team_name):
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
            df = self.league_data.get(sheet)    #Безопасно получаем DataFrame
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

    def manual_simulation(self):
        """
        Ручная симуляция
        :return:
        """
        if not self.file_combobox.get():
            messagebox.showwarning("Ошибка", "Выберите лигу(файл данных)!")
            return
        result_window = tk.Toplevel(self.root)
        result_window.title("Ручная симуляция")
        result_window.minsize(400, 400)
        result_window.geometry("400x400")

        """Контейнер с прокруткой"""
        container = ttk.Frame(result_window)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container)
        s_frame = ttk.Frame(canvas)

        canvas.create_window((0, 0), window=s_frame, anchor="nw")
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        """Основной контент"""
        main_frame = ttk.Frame(s_frame)
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        self.team_frame = ttk.LabelFrame(main_frame, text="Выбор команд")
        self.team_frame.pack(padx=10, pady=5, fill=tk.X)
        self.home_team = ttk.Combobox(self.team_frame, state="readonly")
        self.away_team = ttk.Combobox(self.team_frame, state="readonly")
        self.home_team.pack(side=tk.LEFT, padx=5, pady=5)
        self.away_team.pack(side=tk.RIGHT, padx=5, pady=5)
        self.load_teams()    #загрузка команд
        self.btn_frame = ttk.Frame(main_frame)
        self.btn_frame.pack(pady=10)
        self.simulate_btn = ttk.Button(self.btn_frame, text="Запустить симуляцию", command=self.run_simulation)
        self.simulate_btn.pack()


    def run_simulation(self):
        home_team = self.home_team.get()
        away_team = self.away_team.get()

        if not home_team or not away_team:
            messagebox.showwarning("Ошибка", "Выберите обе команды!")
            return

        try:
            home_data = self.get_team_data(home_team)
            away_data = self.get_team_data(away_team)

            home_avg = calculate_averages(home_data["total"], home_data["home"], home_data["away"])
            away_avg = calculate_averages(away_data["total"], away_data["away"], away_data["home"])

            results = simulate_matches(home_avg, away_avg)
            self.show_results(results, home_team, away_team)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def show_results(self, results, home_team, away_team):
        result_window = tk.Toplevel(self.root)
        result_window.title("Результаты симуляции")
        result_window.minsize(1000, 1000)
        result_window.geometry("1200x800")

        """Контейнер с прокруткой"""
        container = ttk.Frame(result_window)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container)
        scroll_y = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_x = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        """Стилизация"""
        style = ttk.Style()
        style.configure("Header.TLabel", font=('Arial', 14, 'bold'), foreground="#2c3e50")
        style.configure("SubHeader.TLabel", font=('Arial', 12, 'bold'), foreground="#34495e")
        style.configure("Data.TLabel", font=('Arial', 10))

        """Основной контент"""
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        """Шапка"""
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=15)
        ttk.Label(
            header_frame,
            text=f"СИМУЛЯЦИЯ: {home_team} vs {away_team}",
            style="Header.TLabel"
        ).pack(side=tk.TOP)

        """Колонки"""
        columns_frame = ttk.Frame(main_frame)
        columns_frame.pack(fill=tk.BOTH, expand=True)

        """Колонка 1 - Основные исходы"""
        col1 = ttk.Frame(columns_frame)
        col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(col1, text="Основные исходы", style="SubHeader.TLabel").pack(anchor=tk.W)
        for outcome in ["П1", "П2", "Ничья"]:
            prob = results.get(outcome, 0)
            odds = 1 / prob if prob > 0 else 0

            ttk.Label(col1,
                      text=f"{outcome}: {prob * 100:.2f}% (x{odds:.2f})",
                      style="Data.TLabel"
                      ).pack(anchor=tk.W, pady=2)

        """Колонка 2 - Форы"""
        col2 = ttk.Frame(columns_frame)
        col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(col2, text="Форы", style="SubHeader.TLabel").pack(anchor=tk.W)
        for team in ["Хозяева", "Гости"]:
            frame = ttk.Frame(col2)
            frame.pack(fill=tk.X, pady=3)

            for handicap in ["-1.5", "+1.5"]:
                key = f"{team} {handicap}"
                prob = results.get(key, 0)
                odds = 1 / prob if prob > 0 else 0
                ttk.Label(frame,
                          text=f"{key}: {prob * 100:.2f}% (x{odds:.2f})",
                          width=18,
                          style="Data.TLabel"
                          ).pack(anchor=tk.W, pady=2)

        """Колонка 3 - Общие тоталы"""
        col3 = ttk.Frame(columns_frame)
        col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(col3, text="Общие тоталы", style="SubHeader.TLabel").pack(anchor=tk.W)
        for tol in [4.5, 5.5, 6.5]:
            frame = ttk.Frame(col3)
            frame.pack(fill=tk.X, pady=3)

            ttk.Label(frame, text=f"Тотал {tol}", width=12, style="Data.TLabel").pack(side=tk.LEFT)
            for suffix in ["больше", "меньше"]:
                key = f"Тотал {tol} {suffix}"
                prob = results.get(key, 0)
                odds = 1 / prob if prob > 0 else 0
                ttk.Label(frame,
                          text=f"{prob * 100:.2f}% (x{odds:.2f})",
                          width=18,
                          style="Data.TLabel"
                          ).pack(side=tk.LEFT)

        """Колонка 4 - Индивидуальные тоталы"""
        col4 = ttk.Frame(columns_frame)
        col4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        ttk.Label(col4, text="Индивидуальные тоталы", style="SubHeader.TLabel").pack(anchor=tk.W)
        for team in ["Хозяева", "Гости"]:
            team_frame = ttk.Frame(col4)
            team_frame.pack(fill=tk.X, pady=5)

            ttk.Label(team_frame,
                      text=team,
                      style="SubHeader.TLabel",
                      width=15
                      ).pack(side=tk.LEFT)

            for tol in [1.5, 2.5, 3.5]:
                tol_frame = ttk.Frame(team_frame)
                tol_frame.pack(side=tk.LEFT, padx=8)

                for suffix in ["ИТБ", "ИТМ"]:
                    key = f"{team} {suffix} {tol}"
                    prob = results.get(key, 0)
                    odds = 1 / prob if prob > 0 else 0
                    ttk.Label(tol_frame,
                              text=f"{suffix}{tol}: {prob * 100:.2f}% (x{odds:.2f})",
                              style="Data.TLabel"
                              ).pack(anchor=tk.W)

        """Обновление прокрутки"""
        scrollable_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        """Центрирование окна"""
        result_window.update_idletasks()
        width = result_window.winfo_width()
        height = result_window.winfo_height()
        x = (result_window.winfo_screenwidth() // 2) - (width // 2)
        y = (result_window.winfo_screenheight() // 2) - (height // 2)
        result_window.geometry(f'+{x}+{y}')

    def flashscore_parse(self):
        """
        Обновление данных с flashscore
        :return:
        """
        try:
            flashscore_parse()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        print("Обновление выполнено")




    def get_fon_team_data(self, team_name):
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
            df = self.league_data.get(sheet)    #Безопасно получаем DataFrame
            if df is not None and "Команда" in df.columns:    #Ищем самую похожую команду (если точного совпадения нет)
                team_list = df["Команда"].dropna().tolist()    #Убираем NaN и берём список команд
                best_match = difflib.get_close_matches(team_name, team_list, n=1, cutoff=0.3)    #cutoff отвечает за схожесть строк, 1 это максимально приближеннная, 0.1 минимально
                if best_match:
                    team_row = df[df["Команда"] == best_match[0]]
                    data[key] = team_row.iloc[0] if not team_row.empty else None
                else:
                    data[key] = None
            else:
                data[key] = None    #Если таблицы нет, ставим None
        return data


    def fon_comp(self):
        """
        Сведение расчетов с кф фонбета
        :return:
        """

        if not self.file_combobox.get():
            messagebox.showwarning("Ошибка", "Выберите лигу(файл данных)!")
            return
        data_dir = os.path.join(DATA_DIR)
        file_name = self.file_combobox.get()                    #file_name = "KHL_data.xlsx"  # Адрес к лиге
        file_path = os.path.join(data_dir, file_name)

        data = load_excel_file(file_path)
        if data and "Общие матчи (Все матчи)" in data:
            self.league_data = data

        result_window = tk.Toplevel(self.root)
        result_window.title("Результаты симуляции")
        result_window.minsize(1700, 1000)
        result_window.geometry("1700x1000")

        """Контейнер с прокруткой"""
        container = ttk.Frame(result_window)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container)
        scroll_y = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_x = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        """Стилизация"""
        style = ttk.Style()
        style.configure("Header.TLabel", font=('Arial', 14, 'bold'), foreground="#2c3e50")
        style.configure("SubHeader.TLabel", font=('Arial', 12, 'bold'), foreground="#34495e")
        style.configure("Data.TLabel", font=('Arial', 10))

        """Основной контент"""
        main_frame = ttk.Frame(scrollable_frame)
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        teams = fetch_and_display_line_events(file_name)
        for a in teams:
            try:
                home_team = a["team_1"]
                away_team = a["team_2"]
                home_data = self.get_fon_team_data(home_team)
                away_data = self.get_fon_team_data(away_team)

                home_avg = calculate_averages(home_data["total"], home_data["home"], home_data["away"])
                away_avg = calculate_averages(away_data["total"], away_data["away"], away_data["home"])

                results = simulate_matches(home_avg, away_avg)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

            """Шапка"""
            header_frame = ttk.Frame(main_frame)
            header_frame.pack(fill=tk.X, pady=15)
            ttk.Label(
                header_frame,
                style="Header.TLabel"
            ).pack(side=tk.TOP)


            """Колонки"""
            columns_frame = ttk.Frame(main_frame)
            columns_frame.pack(fill=tk.BOTH, expand=True)

            """Колонка 1 - Команды"""
            col1 = ttk.Frame(columns_frame)
            col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
            ttk.Label(col1, text="Команды", style="SubHeader.TLabel").pack(anchor=tk.W)
            ttk.Label(col1, text=f"{home_team}",
                    style="Data.TLabel"
                    ).pack(anchor=tk.W, pady=2)
            ttk.Label(col1,
                      text=f"{away_team}",
                      style="Data.TLabel"
                      ).pack(anchor=tk.W, pady=2)
            ttk.Label(col1,
                      text=f"=====",
                      style="Data.TLabel"
                      ).pack(anchor=tk.W, pady=2)

            """Колонка 2 - Основные исходы"""
            col2 = ttk.Frame(columns_frame)
            col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

            ttk.Label(col2, text="Основные исходы", style="SubHeader.TLabel").pack(anchor=tk.W)
            for outcome in ["П1", "П2", "Ничья"]:
                prob = results.get(outcome, 0)
                odds = 1 / prob if prob > 0 else 0

                if outcome == "П1":
                    ttk.Label(col2,
                              text=f"{outcome}: {prob * 100:.2f}% (x{odds:.2f}) fon {a['p1']}",
                              style="Data.TLabel"
                              ).pack(anchor=tk.W, pady=2)
                elif outcome == "П2":
                    ttk.Label(col2,
                              text=f"{outcome}: {prob * 100:.2f}% (x{odds:.2f}) fon {a['p2']}",
                              style="Data.TLabel"
                              ).pack(anchor=tk.W, pady=2)
                else:
                    ttk.Label(col2,
                              text=f"{outcome}: {prob * 100:.2f}% (x{odds:.2f}) fon {a['x']}",
                              style="Data.TLabel"
                              ).pack(anchor=tk.W, pady=2)

            """Колонка 3 - Форы"""
            col3 = ttk.Frame(columns_frame)
            col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

            ttk.Label(col3, text="Форы", style="SubHeader.TLabel").pack(anchor=tk.W)
            for team in ["Хозяева", "Гости"]:
                frame = ttk.Frame(col3)
                frame.pack(fill=tk.X, pady=3)
    
                for handicap in ["-1.5", "+1.5"]:
                    key = f"{team} {handicap}"
                    prob = results.get(key, 0)
                    odds = 1 / prob if prob > 0 else 0
                    if handicap == "-1.5" and team == "Хозяева":
                        ttk.Label(frame,
                                  text=f"{key}: {prob * 100:.2f}% (x{odds:.2f}) fon {a["fminus15k1"]}",
                                  width=35,
                                  style="Data.TLabel"
                                  ).pack(anchor=tk.W, pady=2)
                    elif handicap == "+1.5" and team == "Хозяева":
                        ttk.Label(frame,
                                  text=f"{key}: {prob * 100:.2f}% (x{odds:.2f}) fon {a["fplus15k1"]}",
                                  width=35,
                                  style="Data.TLabel"
                                  ).pack(anchor=tk.W, pady=2)
                    elif handicap == "-1.5" and team == "Гости":
                        ttk.Label(frame,
                                  text=f"{key}: {prob * 100:.2f}% (x{odds:.2f}) fon {a["fminus15k2"]}",
                                  width=35,
                                  style="Data.TLabel"
                                  ).pack(anchor=tk.W, pady=2)
                    elif handicap == "+1.5" and team == "Гости":
                        ttk.Label(frame,
                                  text=f"{key}: {prob * 100:.2f}% (x{odds:.2f}) fon {a["fplus15k2"]}",
                                  width=35,
                                  style="Data.TLabel"
                                  ).pack(anchor=tk.W, pady=2)

            """Колонка 4 - Общие тоталы"""
            col4 = ttk.Frame(columns_frame)
            col4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

            ttk.Label(col4, text="Общие тоталы", style="SubHeader.TLabel").pack(anchor=tk.W)
            for tol in [4.5, 5.5, 6.5]:
                frame = ttk.Frame(col4)
                frame.pack(fill=tk.X, pady=3)
    
                ttk.Label(frame, text=f"Тотал {tol}", width=12, style="Data.TLabel").pack(side=tk.LEFT)
                for suffix in ["больше", "меньше"]:
                    key = f"Тотал {tol} {suffix}"
                    prob = results.get(key, 0)
                    odds = 1 / prob if prob > 0 else 0
                    ttk.Label(frame,
                              text=f"{prob * 100:.2f}% (x{odds:.2f})",
                              width=18,
                              style="Data.TLabel"
                              ).pack(side=tk.LEFT)

            """Колонка 5 - Индивидуальные тоталы"""
            col5 = ttk.Frame(columns_frame)
            col5.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

            ttk.Label(col5, text="Индивидуальные тоталы", style="SubHeader.TLabel").pack(anchor=tk.W)
            for team in ["Хозяева", "Гости"]:
                team_frame = ttk.Frame(col5)
                team_frame.pack(fill=tk.X, pady=5)
    
                ttk.Label(team_frame,
                          text=team,
                          style="SubHeader.TLabel",
                          width=15
                          ).pack(side=tk.LEFT)
    
                for tol in [1.5, 2.5, 3.5]:
                    tol_frame = ttk.Frame(team_frame)
                    tol_frame.pack(side=tk.LEFT, padx=8)
    
                    for suffix in ["ИТБ", "ИТМ"]:
                        key = f"{team} {suffix} {tol}"
                        prob = results.get(key, 0)
                        odds = 1 / prob if prob > 0 else 0
                        ttk.Label(tol_frame,
                                  text=f"{suffix}{tol}: {prob * 100:.2f}% (x{odds:.2f})",
                                  style="Data.TLabel"
                                  ).pack(anchor=tk.W)

        """Обновление прокрутки"""
        scrollable_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        """Центрирование окна"""
        result_window.update_idletasks()
        width = result_window.winfo_width()
        height = result_window.winfo_height()
        x = (result_window.winfo_screenwidth() // 2) - (width // 2)
        y = (result_window.winfo_screenheight() // 2) - (height // 2)
        result_window.geometry(f'+{x}+{y}')


if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationApp(root)
    root.mainloop()