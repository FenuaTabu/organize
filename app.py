import glob
import os
import sys
import shutil
import filecmp
import struct
import zipfile

is_windows = hasattr(sys, 'getwindowsversion')

if is_windows:
    list_rep_organize = ["C:/Users/"+os.getlogin()+"/Downloads/", ]
    base_path_nas = "S:/"
else:
    list_rep_organize = ["", ]
    base_path_nas = "/volume2/NAS/"


class File_Organise:
    dest_path = ""
    new_file = ""

    def __init__(self, src_full_path):
        self.src_path = os.path.dirname(src_full_path)+"/"
        self.src_file = os.path.basename(src_full_path)
        self.dest_path = base_path_nas + self.dest_path
        self.dest_file = self.src_file

    def rename(self):
        return self.src_file

    def organize(self):
        print(self.src_path+self.src_file+" -> "+self.dest_path+self.path_dest+self.rename())
        #shutil.copy(self.src_file, self.dest_path + self.rename())


class File_Pdf(File_Organise):
    pass


class File_Book_Bd(File_Organise):
    path_dest = "book/BD/"
    pass


class File_Vpk(File_Organise):
    path_dest = "jeux/Vita/"

    def rename(self):
        try:
            with zipfile.ZipFile(self.src_path+self.src_file, 'r') as vpk:
                param_path = "sce_sys/param.sfo"

                if param_path not in vpk.namelist():
                    param_path = None
                    for subfile in vpk.namelist():
                        # Search for param.sfo
                        if subfile.endswith("param.sfo"):
                            param_path = subfile
                            break

                if not param_path:
                    print("Probleme param.sfo dans %s".format(p))
                    return p

                # Read param.sfo
                param_data = vpk.read(param_path)

                key_offset, data_offset = struct.unpack("<II", param_data[0x08:0x10])
                keys = param_data[key_offset:data_offset].strip(b'\0').split(b'\0')

                def get_data(key):
                    if key not in keys:
                        return None

                    info_offset = 0x14 + (keys.index(key) * 0x10)
                    len, _, offset = struct.unpack("<III", param_data[info_offset + 0x04: info_offset + 0x10])
                    return param_data[data_offset + offset:data_offset + offset + len]

                title = get_data(b"TITLE").strip(b'\0').strip().decode('utf-8')
                title_id = get_data(b"TITLE_ID").strip(b'\0').strip().decode('utf-8')
                version = get_data(b"APP_VER").strip(b'\0').strip().decode('utf-8')

                if not title:
                    print("Could not find title of game")
                    exit(-1)

                region = None
                if "PCSB" in title_id or "PCSF" in title_id:
                    region = "EUR"
                elif "PCSE" in title_id or "PCSA" in title_id:
                    region = "USA"
                elif "PCSG" in title_id or "PCSC" in title_id:
                    region = "JPN"
                else:
                    region = "UNK"

            new_filename_base = "%s" % title
            if title_id:
                new_filename_base = "%s [%s]" % (new_filename_base, title_id)
            if version:
                new_filename_base = "%s (v%s)" % (new_filename_base, version)
            if region:
                new_filename_base = "%s (%s)" % (new_filename_base, region)

            # Remove invalid characters from filename in the ASCII range
            invalid_chars = u'™©®"<>|:*?\\/'
            new_filename_base = ''.join('_' if (ord(c) > 0x7f) else c for c in new_filename_base if (c not in invalid_chars and ord(c) >= 0x20))
            new_filename = "%s.%s" % (new_filename_base, "vpk")

            # Check if the files are the same
            # A simple filename comparison does not work because of encoding issues unfortunately
            # And such a check is required for when 2 VPKs are required because they will return the same name
            dupe = 1
            while os.path.exists(new_filename) and not filecmp.cmp(self.src_file, new_filename):
                new_filename = "%s (%d).%s" % (new_filename_base, dupe, "vpk")
                dupe += 1
            #new_filename = new_filename.encode(args.charset, errors='ignore')

            # Rename VPK file
            return new_filename

        except zipfile.BadZipfile:
            return self.src_file


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

                # VPK
                if file_extension.lower() == ".vpk":
                    File_Vpk(p).organize()

    def list_file(self):
        for rep_organize in list_rep_organize:
            for p in glob.glob(rep_organize + "\\*"):
                if os.path.isfile(p):
                    self.file_all.append(p)


if __name__ == '__main__':
    organize = Organize()
