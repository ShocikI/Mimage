import os
from tkinter import filedialog
import numpy as np
from PIL import Image
from skimage import io


class FileMenager:
    file_list = []
    filtered_file_list = []
    image_file = []
    readed_file = []
    summary_file = []
    thread_data = []
    temporary_file = []
    average_data = []

    def fill_file_list(self):
        try:
            files = filedialog.askopenfilenames()
            if files == "":
                return 1
        except:
            return 1
        file_list = list(files)
        for i in range(len(file_list)):
            f = file_list[i]
            if (
                    f.endswith(".jpg") or
                    f.endswith(".tif") or
                    f.endswith(".png") or
                    f.endswith(".jpeg") or
                    f.endswith(".tiff")
            ):
                self.file_list.append(str(file_list[i]))

    def fill_list_from_folder(self):
        self.file_list.clear()
        try:
            folder_name = filedialog.askdirectory().replace("/", "\\")
            if folder_name == "":
                return 1
        except:
            return 1
        os.chdir(folder_name)
        file_list = list(os.listdir())
        for i in range(len(file_list)):
            f = file_list[i]
            if (
                    f.endswith(".jpg") or
                    f.endswith(".tif") or
                    f.endswith(".png") or
                    f.endswith(".jpeg") or
                    f.endswith(".tiff")
            ):
                self.file_list.append(str(os.getcwd()+"\\"+str(file_list[i])))

    def read_file(self, x: int):
        self.readed_file = io.imread(self.file_list[x])

    def read_file_by_path(self, path: str, thread_num: int):
        self.temporary_file[thread_num] = io.imread(path)

    def read_file_to_temporary(self, x: int, thread_num: int):
        self.temporary_file[thread_num] = io.imread(self.file_list[x])

    def get_image_file(self):
        self.image_file = []
        path = filedialog.askopenfilename()
        if path and (
            path.endswith(".jpg") or
            path.endswith(".tif") or
            path.endswith(".png") or
            path.endswith(".jpeg") or
            path.endswith(".tiff")
        ):
            self.image_file = Image.open(path)

    def open_image(self, file: str):
        os.startfile(file)

    # Generate functions
    def average_file(self, thread_num, start, stop):
        if start < stop:
            interval = np.arange(start, stop+1)
        else:
            interval = [start]

        for f in interval:
            self.read_file_to_temporary(f, thread_num)
            self.thread_data[thread_num] += self.temporary_file[thread_num]

    def average_weight_file(self, thread_num, start, stop):
        if start < stop:
            interval = np.arange(start, stop+1)
        else:
            interval = [start]

        for f in interval:
            self.read_file_by_path(self.average_data[f][0], thread_num)
            self.thread_data[thread_num] += (self.temporary_file[thread_num] * self.average_data[f][1])

    def filter(
            self, check_w, check_r, check_g, check_b,
            min_w, max_w, min_r, max_r,
            min_g, max_g, min_b, max_b,
            start, stop, thread_num
    ):
        filtered_file_list = []
        if start < stop:
            interval = np.arange(start, stop + 1)
        else:
            interval = [start]

        for i in interval:
            add_to_filter = False
            brightness_w = 0.0

            self.read_file_to_temporary(i, thread_num)
            dim = np.squeeze(self.temporary_file[thread_num]).ndim
            if dim == 3:
                brightness = self.temporary_file[thread_num].sum(axis=0).sum(axis=0)
                if check_r or check_w:
                    brightness[0] = brightness[0] / (self.temporary_file.shape[1] * self.temporary_file.shape[2])
                    brightness[0] = (brightness[0] / 256) * 100
                if check_g or check_w:
                    brightness[1] = brightness[1] / (self.temporary_file.shape[1] * self.temporary_file.shape[2])
                    brightness[1] = (brightness[1] / 256) * 100
                if check_b or check_w:
                    brightness[2] = brightness[2] / (self.temporary_file.shape[1] * self.temporary_file.shape[2])
                    brightness[2] = (brightness[2] / 256) * 100
                if check_w:
                    brightness_w = ((brightness[0] + brightness[1] + brightness[2]) / 3)
                    if min_w <= brightness_w <= max_w:
                        add_to_filter = True
                    else:
                        add_to_filter = False
                if check_r:
                    if min_r <= brightness[0] <= max_r:
                        add_to_filter = True
                    else:
                        add_to_filter = False
                if check_g:
                    if min_g <= brightness[1] <= max_g:
                        add_to_filter = True
                    else:
                        add_to_filter = False
                if check_b:
                    if min_b <= brightness[2] <= max_b:
                        add_to_filter = True
                    else:
                        add_to_filter = False

                if add_to_filter:
                    filtered_file_list.append(self.file_list[i])

            if dim == 2:
                if check_w:
                    self.read_file_to_temporary(i, thread_num)
                    brightness_w = self.temporary_file[thread_num].sum()
                    brightness_w = brightness_w / (self.temporary_file.shape[1] * self.temporary_file.shape[2])
                    brightness_w = (brightness_w / 256) * 100
                    if min_w < brightness_w < max_w:
                        filtered_file_list.append(self.file_list[i])
        self.filtered_file_list.append(filtered_file_list)

    def threshold(
            self, check_w: bool, bound_w: int, check_r: bool, bound_r: int,
            check_g: bool, bound_g: int, check_b: bool, bound_b: int,
            start, stop, thread_num
    ):
        if start < stop:
            interval = np.arange(start, stop+1)
        else:
            interval = [start]
        self.thread_data = []
        for f in interval:
            self.read_file_to_temporary(f, thread_num)
            dim = np.squeeze(self.temporary_file[thread_num]).ndim
            if dim == 3:
                if check_w:
                    white_list: float = 0.0
                    for x in range(len(self.temporary_file[thread_num])):
                        for y in range(len(self.temporary_file[thread_num][x])):
                            for z in range(len(self.temporary_file[thread_num][x][y])):
                                white_list += self.temporary_file[thread_num][x][y][z]
                            white_list = white_list / len(self.temporary_file[thread_num][x][y])
                            if white_list >= bound_w:
                                self.temporary_file[thread_num][x][y][0] = 255
                                self.temporary_file[thread_num][x][y][1] = 255
                                self.temporary_file[thread_num][x][y][2] = 255

                elif check_r or check_g or check_b:
                    for x in range(len(self.temporary_file[thread_num])):
                        for y in range(len(self.temporary_file[thread_num][x])):
                            if check_r and self.temporary_file[thread_num][x][y][0] >= bound_r:
                                self.temporary_file[thread_num][x][y][0] = 255
                            if check_g and self.temporary_file[thread_num][x][y][1] >= bound_g:
                                self.temporary_file[thread_num][x][y][1] = 255
                            if check_b and self.temporary_file[thread_num][x][y][2] >= bound_b:
                                self.temporary_file[thread_num][x][y][2] = 255

            elif dim == 2:
                if check_w:
                    for x in range(len(self.temporary_file[thread_num])):
                        for y in range(len(self.temporary_file[thread_num][x])):
                            if self.temporary_file[thread_num][x][y] >= bound_w:
                                self.temporary_file[thread_num][x][y] = 255

            filename = "threshold_" + str(f) + ".tif"
            self.save_file(self.temporary_file[thread_num], str(filename))

    def tack_image_on(
            self, is_right, entry_x, is_top, entry_y,
            foldername, start, stop
    ):
        os.chdir(foldername)
        if start < stop:
            interval = np.arange(start, stop+1)
        else:
            interval = [start]
        for f in interval:
            temporary_file = Image.open(self.file_list[f])
            if not is_right:
                pos_x = entry_x
            else:
                pos_x = temporary_file.size[0] - (entry_x + self.image_file.size[0])
            if is_top:
                pos_y = entry_y
            else:
                pos_y = temporary_file.size[1] - (entry_y + self.image_file.size[1])

            if (self.image_file.size[0] + pos_x <= temporary_file.size[0] or
                self.image_file.size[1] + pos_y <= temporary_file.size[1]):
                if self.image_file.mode == 'RGBA':
                    temporary_file.paste(self.image_file, (pos_x, pos_y), self.image_file)
                    temporary_file.save("tack_on_" + str(f) + ".tif")
                else:
                    temporary_file.paste(self.image_file, (pos_x, pos_y))
                    temporary_file.save("tack_on_" + str(f) + ".tif")
            else:
                pass
        return 0

    # Save function
    @staticmethod
    def save_file(file, filename: str):
        file = file.astype('uint8')
        io.imsave(filename, file, check_contrast=False)

    def save_files(self):
        if len(self.file_list) == 0:
            return 1
        try:
            foldername = filedialog.askdirectory(
                title="Wybierz folder do zapisania plików"
            ).replace("/", "\\")
            if foldername == "":
                return 2
        except:
            return 2
        os.chdir(foldername)

        for i in range(len(self.file_list)):
            self.read_file(i)
            self.save_file(self.readed_file, str(os.path.split(self.file_list[i])[1]))
        return 0
