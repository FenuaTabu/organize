# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys
import re
import shutil
import time
import zipfile
import filecmp
import struct
import glob
from mylibs.mycore import MyCore
from mylibs.mycore import MyOs
from mylibs.mycore import MyStr
from mylibs.mycore import MyFile
from mylibs.mycore import MyCli
from mylibs.mycore import MyLog
from mylibs.mycore import MyConfig
from mylibs import convert
from PIL import ExifTags, Image


root_path = os.path.dirname(os.path.abspath(__file__))+'/'
log = MyLog(root_path + 'log.txt')

class Config(MyConfig):
    is_valid = True
    
    def on_load(self):
        self.app = self.datas.get('app', None)
        if self.app is not None:
            self.app_env = self.app.get('env', 'dev').lower()
            self.app_list_path_organize = self.app.get('list_path_organize', [])
            self.app_suffix = self.app.get('suffix', '')
            self.app_space = self.app.get('space', ' ')
            self.app_path_in_process = self.app.get('path_in_process', None)
            self.app_path_reject = self.app.get('path_reject', None)
            self.app_path_doublon = self.app.get('path_doublon', None)
            self.app_ws_ocr_url = self.app.get('ws_ocr_url', None)
            self.app_ws_debug = self.app.get('ws_debug', '0')
            self.app_ws_gray = self.app.get('ws_gray', '0')
        self.valid_config()
    
    def valid_config(self):
        if self.app is not None:
            list_env = ['dev', 'prod']
            if self.app_env.lower() not in list_env:
                log.error("CONFIG - [ENV] "+','.join(list_env))
                sys.exit()
            for arg in sys.argv:
                if arg == "prod":
                    self.app_env = "prod"
            if self.app_path_in_process is not None:
                if not(os.path.isdir(self.app_path_in_process)):
                    log.success(self.app_path_in_process)
                    os.makedirs(self.app_path_in_process)
            if self.app_path_reject is not None:
                if not(os.path.isdir(self.app_path_reject)):
                    log.success(self.app_path_reject)
                    os.makedirs(self.app_path_reject)
            if self.app_path_doublon is not None:
                if not(os.path.isdir(self.app_path_doublon)):
                    log.success(self.app_path_doublon)
                    os.makedirs(self.app_path_doublon)
            if not self.app_ws_debug.isdigit():
                self.app_ws_debug = '0'
            if not self.app_ws_gray.isdigit():
                self.app_ws_gray = '0'


config = Config()
def run():
    config.load(root_path+'config.yml')
    Organize()

class Organize:
    def __init__(self):
        self.file_all = []
        if not self.is_file_in_process():
            self.list_file()
            self.core()
        else:
            log.error("Fichier(s) dans : " + config.app_path_in_process)

    def core(self):
        for p in self.file_all:
            filename, file_extension = os.path.splitext(p)
            
            for modele_title in config.datas['ext']:
                for modele_ext in config.datas['ext'][modele_title]['ext']:
                    if file_extension.lower() == modele_ext:
                        pass
            
            if config.app_env == "dev":
                MyCore.debug(filename+file_extension)
                
            # PDF
            if file_extension.lower() == ".pdf":
                File_Pdf(p).organize()

            # CBZ CBR
            if file_extension.lower() in [".cbz", "*.cbr"]:
                File_Book_Bd(p).organize()

            # VPK
            if file_extension.lower() == ".vpk":
                File_Vpk(p).organize()

            # JPG JPEG
            if file_extension.lower() in [".jpg", "jpeg"]:
                File_Jpg(p).organize()
                
            # AVI MKV
            if file_extension.lower() in [".mkv", "avi"]:
                File_Mkv(p).organize()
                
            if config.app_env == "dev":
                print("\n")

    def is_file_in_process(self):
        cpt = MyOs.count_file(config.app_path_in_process)
        if cpt > 0:
            return True
        else:
            return False
            
    def list_file(self):
        for rep_organize in config.app_list_path_organize:
            for p in glob.glob(rep_organize + "/*"):
                if os.path.isfile(p):
                    if os.path.basename(p).lower() not in  ["thumbs.db",]:
                        if config.app_env == "prod":
                            shutil.move(p, config.app_path_in_process+os.path.basename(p))
                            self.file_all.append(config.app_path_in_process+os.path.basename(p))
                        else:
                            self.file_all.append(p)


