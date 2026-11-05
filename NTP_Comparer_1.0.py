import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ntplib
from datetime import datetime, timedelta
import time
import csv


class NTPComparatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NTP Server Time Comparator")
        self.root.geometry("600x400")

        # Переменные для хранения данных
        self.server1 = tk.StringVar(value="pool.ntp.org")
        self.server2 = tk.StringVar(value="time.google.com")
        self.attempts = tk.IntVar(value=3)
        self.delay = tk.IntVar(value=1)
        self.results = []

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Фрейм для ввода параметров
        input_frame = ttk.LabelFrame(self.root, text="Параметры подключения", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        # Поля ввода серверов
        ttk.Label(input_frame, text="Сервер 1:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.server1, width=30).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(input_frame, text="Сервер 2:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(input_frame, textvariable=self.server2, width=30).grid(row=1, column=1, padx=5, pady=2)

        # Количество попыток
        ttk.Label(input_frame, text="Количество попыток:").grid(row=2, column=0, sticky=tk.W)
        ttk.Spinbox(input_frame, from_=1, to=10, textvariable=self.attempts, width=5).grid(row=2, column=1, sticky=tk.W,
                                                                                           padx=5, pady=2)

        # Задержка между попытками
        ttk.Label(input_frame, text="Задержка (сек):").grid(row=3, column=0, sticky=tk.W)
        ttk.Spinbox(input_frame, from_=1, to=60, textvariable=self.delay, width=5).grid(row=3, column=1, sticky=tk.W,
                                                                                        padx=5, pady=2)

        # Кнопки управления
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Сравнить", command=self.compare_servers).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Сохранить отчет", command=self.save_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить", command=self.clear_results).pack(side=tk.LEFT, padx=5)

        # Таблица результатов
        self.tree = ttk.Treeview(self.root, columns=("timestamp", "server1", "server2", "difference"), show="headings")
        self.tree.heading("timestamp", text="Время проверки")
        self.tree.heading("server1", text="Сервер 1 (мкс)")
        self.tree.heading("server2", text="Сервер 2 (мкс)")
        self.tree.heading("difference", text="Разница (мкс)")

        self.tree.column("timestamp", width=150)
        self.tree.column("server1", width=120)
        self.tree.column("server2", width=120)
        self.tree.column("difference", width=120)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Статус бар
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, padx=5, pady=5)

    def get_ntp_time(self, server):
        try:
            client = ntplib.NTPClient()
            response = client.request(server, version=3)
            return response.tx_time
        except Exception as e:
            self.status_var.set(f"Ошибка подключения к {server}: {str(e)}")
            return None

    def compare_servers(self):
        server1 = self.server1.get().strip()
        server2 = self.server2.get().strip()

        if not server1 or not server2:
            messagebox.showerror("Ошибка", "Укажите оба NTP сервера")
            return

        attempts = self.attempts.get()
        delay = self.delay.get()

        self.results = []

        for i in range(attempts):
            self.status_var.set(f"Попытка {i + 1} из {attempts}...")
            self.root.update()

            time1 = self.get_ntp_time(server1)
            time2 = self.get_ntp_time(server2)

            if time1 is None or time2 is None:
                continue

            # Вычисляем разницу в микросекундах
            difference = abs(time1 - time2) * 1_000_000
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            result = {
                "timestamp": timestamp,
                "server1": f"{time1:.6f}",
                "server2": f"{time2:.6f}",
                "difference": f"{difference:.2f}"
            }

            self.results.append(result)
            self.tree.insert("", tk.END, values=(
                timestamp,
                f"{time1:.6f}",
                f"{time2:.6f}",
                f"{difference:.2f}"
            ))

            if i < attempts - 1:
                time.sleep(delay)

        if self.results:
            avg_diff = sum(float(r["difference"]) for r in self.results) / len(self.results)
            self.status_var.set(f"Готово. Среднее расхождение: {avg_diff:.2f} микросекунд")
        else:
            self.status_var.set("Не удалось получить данные с серверов")

    def save_report(self):
        if not self.results:
            messagebox.showwarning("Предупреждение", "Нет данных для сохранения")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")],
            title="Сохранить отчет"
        )

        if not file_path:
            return

        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Время проверки", "Сервер 1 (UTC)", "Сервер 2 (UTC)", "Разница (микросекунды)"])

                for result in self.results:
                    writer.writerow([
                        result["timestamp"],
                        result["server1"],
                        result["server2"],
                        result["difference"]
                    ])

            messagebox.showinfo("Успех", f"Отчет сохранен в {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {str(e)}")

    def clear_results(self):
        self.tree.delete(*self.tree.get_children())
        self.results = []
        self.status_var.set("Готово")


if __name__ == "__main__":
    root = tk.Tk()
    app = NTPComparatorApp(root)
    root.mainloop()