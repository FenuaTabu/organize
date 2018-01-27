import glob
import os
import sys
import shutil

is_windows = hasattr(sys, 'getwindowsversion')

if is_windows:
    list_rep_organize = ["C:/Users/"+os.getlogin()+"/Downloads/", ]
    base_path_nas = "S:/"
else:
    list_rep_organize = ["", ]
    base_path_nas = "/volume2/NAS/"


class File_Organise:
    path_dest = ""

    def __init__(self, p):
        self.p = p
        self.path_dest = base_path_nas + self.path_dest

    def rename(self, p):
        return p

    def organize(self):
        print(self.p + " -> " + self.path_dest + self.rename(os.path.basename(self.p)))
        shutil.copy(self.p, self.path_dest + self.rename(os.path.basename(self.p)))


class File_Pdf(File_Organise):

    def rename(self, p):
        return p


class File_Book_Bd(File_Organise):
    path_dest = "book/BD/"

    def rename(self, p):
        return p


class Organize:
    file_all = []

    def __init__(self):
        self.list_file()
        self.core()

    def core(self):
        for p in self.file_all:
            filename, file_extension = os.path.splitext(p)
            with open(p, 'rb') as pb:
                header = tuple([int(o) for o in pb.read(4)])

                # PDF
                if header == (0x25, 0x50, 0x44, 0x46) and file_extension.lower() == ".pdf":
                    # File_Pdf(p).organize()
                    # print("PDF - "+p)
                    pass

                # CBZ
                if header == (0x50, 0x4B, 0x03, 0x04) and file_extension.lower() == ".cbz":
                    File_Book_Bd(p).organize()
                    # print("CBZ - " + p)

                # CBR
                if file_extension.lower() == ".cbr":
                    File_Book_Bd(p).organize()

    def list_file(self):
        for rep_organize in list_rep_organize:
            for p in glob.glob(rep_organize + "\\*"):
                if os.path.isfile(p):
                    self.file_all.append(p)


if __name__ == '__main__':
    organize = Organize()
