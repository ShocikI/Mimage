import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from FileMenagment import FileMenager
from threading import Thread
import os
import numpy as np


class GUI:
    file_menager = FileMenager()
    root = tk.Tk()
    root.title("Mimage")
    buttons = []

    cores = int(os.cpu_count() / 2)
    weight_file = []
    entry_weight = []
    button_weight = []
    weight_is_used = False

    file_counter = tk.StringVar()
    file_width = tk.StringVar()
    file_height = tk.StringVar()
    image_width = tk.StringVar()
    image_height = tk.StringVar()
    a_error_str = tk.StringVar()
    s_error_str = tk.StringVar()
    t_error_str = tk.StringVar()
    f_error_str = tk.StringVar()
    i_error_str = tk.StringVar()

    is_thres_w = tk.BooleanVar()
    is_thres_r = tk.BooleanVar()
    is_thres_g = tk.BooleanVar()
    is_thres_b = tk.BooleanVar()
    is_top = tk.BooleanVar()
    is_right = tk.BooleanVar()
    filter_by_white = tk.BooleanVar()
    filter_by_red = tk.BooleanVar()
    filter_by_green = tk.BooleanVar()
    filter_by_blue = tk.BooleanVar()

    average_frame = tk.LabelFrame(root, text="Uśrednianie")

    progress_bar = ttk.Progressbar(
        root, orient="horizontal", length=800, mode="indeterminate"
    )

    def create_weight_option(self):
        self.weight_file = ttk.Combobox(
            self.average_frame, values=self.file_menager.file_list,
            width=50, justify="right"
        )
        weight_label = tk.Label(self.average_frame, text="Waga")
        self.entry_weight = tk.Entry(self.average_frame, width=5)
        self.button_weight = tk.Button(
            self.average_frame, text="Zmień wagę",
            command=self.set_weight
        )
        self.weight_file.grid(row=0, column=0, padx=5, pady=5, columnspan=3)
        weight_label.grid(row=1, column=0, padx=5, pady=5, sticky="E")
        self.entry_weight.grid(row=1, column=1, padx=5, pady=5, sticky="W")
        self.button_weight.grid(row=1, column=2, padx=5, pady=5)

    def start_progress(self):
        self.progress_bar.start(20)
        for button in self.buttons:
            button.config(state="disabled")
        if self.button_weight:
            self.button_weight.config(state="disabled")

    def stop_progress(self):
        self.progress_bar.stop()
        self.cores = int(os.cpu_count() / 2)
        self.weight_is_used = False
        for button in self.buttons:
            button.config(state="normal")
        if self.button_weight:
            self.button_weight.config(state="normal")

    def fill_file_list(self):
        val = self.file_menager.fill_file_list()
        if val == 1:
            return
        self.file_counter.set(str(len(self.file_menager.file_list)))
        self.file_menager.read_file(0)
        self.file_width.set(str(self.file_menager.readed_file.shape[1]))
        self.file_height.set(str(self.file_menager.readed_file.shape[0]))
        self.create_weight_option()

    def fill_list_from_folder(self):
        val = self.file_menager.fill_list_from_folder()
        if val == 1:
            self.file_counter.set("0")
            self.file_width.set("0")
            self.file_height.set("0")
            self.create_weight_option()
            return
        self.file_counter.set(str(len(self.file_menager.file_list)))
        self.file_menager.read_file(0)
        self.file_width.set(str(self.file_menager.readed_file.shape[1]))
        self.file_height.set(str(self.file_menager.readed_file.shape[0]))
        self.create_weight_option()

    def average_file(self):
        self.a_error_str.set("")

        if len(self.file_menager.file_list) == 0:
            self.a_error_str.set("Nie wybrano plików do uśrednienia")
            return

        foldername = filedialog.askdirectory(
            title="Wybierz folder do zapisania pliku"
        ).replace("/", "\\")
        if foldername == "":
            self.a_error_str.set("Nie wybrano folderu do zapisu")
            return

        self.start_progress()

        thread = Thread(
            target=self.average_thread_fun,
            args=(foldername)
        )
        thread.start()

    def average_thread_fun(self, foldername):
        os.chdir(foldername)

        self.a_error_str.set("Trwa walidacja plików.\n"
                             "To może potrwać kilka minut.")
        self.file_menager.read_file(0)
        template = self.file_menager.readed_file

        for file in range(len(self.file_menager.file_list)):
            self.file_menager.read_file(file)
            if (
                    template.shape[0] != self.file_menager.readed_file.shape[0] or
                    template.shape[1] != self.file_menager.readed_file.shape[1] or
                    np.squeeze(template).ndim != np.squeeze(self.file_menager.readed_file).ndim
            ):
                self.a_error_str.set("Operacja niemożliwa, pliki mają różne rozdzielczości\n"
                                     "bądź są zapisane w różnych systemach barw")
                self.stop_progress()
                return
        self.a_error_str.set("Walidacja zakończona pomyślnie.\n"
                             "Trwa proces uśrednienia.")
        template = []

        if self.cores > len(self.file_menager.file_list):
            self.cores = len(self.file_menager.file_list)

        intervals = self.define_intervals()

        threads = []
        self.prepare_to_thread()

        if not self.weight_is_used:
            for i in range(self.cores):
                threads.append(
                    Thread(
                        target=self.file_menager.average_file,
                        args=(i, intervals[i][0], intervals[i][1])
                    )
                )
                threads[i].start()
        else:
            for i in range(self.cores):
                threads.append(
                    Thread(
                        target=self.file_menager.average_weight_file,
                        args=(i, intervals[i][0], intervals[i][1])
                    )
                )
                threads[i].start()

            weight_sum = 0
            for i in range(len(self.file_menager.average_data)):
                weight_sum += self.file_menager.average_data[i][1]

        for i in range(self.cores):
            threads[i].join()

        self.a_error_str.set("Łączę obrazy.")

        dim = np.squeeze(self.file_menager.thread_data[0]).ndim
        if dim == 3:
            self.file_menager.summary_file = np.full((
                len(self.file_menager.thread_data[0]),
                len(self.file_menager.thread_data[0][0]),
                len(self.file_menager.thread_data[0][0][0])
            ), 0
            )
            for i in range(self.cores):
                self.file_menager.summary_file += self.file_menager.thread_data[i]

            self.file_menager.thread_data = []
            self.file_menager.temporary_file = []

            if not self.weight_is_used:
                self.file_menager.summary_file = self.file_menager.summary_file / len(self.file_menager.file_list)
            else:
                self.file_menager.summary_file = self.file_menager.summary_file / weight_sum

            self.a_error_str.set("Obliczam jasność.")

            brightness = self.file_menager.summary_file.sum(axis=0).sum(axis=0)

            brightness = brightness / (
                        self.file_menager.summary_file.shape[0] * self.file_menager.summary_file.shape[1])
            brightness = (brightness / 256) * 100
            brightness_w = brightness.sum() / len(brightness)
            self.a_error_str.set(
                "Jasność ogólna: " + str(format(round(brightness_w, 2))) + "%\n"
                                                                           "Jasność czerwonego: " + str(
                    format(round(brightness[0], 2))) + "%\n"
                                                       "Jasność zielonego: " + str(
                    format(round(brightness[1], 2))) + "%\n"
                                                       "Jasność niebieski: " + str(
                    format(round(brightness[2], 2))) + "%"
            )

        elif dim == 2:
            self.file_menager.summary_file = np.full((
                len(self.file_menager.readed_file),
                len(self.file_menager.readed_file[0])), 0
            )
            for i in range(self.cores):
                self.file_menager.summary_file += self.file_menager.thread_data[i]

            if not self.weight_is_used:
                self.file_menager.summary_file = self.file_menager.summary_file / len(self.file_menager.file_list)
            else:
                self.file_menager.summary_file = self.file_menager.summary_file / weight_sum

            self.a_error_str.set("Obliczam jasność.")
            brightness_w = self.file_menager.summary_file.sum()
            brightness_w = brightness_w / (len(self.file_menager.summary_file) * len(self.file_menager.summary_file[0]))
            brightness_w = (brightness_w / 256) * 100
            self.a_error_str.set("Jasność ogólna: " + str(format(round(brightness_w))) + "%")

        self.file_menager.summary_file = self.file_menager.summary_file.astype('uint8')

        filename = foldername + "\\result.tif"
        self.file_menager.save_file(self.file_menager.summary_file, filename)

        self.weight_is_used = False
        self.file_menager.file_list.clear()
        self.file_menager.file_list.append(filename)
        self.file_counter.set(str(len(self.file_menager.file_list)))
        self.file_menager.read_file(0)
        self.file_width.set(str(self.file_menager.readed_file.shape[1]))
        self.file_height.set(str(self.file_menager.readed_file.shape[0]))
        self.file_menager.open_image(self.file_menager.file_list[0])
        self.stop_progress()
        self.create_weight_option()

    def filter_fun(self, min_w, max_w, min_r, max_r, min_g, max_g, min_b, max_b):
        self.f_error_str.set("")

        full: int = 100
        zero: int = 0
        if min_w == '':
            min_w = zero
        if min_r == '':
            min_r = zero
        if min_g == '':
            min_g = zero
        if min_b == '':
            min_b = zero
        if max_w == '':
            max_w = full
        if max_r == '':
            max_r = full
        if max_g == '':
            max_g = full
        if max_b == '':
            max_b = full

        if len(self.file_menager.file_list) == 0:
            self.f_error_str.set("Nie wybrano plików do filtrowania.")
            return

        if not (
                self.filter_by_white.get() or self.filter_by_red.get() or self.filter_by_green.get() or self.filter_by_blue.get()):
            self.f_error_str.set("Nie wybrano kanału do filtrowania.")
            return

        try:
            if self.filter_by_white.get():
                min_w = float(min_w)
                max_w = float(max_w)
            if self.filter_by_red.get():
                min_r = float(min_r)
                max_r = float(max_r)
            if self.filter_by_green.get():
                min_g = float(min_g)
                max_g = float(max_g)
            if self.filter_by_blue.get():
                min_b = float(min_b)
                max_b = float(max_b)
        except:
            self.f_error_str.set("Do ustalelnia minimum/maximum\nużyj liczb")
            return

        self.start_progress()

        thread = Thread(
            target=self.filter_thread_fun,
            args=(min_w, max_w, min_r, max_r, min_g, max_g, min_b, max_b)
        )
        thread.start()

    def filter_thread_fun(self, min_w, max_w, min_r, max_r, min_g, max_g, min_b,max_b):
        if self.cores > len(self.file_menager.file_list):
            self.cores = len(self.file_menager.file_list)

        intervals = self.define_intervals()

        threads = []

        self.prepare_to_thread()

        for i in range(self.cores):
            threads.append(Thread(
                target=self.file_menager.filter,
                args=(
                    self.filter_by_white.get(), self.filter_by_red.get(),
                    self.filter_by_green.get(), self.filter_by_blue.get(),
                    min_w, max_w, min_r, max_r, min_g, max_g, min_b, max_b,
                    intervals[i][0], intervals[i][1], i
                )))
            threads[i].start()

        for i in range(len(threads)):
            threads[i].join()

        self.file_menager.file_list = []
        for i in range(len(self.file_menager.filtered_file_list)):
            for j in range(len(self.file_menager.filtered_file_list[i])):
                self.file_menager.file_list.append(self.file_menager.filtered_file_list[i][j])

        self.f_error_str.set("Filtracja zakończona.")

        self.file_counter.set(str(len(self.file_menager.file_list)))
        self.create_weight_option()

        self.stop_progress()

    def threshold_fun(self, bound_w: int, bound_r: int, bound_g: int, bound_b: int):
        self.t_error_str.set("")
        check_w = self.is_thres_w.get()
        check_r = self.is_thres_r.get()
        check_g = self.is_thres_g.get()
        check_b = self.is_thres_b.get()

        if len(self.file_menager.file_list) == 0:
            self.t_error_str.set("Brak plików do sprogowania.")
            return

        if not (check_w or check_r or check_g or check_b):
            self.t_error_str.set("Nie wybrano kanału.")
            return

        foldername = filedialog.askdirectory(
            title="Wybierz folder do zapisania plików"
        ).replace("/", "\\")
        if foldername == "":
            self.t_error_str.set("Nie wybrano folderu do zapisu.")
            return

        self.start_progress()

        thread = (
            Thread(
                target=self.threshold_thread_fun,
                args=(bound_w, bound_r, bound_g, bound_b, foldername)
            )
        )
        thread.start()

    def threshold_thread_fun(self, bound_w: int, bound_r: int, bound_g: int, bound_b: int, foldername):
        os.chdir(foldername)
        check_w = self.is_thres_w.get()
        check_r = self.is_thres_r.get()
        check_g = self.is_thres_g.get()
        check_b = self.is_thres_b.get()

        if self.cores > len(self.file_menager.file_list):
            self.cores = len(self.file_menager.file_list)

        intervals = self.define_intervals()

        threads = []
        self.prepare_to_thread()

        for i in range(self.cores):
            threads.append(
                Thread(
                    target=self.file_menager.threshold,
                    args=(
                        check_w, bound_w, check_r, bound_r,
                        check_g, bound_g, check_b, bound_b,
                        intervals[i][0], intervals[i][1], i
                    )
                )
            )
            threads[i].start()

        for i in range(self.cores):
            threads[i].join()

        self.t_error_str.set("Sprogowano pomyślnie.")
        self.file_menager.open_image("threshold_" + str(len(self.file_menager.file_list) - 1) + ".tif")
        self.stop_progress()

    def get_image_file(self):
        self.file_menager.get_image_file()
        self.image_width.set(str(self.file_menager.image_file.size[0]))
        self.image_height.set(str(self.file_menager.image_file.size[1]))

    def save_files(self):
        self.s_error_str.set("")
        val = self.file_menager.save_files()
        if val == 1:
            self.s_error_str.set("Brak plików do zapisania.")
        elif val == 2:
            self.s_error_str.set("Nie wybrano folderu do\nzapisania plików.")
        elif val == 0:
            self.s_error_str.set("Pomyślnie zapisano pliki.")

    def tack_image_on(self, entry_x, entry_y,):
        self.i_error_str.set("")
        try:
            entry_x = int(entry_x)
            entry_y = int(entry_y)
        except:
            self.i_error_str.set("Do określenia odsunięcia od krawędzi\n"
                                 "użyj liczb naturalnych.")
            return
        if entry_x < 0 or entry_y < 0:
            self.i_error_str.set("Do określenia odsunięcia od krawędzi\n"
                                 "użyj liczb naturalnych.")
            return
        if not self.file_menager.image_file:
            self.i_error_str.set("Nie wybrano pliku do wklejenia.")
            return
        if (int(self.file_menager.image_file.size[0])+entry_x > int(self.file_menager.readed_file.shape[1]) or
            int(self.file_menager.image_file.size[1])+entry_y > int(self.file_menager.readed_file.shape[0])):
            self.i_error_str.set("Plik pierwszoplanowy nie zmieści się\n"
                                 "na pilku drugoplanowym")
            return
        if len(self.file_menager.file_list) == 0:
            self.i_error_str.set("Brak plików do doklejenia.")
            return
        foldername = filedialog.askdirectory(
            title="Wybierz folder do zapisania plików"
        ).replace("/", "\\")
        if foldername == "":
            self.i_error_str.set("Nie wybrano folderu do zapisu.")
            return

        self.start_progress()

        thread = Thread(
            target=self.tack_on_thread_fun,
            args=(entry_x, entry_y, foldername)
        )
        thread.start()

    def tack_on_thread_fun(self, entry_x, entry_y, foldername):
        if self.cores > len(self.file_menager.file_list):
            self.cores = len(self.file_menager.file_list)

        intervals = self.define_intervals()

        threads = []
        self.prepare_to_thread()

        for i in range(self.cores):
            threads.append(
                Thread(
                    target=self.file_menager.tack_image_on,
                    args=(
                        self.is_right.get(), entry_x,
                        self.is_top.get(), entry_y,
                        foldername, intervals[i][0], intervals[i][1]
                    )
                )
            )
            threads[i].start()

        for i in range(self.cores):
            threads[i].join()

        self.i_error_str.set("Pomyślnie zapisano pliki")
        self.file_menager.open_image("tack_on_" + str(len(self.file_menager.file_list) - 1) + ".tif")
        self.stop_progress()

    def define_intervals(self):
        forlist = np.arange(1, self.cores)
        intervals = []

        items = int(len(self.file_menager.file_list) / self.cores)
        intervals.append([0, items - 1])
        i = 0
        for i in forlist:
            intervals.append([intervals[i - 1][0] + items, intervals[i - 1][1] + items])
        if (len(self.file_menager.file_list) % self.cores) != 0:
            difference = len(self.file_menager.file_list) % self.cores
            intervals[i][1] += difference
        return intervals

    def prepare_to_thread(self):
        self.file_menager.read_file(0)
        dim = np.squeeze(self.file_menager.readed_file).ndim
        if dim == 3:
            self.file_menager.thread_data = np.full((
                self.cores,
                len(self.file_menager.readed_file),
                len(self.file_menager.readed_file[0]),
                len(self.file_menager.readed_file[0][0])), 0
            )
            self.file_menager.temporary_file = np.full((
                self.cores,
                len(self.file_menager.readed_file),
                len(self.file_menager.readed_file[0]),
                len(self.file_menager.readed_file[0][0])), 255
            )
            self.file_menager.brightness = np.full(3, 0)
        if dim == 2:
            self.file_menager.thread_data = np.full((
                self.cores,
                len(self.file_menager.readed_file),
                len(self.file_menager.readed_file[0])), 0
            )
            self.file_menager.temporary_file = np.full((
                self.cores,
                len(self.file_menager.readed_file),
                len(self.file_menager.readed_file[0])), 0
            )
        self.file_menager.brightness_w = 0

    def set_weight_data(self):
        self.file_menager.average_data = np.empty((len(self.file_menager.file_list), 2), dtype="object")
        for f in range(len(self.file_menager.file_list)):
            self.file_menager.average_data[f][0] = self.file_menager.file_list[f]
            self.file_menager.average_data[f][1] = 1

    def set_weight(self):
        self.a_error_str.set("")

        weight = 0
        try:
            weight = int(self.entry_weight.get())
            if weight == 0:
                self.a_error_str.set("Waga musi być liczbą naturalną.")
                return
        except:
            self.a_error_str.set("Waga musi być liczbą naturalną.")
            return

        if not self.weight_is_used:
            self.set_weight_data()
            self.weight_is_used = True

        for f in range(len(self.file_menager.average_data)):
            if self.file_menager.average_data[f][0] == self.weight_file.get():
                self.file_menager.average_data[f][1] = weight

    # Layout

    def __init__(self):
        button_frame = tk.LabelFrame(self.root, text="Wybór plików")
        file_button = tk.Button(button_frame, text="Wybierz plik", command=self.fill_file_list)
        self.buttons.append(file_button)
        folder_button = tk.Button(button_frame, text="Wybierz folder", command=self.fill_list_from_folder)
        self.buttons.append(folder_button)
        files_count = tk.Label(button_frame, textvariable=self.file_counter)

        filtering = tk.LabelFrame(self.root, text="Filtrowanie")
        check_filter = tk.Label(
            filtering, text="       Filtruj obrazy po średniej jasności w %       "
        )

        check_filter_w = tk.Checkbutton(
            filtering, text="biały", variable=self.filter_by_white,
            onvalue=True, offvalue=False
        )
        min_w = tk.Entry(filtering, width=5)
        max_w = tk.Entry(filtering, width=5)

        check_filter_r = tk.Checkbutton(
            filtering, text="czerwony", variable=self.filter_by_red,
            onvalue=True, offvalue=False
        )
        min_r = tk.Entry(filtering, width=5)
        max_r = tk.Entry(filtering, width=5)

        check_filter_g = tk.Checkbutton(
            filtering, text="zielony", variable=self.filter_by_green,
            onvalue=True, offvalue=False
        )
        min_g = tk.Entry(filtering, width=5)
        max_g = tk.Entry(filtering, width=5)

        check_filter_b = tk.Checkbutton(
            filtering, text="niebieski", variable=self.filter_by_blue,
            onvalue=True, offvalue=False
        )
        min_b = tk.Entry(filtering, width=5)
        max_b = tk.Entry(filtering, width=5)

        filter_error = tk.Label(filtering, textvariable=self.f_error_str)
        filter_button = tk.Button(
            filtering, text="Filtruj",
            command=lambda: self.filter_fun(
                min_w.get(), max_w.get(), min_r.get(), max_r.get(),
                min_g.get(), max_g.get(), min_b.get(), max_b.get()
            )
        )
        self.buttons.append(file_button)

        scale_length = 200
        threshold = tk.LabelFrame(self.root, text="Progowanie")
        bound_check_w = tk.Checkbutton(
            threshold, text="biały:", variable=self.is_thres_w,
            onvalue=True, offvalue=False
        )
        bound_white = tk.Scale(
            threshold, from_=1, to=255,
            orient="horizontal", length=scale_length
        )
        bound_check_r = tk.Checkbutton(
            threshold, text="czerwony:", variable=self.is_thres_r,
            onvalue=True, offvalue=False
        )
        bound_red = tk.Scale(
            threshold, from_=1, to=255,
            orient="horizontal", length=scale_length
        )
        bound_check_g = tk.Checkbutton(
            threshold, text="zielony:", variable=self.is_thres_g,
            onvalue=True, offvalue=False
        )
        bound_green = tk.Scale(
            threshold, from_=1, to=255,
            orient="horizontal", length=scale_length
        )
        bound_check_b = tk.Checkbutton(
            threshold, text="niebieski:", variable=self.is_thres_b,
            onvalue=True, offvalue=False
        )
        bound_blue = tk.Scale(
            threshold, from_=1, to=255,
            orient="horizontal", length=scale_length
        )
        thres_error = tk.Label(threshold, textvariable=self.t_error_str)
        thres_button = tk.Button(
            threshold, text="Proguj",
            command=lambda: self.threshold_fun(bound_white.get(), bound_red.get(), bound_green.get(), bound_blue.get())
        )
        self.buttons.append(thres_button)

        save_frame = tk.LabelFrame(self.root, text="Zapisz pliki")
        save_error = tk.Label(save_frame, textvariable=self.s_error_str)
        save_button = tk.Button(save_frame, text="Zapisz", command=self.save_files)
        self.buttons.append(save_button)

        image_frame = tk.LabelFrame(self.root, text="Dodaj obraz")
        file_width = tk.Label(image_frame, textvariable=self.file_width)
        file_height = tk.Label(image_frame, textvariable=self.file_height)
        image_width = tk.Label(image_frame, textvariable=self.image_width)
        image_height = tk.Label(image_frame, textvariable=self.image_height)
        radio_up = tk.Radiobutton(image_frame, variable=self.is_top, value=True, text="górnej")
        radio_down = tk.Radiobutton(image_frame, variable=self.is_top, value=False, text="dolnej")
        entry_x_pos = tk.Entry(image_frame, width=5)
        radio_right = tk.Radiobutton(image_frame, variable=self.is_right, value=True, text="prawej")
        radio_left = tk.Radiobutton(image_frame, variable=self.is_right, value=False, text="lewej")
        entry_y_pos = tk.Entry(image_frame, width=5)
        image_label = tk.Label(image_frame, textvariable=self.i_error_str)
        image_button = tk.Button(image_frame, text="Wybierz obraz",command=self.get_image_file)
        self.buttons.append(image_button)
        tack_on_button = tk.Button(
            image_frame, text="Doklej",
            command=lambda: self.tack_image_on(entry_x_pos.get(), entry_y_pos.get())
        )
        self.buttons.append(tack_on_button)

        # average_frame
        average_error = tk.Label(self.average_frame, textvariable=self.a_error_str)
        average_button = tk.Button(
            self.average_frame, text="Uśrednij",
            command=self.average_file
        )
        self.buttons.append(average_button)

        # Grid
        button_frame.grid(row=0, column=0, rowspan=4, padx=5, pady=5, sticky="N")
        file_button.grid(row=0, column=0, columnspan=4, padx=5, pady=5)
        tk.Label(button_frame, text="lub").grid(row=0, column=4)
        folder_button.grid(row=0, column=5, columnspan=4, padx=5, pady=5)
        tk.Label(button_frame, text="Liczba plików:").grid(row=1, column=0, padx=5, pady=5)
        files_count.grid(row=1, column=4, padx=5, pady=5)

        save_frame.grid(row=4, column=0, padx=5, pady=5, sticky="N", rowspan=4)
        save_error.grid(row=0, column=0, padx=10)
        save_button.grid(row=1, column=0, padx=50, pady=10)

        filtering.grid(row=8, column=0, padx=5, pady=5, rowspan=4)
        check_filter.grid(row=1, column=0, columnspan=9)
        check_filter_w.grid(row=2, column=0, columnspan=3, sticky="W")
        tk.Label(filtering, text="min").grid(row=2, column=4)
        min_w.grid(row=2, column=5)
        tk.Label(filtering, text="max").grid(row=2, column=6)
        max_w.grid(row=2, column=7)

        check_filter_r.grid(row=3, column=0, columnspan=3, sticky="W")
        tk.Label(filtering, text="min").grid(row=3, column=4)
        min_r.grid(row=3, column=5)
        tk.Label(filtering, text="max").grid(row=3, column=6)
        max_r.grid(row=3, column=7)

        check_filter_g.grid(row=4, column=0, columnspan=3, sticky="W")
        tk.Label(filtering, text="min").grid(row=4, column=4)
        min_g.grid(row=4, column=5)
        tk.Label(filtering, text="max").grid(row=4, column=6)
        max_g.grid(row=4, column=7)

        check_filter_b.grid(row=5, column=0, columnspan=3, sticky="W")
        tk.Label(filtering, text="min").grid(row=5, column=4)
        min_b.grid(row=5, column=5)
        tk.Label(filtering, text="max").grid(row=5, column=6)
        max_b.grid(row=5, column=7)
        filter_error.grid(row=6, column=0, columnspan=9, padx=5, pady=5)
        filter_button.grid(row=7, column=0, columnspan=9, padx=5, pady=5)

        threshold.grid(row=0, column=1, padx=5, pady=5, rowspan=8)
        bound_check_w.grid(row=1, column=0, sticky="W")
        bound_white.grid(row=1, column=2, padx=5, pady=5)
        bound_check_r.grid(row=2, column=0, sticky="W")
        bound_red.grid(row=2, column=2, padx=5, pady=5)
        bound_check_g.grid(row=3, column=0, sticky="W")
        bound_green.grid(row=3, column=2, padx=5, pady=5)
        bound_check_b.grid(row=4, column=0, sticky="W")
        bound_blue.grid(row=4, column=2, padx=5, pady=5)
        thres_error.grid(row=6, column=0, pady=5, columnspan=3)
        thres_button.grid(row=7, column=0, pady=5, columnspan=3)

        image_frame.grid(row=0, column=2, padx=5, pady=5, rowspan=8, sticky="N")
        tk.Label(image_frame, text="Rozdzielczość obrazu docelowego:").grid(
            row=0, column=0, padx=5, pady=5, sticky="W", columnspan=3
        )
        file_width.grid(row=0, column=4, padx=5, pady=5)
        tk.Label(image_frame, text="x").grid(row=0, column=5)
        file_height.grid(row=0, column=6, padx=5, pady=5)
        tk.Label(image_frame, text="Rozdzielczość obrazu doklejanego:").grid(
            row=1, column=0, padx=5, pady=5, sticky="W", columnspan=3
        )
        image_width.grid(row=1, column=4, padx=5, pady=5)
        tk.Label(image_frame, text="x").grid(row=1, column=5)
        image_height.grid(row=1, column=6, padx=5, pady=5)
        tk.Label(image_frame, text="Odsunięcie od krawędzi:").grid(
            row=2, column=0, padx=5, pady=5, columnspan=7
        )
        radio_right.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="W")
        radio_left.grid(row=3, column=2, columnspan=2, padx=5, pady=5, sticky="W")
        entry_x_pos.grid(row=3, column=4, columnspan=3, padx=15, pady=5, sticky="E")
        tk.Label(image_frame, text="Odsunięcie od krawędzi:").grid(
            row=4, column=0, padx=5, pady=5, columnspan=7
        )
        radio_up.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="W")
        radio_down.grid(row=5, column=2, columnspan=2, padx=5, pady=5, sticky="W")
        entry_y_pos.grid(row=5, column=4, columnspan=3, padx=15, pady=5, sticky="E")
        image_label.grid(row=6, column=0, padx=5, pady=5, columnspan=4)
        image_button.grid(row=6, column=4, padx=5, pady=5, columnspan=3)
        tack_on_button.grid(row=7, column=0, padx=5, pady=5, columnspan=9)

        self.average_frame.grid(row=8, column=1, padx=5, pady=5, columnspan=2, rowspan=4)
        average_error.grid(row=2, column=0, padx=20, pady=5, columnspan=3)
        average_button.grid(row=3, column=0, padx=50, pady=10, columnspan=3)

        self.progress_bar.grid(row=25, column=0, columnspan=3, pady=5, padx=5)

        # Init values
        self.file_counter.set("0")
        self.file_width.set("0")
        self.file_height.set("0")
        self.image_width.set("0")
        self.image_height.set("0")

        self.is_thres_w.set(False)
        self.is_thres_r.set(False)
        self.is_thres_g.set(False)
        self.is_thres_b.set(False)
        self.filter_by_white.set(False)
        self.filter_by_red.set(False)
        self.filter_by_green.set(False)
        self.filter_by_blue.set(False)

        self.root.mainloop()