class File_Organise(object):
    def __init__(self, src_full_path):
        self.dest_path = ""
        self.dest_file = ""
        self.src_path = os.path.dirname(src_full_path)+"/"
        self.src_file = os.path.basename(src_full_path)
        self.ls_debug = []
        
    def rename(self):
        return self.src_file
        
    def to_debug(self, msg, status=''):
        if msg is not None:
            if config.app_env == "dev":
                MyCore.debug(msg, status)
            self.ls_debug.append(status+'|'+msg)
        
    def to_log(self, msg, status=''):
        log.message(msg, status)
    
    def dest_fullpath(self):
        return self.dest_path+self.dest_file
    
    def src_fullpath(self):
        return self.src_path+self.src_file
    
    def to_reject_sp(self):
        pass
        
    def to_reject(self):
        if config.app_env == "prod" and config.app_path_reject is not None:
            if not(os.path.isdir(config.app_path_reject+self.src_file)):
                os.makedirs(config.app_path_reject+self.src_file)
                shutil.move(self.src_fullpath(), config.app_path_reject+self.src_file+'/'+self.src_file)
                self.to_reject_sp()
                MyFile.write(self.ls_debug, config.app_path_reject+self.src_file+'/log.txt')
                log.success('Rejet - '+self.src_fullpath())
    
    def to_doublon(self):
        if config.app_env == "prod" and config.app_path_doublon is not None:
            shutil.move(self.src_fullpath(), config.app_path_doublon+self.src_file)
            log.success('Doubl - '+self.src_fullpath())

    def organize(self):
        self.dest_file = self.rename()
        if self.dest_file is not None:
            self.dest_path = convert.str_transliterate(self.dest_path)
            self.dest_file = MyStr.valid_filename(self.dest_file)
            self.dest_file = re.sub(" ", config.app_space, self.dest_file)
            
            if not os.path.exists(self.dest_fullpath()):
                if config.app_env == "prod":
                    if not(os.path.isdir(os.path.dirname(self.dest_fullpath()))):
                        os.makedirs(os.path.dirname(self.dest_fullpath()))
                        log.success('mkdir '+os.path.dirname(self.dest_fullpath()))
                    shutil.move(self.src_fullpath(), self.dest_fullpath())
                self.to_log('Renommer '+self.src_fullpath()+" -> "+self.dest_fullpath(), 'OK')
            else:
                src_size = os.path.getsize(self.src_fullpath())
                dest_size = os.path.getsize(self.dest_fullpath())
                if src_size == dest_size:
                    log.warning("Le fichier existe deja, meme taille "+self.dest_fullpath())
                    self.to_doublon()
                else:
                    self.to_log("Le fichier existe deja, taille differente "+self.dest_fullpath(), 'WARN')
                    self.to_reject()
        else:
            self.to_log("Impossible de generer le nouveau nom de fichier "+self.src_fullpath(), 'WARN')
            self.to_reject()
    
class File_Vpk(File_Organise):
    def __init__(self, src_full_path):
        super().__init__(src_full_path)
        self.dest_path = config.datas['ext']['vpk']['dest_path']


    def rename(self, src_path, src_file):
        try:
            with zipfile.ZipFile(src_path+src_file, 'r') as vpk:
                param_path = "sce_sys/param.sfo"
    
                if param_path not in vpk.namelist():
                    param_path = None
                    for subfile in vpk.namelist():
                        # Search for param.sfo
                        if subfile.endswith("param.sfo"):
                            param_path = subfile
                            break
                param_data = vpk.read(param_path)
    
                key_offset, data_offset = struct.unpack("<II", param_data[0x08:0x10])
                keys = param_data[key_offset:data_offset].strip(b'\0').split(b'\0')
    
                def get_data(key):
                    if key not in keys:
                        return None
    
                    info_offset = 0x14 + (keys.index(key) * 0x10)
                    lenn, _, offset = struct.unpack("<III", param_data[info_offset + 0x04: info_offset + 0x10])
                    return param_data[data_offset + offset:data_offset + offset + lenn]
    
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
            while os.path.exists(new_filename) and not filecmp.cmp(src_file, new_filename):
                new_filename = "%s (%d).%s" % (new_filename_base, dupe, "vpk")
                dupe += 1
            #new_filename = new_filename.encode(args.charset, errors='ignore')
    
            # Rename VPK file
            return new_filename
    
        except zipfile.BadZipfile:
            return None

