import sys
import subprocess
import pkg_resources
from PIL import Image, ImageTk
import time
import psutil
import os
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import zipfile
import threading
from ttkthemes import ThemedTk

class MinecraftInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Установщик сборок Nevir")
        self.root.geometry("800x600")
        
        # Загрузка иконки
        try:
            if getattr(sys, 'frozen', False):
                application_path = sys._MEIPASS
            else:
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(application_path, 'icon.ico')
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Не удалось загрузить иконку: {e}")
        
        # Устанавливаем тему ubuntu
        self.root.set_theme("ubuntu")
        
        # Словарь с путями по умолчанию
        self.default_paths = {
            "TLauncher": str(Path.home() / "AppData/Roaming/.minecraft/versions"),
            "Prism Launcher": str(Path.home() / "AppData/Roaming/PrismLauncher/instances"),
            "Legacy Launcher": str(Path.home() / "AppData/Roaming/.minecraft")
        }
        
        # Словарь с URL для агрузки
        self.download_urls = {
            "TLauncher": {
                "low": "http://nevir.dobskr.ru/downloads/lowPC/TLauncher/NEVIR_LOW_TL.zip",
                "normal": "http://nevir.dobskr.ru/downloads/highPC/TLauncher/NEVIR_HIGH_TL.zip"
            },
            "Prism Launcher": {
                "low": "http://nevir.dobskr.ru/downloads/lowPC/Prismlauncher/Nevir_LowP_PRISM.zip",
                "normal": "http://nevir.dobskr.ru/downloads/highPC/Prismlauncher/Nevir_GoodP_PRISM.zip"
            },
            "Legacy Launcher": {
                "low": "http://nevir.dobskr.ru/downloads/lowPC/LegacyLauncher/NEVIR_LOW_LEGACY.zip",
                "normal": "http://nevir.dobskr.ru/downloads/highPC/LegacyLauncher/NEVIR_HIGH_LEGACY.zip"
            }
        }
        
        # Добавляем новые переменные для отслеживания скорости
        self.download_start_time = 0
        self.downloaded_size = 0
        self.current_speed = 0
        
        self.installation_thread = None
        self.is_installing = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Настройка стилей
        style = ttk.Style()
        
        # Основные цвета (более нейтральные)
        primary_color = "#424242"    # Темно-серый
        accent_color = "#616161"     # Серый для ховера
        text_color = "#212121"       # Почти черный
        light_text = "#757575"       # Серый для второстепенного текста
        
        # Настройка стилей
        style.configure("Title.TLabel",
                       font=("Segoe UI", 24, "bold"),
                       foreground=text_color)
        
        style.configure("Card.TLabelframe",
                       background="white",
                       padding=15)
        
        style.configure("Card.TLabelframe.Label",
                       font=("Segoe UI", 10, "bold"),
                       foreground=text_color,
                       background="white")
        
        # Стиль кнопок (серый вместо синего)
        style.configure("Primary.TButton",
                       font=("Segoe UI", 10),
                       padding=(20, 10))
        
        # Убираем эффект при наведении
        style.map("Primary.TButton",
                 background=[('active', 'white'),  # Тот же цвет, что и в обычном состоянии
                           ('pressed', 'white')],
                 foreground=[('active', text_color),
                           ('pressed', text_color)])
        
        # Убираем фокусную рамку
        style.configure("Primary.TButton",
                       focuscolor='none')  # Убирает фокусную рамку
        
        # Стиль радиокнопок
        style.configure("TRadiobutton",
                       font=("Segoe UI", 10),
                       background="white",
                       foreground=text_color)
        
        # Стиль прогресс-бара (серый вместо синего)
        style.configure("Horizontal.TProgressbar",
                       background=primary_color,
                       troughcolor="#E0E0E0")
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Заголовок
        title_label = ttk.Label(main_frame,
                               text="Установщик сборок Minecraft",
                               style="Title.TLabel")
        title_label.pack(pady=(0, 20))
        
        # Контейнер для опций
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill="x", pady=(0, 20))
        
        # Левая панель
        left_panel = ttk.Frame(options_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Выбор лаунчера
        launcher_frame = ttk.LabelFrame(left_panel,
                                      text="ВЫБОР ЛАУНЧЕРА",
                                      style="Card.TLabelframe")
        launcher_frame.pack(fill="x", pady=(0, 10))
        
        self.launcher_var = tk.StringVar()
        self.launcher_combo = ttk.Combobox(launcher_frame,
                                         textvariable=self.launcher_var,
                                         values=list(self.default_paths.keys()),
                                         state="readonly",
                                         font=("Segoe UI", 10))
        self.launcher_combo.pack(fill="x", padx=10, pady=10)
        self.launcher_combo.bind("<<ComboboxSelected>>", self.update_path)
        self.launcher_combo.set("TLauncher")
        
        # Правая панель
        right_panel = ttk.Frame(options_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Выбор вер��ии
        version_frame = ttk.LabelFrame(right_panel,
                                     text="ВЫБОР ВЕРСИИ",
                                     style="Card.TLabelframe")
        version_frame.pack(fill="x", pady=(0, 10))
        
        self.version_var = tk.StringVar(value="normal")
        ttk.Radiobutton(version_frame,
                        text="Обычная сборка",
                        variable=self.version_var,
                        value="normal").pack(fill="x", padx=10, pady=5)
        ttk.Radiobutton(version_frame,
                        text="Сборка для слабых ПК",
                        variable=self.version_var,
                        value="low").pack(fill="x", padx=10, pady=5)
        
        # Путь установки
        path_frame = ttk.LabelFrame(main_frame,
                                  text="ПУТЬ УСТАНОВКИ",
                                  style="Card.TLabelframe")
        path_frame.pack(fill="x", pady=(0, 20))
        
        path_container = ttk.Frame(path_frame)
        path_container.pack(fill="x", padx=10, pady=10)
        
        self.path_var = tk.StringVar()
        self.path_var.set(self.default_paths["TLauncher"])
        
        path_entry = ttk.Entry(path_container,
                              textvariable=self.path_var,
                              font=("Segoe UI", 10))
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(path_container,
                               text="Обзор",
                               command=self.browse_path,
                               style="Primary.TButton")
        browse_btn.pack(side="right")
        
        # Прогресс
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame,
                                      variable=self.progress_var,
                                      maximum=100,
                                      mode='determinate')
        self.progress.pack(fill="x", pady=(0, 10))
        
        # Статус
        self.status_var = tk.StringVar(value="Готов к установке")
        status_label = ttk.Label(main_frame,
                               textvariable=self.status_var,
                               font=("Segoe UI", 10),
                               foreground=light_text)
        status_label.pack(pady=(0, 20))
        
        # Кнопка установки
        install_btn = ttk.Button(main_frame,
                               text="УСТАНОВИТЬ",
                               command=self.start_installation,
                               style="Primary.TButton")
        install_btn.pack(pady=(0, 20))
        
        # Футер
        footer = ttk.Label(main_frame,
                         text="© 2024 Nevir",
                         font=("Segoe UI", 9),
                         foreground=light_text)
        footer.pack(side="bottom")
        
    def update_path(self, event=None):
        selected = self.launcher_var.get()
        self.path_var.set(self.default_paths[selected])
        
    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)
            
    def cleanup_processes(self):
        """Очищает процессы и корректно завершает работу приложения"""
        try:
            # Останавливаем установку если она запущена
            if self.is_installing:
                self.is_installing = False
                if self.installation_thread and self.installation_thread.is_alive():
                    self.installation_thread.join(timeout=1.0)
            
            # Закрываем окно и завершаем приложение
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Ошибка при закрытии: {e}")
            sys.exit(1)

    def start_installation(self):
        if self.is_installing:
            return
            
        # Отключаем кнопку установки во время процесса
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.configure(state='disabled')
        
        try:
            self.is_installing = True
            self.installation_thread = threading.Thread(target=self.install)
            self.installation_thread.daemon = True
            self.installation_thread.start()
        except Exception as e:
            self.is_installing = False
            messagebox.showerror("Ошибка", f"Не удалось начать установку: {str(e)}")
            # Возвращаем кнопкам активное состояние
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.configure(state='normal')
                    
    def format_size(self, size):
        """Форматирует размер в байтах в человекочитаемый формат"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} ТБ"

    def format_speed(self, speed):
        """Форматирует скорость в байтах/сек в человекочитаемый формат"""
        return f"{self.format_size(speed)}/с"

    def calculate_eta(self, total_size, downloaded, speed):
        """Рассчитывает оставшееся время загрузки"""
        if speed == 0:
            return "∞"
        seconds_left = (total_size - downloaded) / speed
        
        # Более детальный расчет времени
        hours = int(seconds_left // 3600)
        minutes = int((seconds_left % 3600) // 60)
        seconds = int(seconds_left % 60)
        
        if hours > 0:
            return f"{hours}ч {minutes}м {seconds}с"
        elif minutes > 0:
            return f"{minutes}м {seconds}с"
        else:
            return f"{seconds}с"

    def install(self):
        try:
            launcher = self.launcher_var.get()
            version_type = "low" if self.version_var.get() == "low" else "normal"
            install_path = self.path_var.get()
            
            download_url = self.download_urls[launcher][version_type]
            
            # Создаём папки в зависимости от лаунчера
            if launcher == "TLauncher":
                minecraft_path = os.path.join(str(Path.home()), "AppData", "Roaming", ".minecraft")
                install_path = os.path.join(minecraft_path, "versions")
                os.makedirs(install_path, exist_ok=True)
            elif launcher == "Prism Launcher":
                modpack_name = "Nevir" + ("_Low" if version_type == "low" else "_High")
                install_path = os.path.join(install_path, modpack_name)
                os.makedirs(install_path, exist_ok=True)
            else:  # Legacy Launcher
                os.makedirs(install_path, exist_ok=True)
            
            # Загружаем файл
            self.status_var.set("Подготовка к загрузке...")
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            temp_file = Path(install_path) / "temp.zip"
            
            # Увеличиваем размер буфера для ускорения загрузки
            block_size = 8192  # Увеличенный размер блока
            self.downloaded_size = 0
            self.download_start_time = time.time()
            last_update_time = self.download_start_time
            
            with open(temp_file, 'wb') as f:
                for data in response.iter_content(block_size):
                    self.downloaded_size += len(data)
                    f.write(data)
                    
                    # Обновляем информацию каждые 0.1 секунды
                    current_time = time.time()
                    if current_time - last_update_time >= 0.1:
                        # Рассчитываем скорость и прогресс
                        elapsed_time = current_time - self.download_start_time
                        self.current_speed = self.downloaded_size / elapsed_time
                        progress = (self.downloaded_size / total_size) * 100
                        
                        # Рассчитываем примерное время окончания
                        eta = self.calculate_eta(total_size, self.downloaded_size, self.current_speed)
                        current_time_str = time.strftime("%H:%M:%S")
                        
                        if self.current_speed > 0:
                            finish_time = time.localtime(time.time() + (total_size - self.downloaded_size) / self.current_speed)
                            finish_time_str = time.strftime("%H:%M:%S", finish_time)
                        else:
                            finish_time_str = "неизвестно"
                        
                        # Обновляем статус с более подробной информацией
                        status_text = (
                            f"Загружено: {self.format_size(self.downloaded_size)} из {self.format_size(total_size)}\n"
                            f"Скорость: {self.format_speed(self.current_speed)}\n"
                            f"Осталось времени: {eta}\n"
                            f"Ожидаемое время завершения: {finish_time_str}"
                        )
                        
                        self.progress_var.set(progress)
                        self.status_var.set(status_text)
                        self.root.update_idletasks()
                        last_update_time = current_time

            # Распаковка
            self.status_var.set("Распаковка файлов...")
            self.progress_var.set(0)
            
            with zipfile.ZipFile(temp_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for index, file_info in enumerate(zip_ref.filelist, 1):
                    # Получаем относительный путь фала
                    filename = file_info.filename
                    
                    # Пропускаем пустые директории
                    if filename.endswith('/'):
                        continue
                        
                    # Определяем, куда извлекать файл
                    if launcher == "TLauncher":
                        # Если это файл для versions, и��влекаем в install_path
                        if filename.startswith('versions/'):
                            target_path = os.path.join(minecraft_path, filename)
                        # Если это resourcepack, извлекаем в папку resourcepacks
                        elif filename.startswith('resourcepacks/'):
                            target_path = os.path.join(minecraft_path, filename)
                        else:
                            target_path = os.path.join(install_path, filename)
                    else:
                        target_path = os.path.join(install_path, filename)
                    
                    # Создаем директорию для файла если её нет
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    # Извлекаем айл
                    try:
                        with zip_ref.open(file_info) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    except Exception as e:
                        print(f"Ошибка при извлечении {filename}: {str(e)}")
                        continue
                    
                    # Обновляем прогресс распаковки
                    progress = (index / total_files) * 100
                    self.progress_var.set(progress)
                    self.status_var.set(f"Распаковка: {index} из {total_files} файлов ({int(progress)}%)")
                    self.root.update_idletasks()

            # Удаляем временный файл
            temp_file.unlink()
            
            self.status_var.set("Установка успешно завершена!")
            messagebox.showinfo("Успех", "Установка успешно завершена!")
            
        except Exception as e:
            self.status_var.set("Произошла ошибка!")
            messagebox.showerror("Ошибка", f"Ошибка при установке: {str(e)}")
        finally:
            self.is_installing = False
            self.cleanup_processes()
            # Возвращаем кнопкам активное состояние
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.configure(state='normal')

def cleanup():
    """Очистка временных файлов и директорий после установки"""
    paths_to_remove = [
        'build',
        'dist',
        '__pycache__',
        '*.spec'
    ]
    
    for path in paths_to_remove:
        if '*' in path:
            # Удаление файлов по маске
            for file in Path('.').glob(path):
                if file.name != 'Nevir Installer.spec':  # Сохраняем основной spec файл
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"Не удалось удалить {file}: {e}")
        else:
            # Удаление директорий
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                except Exception as e:
                    print(f"Не удалось удалить {path}: {e}")

def main():
    try:
        root = ThemedTk(theme="ubuntu")
        app = MinecraftInstaller(root)
        root.protocol("WM_DELETE_WINDOW", app.cleanup_processes)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Критическая ошибка", str(e))
    finally:
        cleanup()

if __name__ == "__main__":
    main() 