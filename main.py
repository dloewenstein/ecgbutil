import tkinter as tk
import tkinter.filedialog
import os
import shutil.rmtree as rmdir
import csv
import subprocess
import xml.etree.ElementTree as ET
import hashlib
import datetime as dt

# Class declarations
class Ecg:
    # Superclass for ecg conversion
    def __init__(self, dir, file):
        self.path   = str(dir + "/" + file)
        self.fname, self.ext = self.get_fname_fext(file)

    def get_fname_fext(self, file):
        """Get the filename, extension"""
        return os.path.splitext(file)

    def check_ext(self):
        """Verify valid file extension"""
        if self.ext in [".dcm", ".xml", ".scp", ".ecg"]:
            correct_ext = True
        else:
            correct_ext = False
        return correct_ext

    def set_target_format(self, target_form):
        self.target_format = target_form[0]
        self.target_ext    = target_form[1]

    def set_outdir(self, path):
        self.outdir = path
        self.outpath = str(self.outdir + "/" + self.fname + self.target_ext)

    def convert_args(self):
        args = ['ECGTool', self.path, self.target_format, self.outpath]
        return args

class Ecg_xml(Ecg):
    # Childclass from Ecg for anonymization
    def __init__(self, dir, file):
        Ecg.__init__(self, dir, file)
        self.xml = ET.parse(self.path)
        self.pat_id = self.get_patdemo("PatientID")
        self.acq_dt = str(self.get_testdemo("AcquisitionDate") + " " + self.get_testdemo("AcquisitionTime"))

    def get_patdemo(self, var):
        return self.xml.find(str("./PatientDemographics/" + var)).text

    def set_patdemo(self, var, value):
        self.xml.find(str("./PatientDemographics/" + var)).text = value

    def blank_patdemo(self, var):
        self.set_patdemo(var, value = "")
    
    def get_testdemo(self, var):
        return self.xml.find(str("./TestDemographics/" + var)).text

    def set_testdemo(self, var, value):
        self.xml.find(str("./TestDemographics/" + var)).text = value

    def blank_testdemo(self, var):
        self.set_testdemo(var, value = "")

    def create_hash(self, var):
        return hashlib.sha256(var.encode("utf8")).hexdigest()

    def anonymize(self):
        self.hash_id     = self.create_hash(self.pat_id)
        self.acq_dt_hash = self.create_hash(self.acq_dt)

        self.set_patdemo("PatientID", self.hash_id)
        self.set_testdemo("SecondaryID", self.acq_dt_hash)

        self.blank_patdemo("DateofBirth")
        self.blank_patdemo("Gender")
        self.blank_patdemo("Race")
        self.blank_patdemo("PatientFirstName")
        self.blank_patdemo("PatientLastName")

        self.set_testdemo("AcquisitionDate", dt.date.today().strftime('%m/%d/%Y'))
        self.set_testdemo("AcquisitionTime", dt.datetime.today().strftime('%H:%M:%S'))

    def get_ano_info(self):
        return list([self.pat_id, self.hash_id, self.acq_dt, self.acq_dt_hash])

    def write(self):
        self.xml.write(self.path, encoding = "utf-8", xml_declaration = True)


def create_tempdir(path):
    temp_path = str(path + "/temp")
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    return temp_path

def convert_ecg(in_dir, out_dir, file, target_form):
    """Convert ecg and return (n) success or fail"""
    ecg = Ecg(in_dir, file)
    if ecg.check_ext() is False:
        return
    ecg.set_target_format(target_form)
    ecg.set_outdir(out_dir)
    p = subprocess.run(ecg.convert_args())

    if p.returncode == 0:
        success, fail = 1, 0
    else:
        success, fail = 0, 1

    return success, fail

def anonymize_ecg(dir, file):
    """Anonymize ecg and return anonymized info"""
    ecg = Ecg_xml(dir, file)
    ecg.set_target_format(("MUSE-XML", ".xml"))
    ecg.set_outdir(dir)
    ecg.anonymize()
    ecg.write()

    ano_info = ecg.get_ano_info()
    return ano_info

def convert_files(in_dir, out_dir, target_form, anonymize = False):
    files = os.listdir(in_dir)
    if anonymize:
        anonymization_key = []
        anonymization_key.append(list(["pat_id", "ano_id", "acq_datetime", "acq_datetime_ano"]))

        temp_path = create_tempdir(out_dir)

        for file in files:
            convert_ecg(in_dir, temp_path, file, ("MUSE-XML", ".xml"))

        temp_files = os.listdir(temp_path)

        for file in temp_files:
            ano_info = anonymize_ecg(temp_path, file)
            anonymization_key.append(ano_info)

        for file in temp_files:
            convert_ecg(temp_path, out_dir, file, target_form)

        rmdir(temp_path)

        with open(str(out_dir + "/" + "anonymization_key.csv"), "w") as outfile:
            writer = csv.writer(outfile, lineterminator = "\n")
            writer.writerows(anonymization_key)
    else:
        for file in files:
            convert_ecg(in_dir, out_dir, file, target_form)

tk.Tk().withdraw()

in_dir = tk.filedialog.askdirectory(title="Choose input directory")
print(in_dir)
out_dir = tk.filedialog.askdirectory(title="Choose output directory")
print(out_dir)

out_opts = [("DICOM",    ".dcm"),
            ("ISHNE",    ".ecg"),
            ("MUSE-XML", ".xml"),
            ("SCP-ECG",  ".scp"),
            ("aECG",     ".xml"),
            ("CSV",      ".csv")]

in_opts = [".dcm",
           ".xml",
           ".scp",
           ".ecg"]

convert_files(in_dir, out_dir, out_opts[0], anonymize = True)