class File_Book_Bd(File_Organise):
    def __init__(self, src_full_path):
        super().__init__(src_full_path)
        self.dest_path = config.datas['ext']['bd']['dest_path']

class File_Jpg(File_Organise):
    def __init__(self, src_full_path):
        super().__init__(src_full_path)
        self.dest_path = config.datas['ext']['jpg']['dest_path']
        self.new_fullpath = config.datas['ext']['jpg']['fullpath']
    
    def rename(self): 
        new_fullpath = ''
        exif = Image.open(self.src_fullpath())._getexif()
        if exif is not None:
            for tag, value in exif.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                if decoded == "DateTime":
                    try:
                        datetime = time.strptime(value, "%Y:%m:%d %H:%M:%S")
                        self.new_fullpath = self.new_fullpath.replace("{$yyyy}", "%Y")
                        self.new_fullpath = self.new_fullpath.replace("{$mm}", "%m")
                        self.new_fullpath = self.new_fullpath.replace("{$mmm}", convert.mm_to_mmm("{:02}".format(datetime[1])))
                        self.new_fullpath = self.new_fullpath.replace("{$src_filename}", os.path.basename(self.src_fullpath()))
                        return time.strftime(self.new_fullpath, datetime)
                    except ValueError:
                        return None
        return None;
    
    
class File_Mkv(File_Organise):
    def rename(self): 
        import imdb
        self.dest_path = config.datas['ext']['mkv']['dest_path']
        tmp_filename = self.src_file
        ls_words = ["ws", "bluray", "french", "light", "x264", "720p", "ac3",\
                    "ac3-acool", "acool", "zone-telechargement", "zone-telechargement1",\
                    "com", "ac3-sharks", "ec", "hdlight", "wawacity", "ec"]
        for w in ls_words:
            tmp_filename = re.sub("\."+w+"\.", ".", tmp_filename, flags=re.IGNORECASE)

        filename, file_extension = os.path.splitext(tmp_filename)
        filename = filename.replace(".", " ")
        
        self.to_debug(filename, "clean")
        ia = imdb.IMDb()
        movies = ia.search_movie(filename)
        try:
            m = movies[0]
        except IndexError:
            return None
        
        new_fullpath = config.datas['ext']['mkv']['fullpath']
        new_fullpath = new_fullpath.replace("{$dest_filename}", m["title"])
        new_fullpath = new_fullpath.replace("{$year}", str(m["year"]))
        new_fullpath = convert.str_transliterate(new_fullpath)
        
        if config.app_env == "dev":
            self.to_debug(new_fullpath, "Titre")
        return new_fullpath+file_extension;

class File_Pdf(File_Organise):
    def __init__(self, src_full_path):
        super(File_Pdf,self).__init__(src_full_path)
        self.dest_path = config.datas['ext']['pdf']['dest_path']
        self._transcodings = {}
        self._vars = {}
        self._params = {}
        self.try_ws_ocr = False
    
    def clean_ocr(self, ocr):
        tmp = ocr.strip()
        tmp = re.sub('[\n\r\t]', " ", tmp)
        tmp = convert.str_transliterate(tmp)
        tmp = re.sub("[  ]+", " ", tmp)
        return tmp
        
    def load_vars(self, model, version):
        try:
            for ls_var in config.datas['ext']['pdf']['models'][model]['versions'][version]['vars']:
                var = config.datas['ext']['pdf']['models'][model]['versions'][version]['vars'][ls_var]
                self._vars[ls_var] = var
        except KeyError:
            pass
    
    def load_transcoding(self, model):
        try:
            for transco in config.datas['ext']['pdf']['transcodings']:
                for key, value in transco.items():
                    self._transcodings[key] = value
        except KeyError:
            pass
        
        try:
            for transco in config.datas['ext']['pdf']['models'][model]['transcodings']:
                for key, value in transco.items():
                    self._transcodings[key] = value
        except KeyError:
            pass
        
    def load_param_format_value(self, param, model, version=None):
        try:
            if version is not None:
                return config.datas['ext']['pdf']['models'][model]['versions'][version]['params'][param]['format_value']
            else:
                return config.datas['ext']['pdf']['models'][model]['params'][param]['format_value']
        except KeyError:
            return None
            
    def load_param_default_value(self, param, model, version=None):
        try:
            if version is not None:
                return config.datas['ext']['pdf']['models'][model]['versions'][version]['params'][param]['default_value']
            else:
                return config.datas['ext']['pdf']['models'][model]['params'][param]['default_value']
        except KeyError:
            return None
            
    def process_param(self, param, pattern, format_value, default_value):
        p_key = None
        p_value = None
        p_num = 0
        
        # DATE
        match_date = re.search('p_date_(?P<p_num>\d{1})', param)
        if match_date:
            p_num = match_date.group('p_num')
            p_key = "{$p_date_"+p_num+"}"
            if p_key not in self._params.keys():
                p_value = self.g_p_date(pattern, format_value, default_value)
            else:
                return False
        # STR
        match_str = re.search('p_str_(?P<p_num>\d{1})', param)
        if match_str:
            p_num = match_str.group('p_num')
            p_key = "{$p_str_"+p_num+"}"
            if p_key not in self._params.keys():
                p_value = self.g_p_str(pattern, format_value, default_value)
            else:
                return False
        
        if p_value is not None:
            # transcodings
            if p_value in self._transcodings.keys():
                p_value = self._transcodings.get(p_value)

            self.to_log(self.render_table_3(" "*6+p_key[2:-1], p_value, MyCli.color("OK  ", "SUCCESS")))
            self._params[p_key] = p_value
        else:
            self.to_log(self.render_table_3(" "*3+p_key, pattern + MyCli.color("NOK  ", "DANGER")))
            return None
        return True
    
    def get_param(self, model, version):
        fullpath = self.get_model_fullpath(model, version)
        ret = True
        
        self.to_log(" "*3+"params")
        
        try:
            for param in config.datas['ext']['pdf']['models'][model]['versions'][version]['params']:
                pattern = config.datas['ext']['pdf']['models'][model]['versions'][version]['params'][param]['pattern']
                format_value = self.load_param_format_value(param, model, version)
                default_value = self.load_param_default_value(param, model, version)
                ret = self.process_param(param, pattern, format_value, default_value)
                if ret is None:
                    return None
        except KeyError:
            pass
        
        try:
            for param in config.datas['ext']['pdf']['models'][model]['params']:
                pattern = config.datas['ext']['pdf']['models'][model]['params'][param]['pattern']
                format_value = self.load_param_format_value(param, model)
                default_value = self.load_param_default_value(param, model)
                ret = self.process_param(param, pattern, format_value, default_value)
                if ret is None:
                    return None
        except KeyError:
            pass
                
        for key, value in self._params.items():
            fullpath = self.g_fullpathname(fullpath, key, value)
        return fullpath
        
    def is_ping_ws_ocr(self):
        import requests
        import json
        
        try:
            response = requests.get(config.app_ws_ocr_url+"/hello", timeout=0.5)
            y = json.loads(response.text)
            self.to_debug(" "*3 + "{:<50}".format("WS OCR [1]") + MyCli.color("OK  ", "SUCCESS"))
            return  (y["message"] == 'Hello')
        except Exception as e:
            self.to_debug(" "*3 + "{:<50}".format("WS OCR [1]") + MyCli.color("ERROR", "DANGER"))
            log.error("Erreur de WS_OCR - " + str(e))
        
        try:
            response = requests.get(config.app_ws_ocr_url+"/hello", timeout=5)
            y = json.loads(response.text)
            self.to_debug(" "*3 + "{:<50}".format("WS OCR [2]") + MyCli.color("OK  ", "SUCCESS"))
            return  (y["message"] == 'Hello')
        except Exception as e:
            self.to_debug(" "*3 + "{:<50}".format("WS OCR [2]") + MyCli.color("ERROR", "DANGER"))
            log.error("Erreur de WS_OCR - " + str(e))
        return None
        
            
    def get_ws_ocr(self):
        if config.app_ws_ocr is not None:
            self.to_debug("PDF - Tentative MODE WS OCR", "ACTION")
            import requests
            import json
            try:
                data = {'ws_debug': config.app_ws_debug, 'ws_gray': config.app_ws_gray}
                response = requests.post(config.app_ws_ocr_url+'/ocr', data=data, files={'file': open(self.src_path+self.src_file,'rb')})
                y = json.loads(response.text)
                return self.clean_ocr(y['ocr'])
            except Exception as e:
                self.to_log("Erreur de WS_OCR - " + str(e), 'ERROR')
        return None
        
    def get_ocr(self):
        tmp = ''
        try:
            self.to_debug("PDF - Tentative MODE OCR Simple", "ACTION")
            tmp = self.clean_ocr(convert.pdf_to_txt(self.src_path+self.src_file))
            if tmp == '':
                return None
            else:
                return self.clean_ocr(convert.pdf_to_txt(self.src_path+self.src_file))
        except AttributeError:
            self.to_log("Impossible de lire fichier "+self.src_fullpath(), 'ERROR')
            return None
            
    def to_reject_sp(self):
        if self.ocr is not None:
            MyFile.write(self.ocr, config.app_path_reject+self.src_file+'/ocr.txt')
    
    def rename(self):
        ret = None
        
        if config.app_ws_ocr_url is not None:
            config.app_ws_ocr = self.is_ping_ws_ocr()
        
        self.ocr = self.get_ocr()
        if self.ocr is not None:
            self.to_debug(self.ocr, "OCR")
            ret = self.find_model()
            if ret is not None:
                return ret
                
        if config.app_ws_ocr is not None:
            self.ocr = self.get_ws_ocr()
            self.to_debug(self.ocr, "OCR")
            ret = self.find_model()
            if ret is not None:
                return ret
            
        return None
        
    def get_model_fullpath(self, model, version):
        fullpath = config.datas['ext']['pdf']['models'][model]['fullpath']
        
        try:
            fullpath = config.datas['ext']['pdf']['models'][model]['versions'][version]['fullpath']
        except KeyError:
            pass
        
        try:
            fullpath_suffix = config.datas['ext']['pdf']['models'][model]['versions'][version]['fullpath_suffix']
            fullpath = fullpath + fullpath_suffix
        except KeyError:
            pass
        return fullpath
        
    def render_table_3(self, val1, val2, val3):
        return("{:<20}".format(val1) + "|" + "{:<50}".format(val2) + "|" + "{:<20}".format(val3))
        
    def find_model(self):
        for model in config.datas['ext']['pdf']['models']:
            for version in config.datas['ext']['pdf']['models'][model]['versions']:
                if self.compare_keywords(model, version):
                    # Model trouve
                    self.to_log(self.render_table_3(" "*3 +"Modele", config.datas['ext']['pdf']['models'][model]['name']+'/'+version, ""))
                    
                    self.load_transcoding(model)
                    self.load_vars(model, version)
                    fullpath = self.get_param(model, version)
                    if fullpath is None:
                        return None
                    
                    # vars
                    for key, value in self._vars.items():
                        self.to_log(value, key)
                        fullpath = fullpath.replace("{$"+key+"}", value)
                    
                    return fullpath+config.app_suffix+".pdf"
        self.to_log(self.render_table_3(" "*3 +"Modele", "Aucun modele trouve", MyCli.color("WARN", "WARNING")))
        return None


    def compare_keywords(self, model, version):
        ls_tmp = []
        try:
            ls_tmp.extend(config.datas['ext']['pdf']['models'][model]['versions'][version]['keywords'])
        except:
            pass
        
        try:
            ls_tmp.extend(config.datas['ext']['pdf']['models'][model]['keywords'])
        except:
            pass
            
        for key in ls_tmp:
            if not re.search(self.g_p_preset(key), self.ocr, re.IGNORECASE):
                return False
        return True
    
    def get_group_value(self, match, group, default=None):
        try:
            return match.group(group)
        except IndexError:
            return default
    
    def g_p_preset(self, pattern):
        pattern = pattern.replace("{$d}", "(?P<d>([1-2][0-9]|(3)[0-1]|[1-9]))")
        pattern = pattern.replace("{#d}", "([1-2][0-9]|(3)[0-1]|[1-9])")
        pattern = pattern.replace("{$dd}", "(?P<dd>([0-2][0-9]|(3)[0-1]))")
        pattern = pattern.replace("{#dd}", "([0-2][0-9]|(3)[0-1])")
        pattern = pattern.replace("{$ddd}", "(?P<ddd>(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche))")
        pattern = pattern.replace("{#ddd}", "(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)")
        pattern = pattern.replace("{$mm}", "(?P<mm>((0[0-9])|(1[0-2])))")
        pattern = pattern.replace("{#mm}", "((0[0-9])|(1[0-2]))")
        pattern = pattern.replace("{$mmm}", "(?P<mmm>(janvier|f(.)vrier|mars|avril|mai|juin|juillet|ao(.)t|septembre|octobre|novembre|decembre))")
        pattern = pattern.replace("{#mmm}", "(janvier|f(.)vrier|mars|avril|mai|juin|juillet|ao(.)t|septembre|octobre|novembre|d(.)cembre)")
        pattern = pattern.replace("{$yyyy}", "(?P<yyyy>\d{4})")
        pattern = pattern.replace("{#yyyy}", "(\d{4})")
        
        pattern = pattern.replace("{$nir}", "(?P<str>([12][0-9]{2}(0[0-9]|1[0-2])(2[AB]|[0-9]{2})[0-9]{3}[0-9]{3}|[12] [0-9]{2} (0[0-9]|1[0-2]) (2[AB]|[0-9]{2}) [0-9]{3} [0-9]{3}))")
        pattern = pattern.replace("{$nir15}", "(?P<str>([12][0-9]{2}(0[0-9]|1[0-2])(2[AB]|[0-9]{2})[0-9]{3}[0-9]{3}[0-9]{2}|[12] [0-9]{2} (0[0-9]|1[0-2]) (2[AB]|[0-9]{2}) [0-9]{3} [0-9]{3} [0-9]{2}))")
        pattern = pattern.replace("{$tel}", "(?P<str>(([0-9]{2}){5}|([0-9]{2}[.]){4}[0-9]{2}|([0-9]{2}[ ]){4}[0-9]{2}))")
        pattern = pattern.replace("{#tel}", "(([0-9]{2}){5}|([0-9]{2}[.]){4}[0-9]{2}|([0-9]{2}[ ]){4}[0-9]{2})")
        pattern = pattern.replace("{$email}", "(?P<str>\S+@\S+)")
        return pattern
    
    def g_p_date(self, pattern, format_value=None, default_value=None):
        pattern = self.g_p_preset(pattern)
        match = re.search(pattern, self.ocr, re.IGNORECASE)
        
        if match:
            if format_value is not None:
                try:
                    yyyy = self.get_group_value(match, 'yyyy')
                    mm = self.get_group_value(match, 'mm')
                    mmm = self.get_group_value(match, 'mmm')
                    dd = self.get_group_value(match, 'dd')
                    d = self.get_group_value(match, 'd')
                    
                    match2 = re.search("yyyy", format_value)
                    if match2:
                        if yyyy is not None:
                            format_value = format_value.replace("yyyy", yyyy)
                        else:
                            return None
                    
                    match2 = re.search("mm", format_value)
                    if match2:
                        if mm is not None:
                            format_value = format_value.replace("mm", mm)
                        elif mmm is not None:
                            format_value = format_value.replace("mm", convert.mmm_to_mm(mmm))
                        else:
                            return None
                        
                    match2 = re.search("dd", format_value)
                    if match2:
                        if d is not None:
                            format_value = format_value.replace("dd",  	"{:0>2s}".format(d))
                        elif dd is not None:
                            format_value = format_value.replace("dd", dd)
                        elif jjj is not None:
                            format_value = format_value.replace("dd", convert.jjj_to_jj(jjj))
                        else:
                            return None
                    return format_value
                except:
                    return None
        else:
            if default_value is not None:
                return default_value
        return None

    def g_p_str(self, pattern, format_value=None, default_value=None):
        pattern = self.g_p_preset(pattern)
        match = re.search(pattern, self.ocr, re.IGNORECASE)
        res = ''
        if match:
            res = match.group('str')
            res = re.sub("/", "", res)
            if format_value is not None:
                ls_format_value = format_value.split('|')
                for fv in ls_format_value:
                    if fv == "supprespace":
                        res = re.sub(" ", "", res)
                    else:
                        return None
            return res
        else:
            if default_value is not None:
                return default_value
        return None
    
    def g_fullpathname(self, fullpath, pattern, value):
            return fullpath.replace(pattern, value)
    