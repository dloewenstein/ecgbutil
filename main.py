import tkinter as tk               # Used for main gui
import tkinter.ttk as ttk          # Used for pretty widgets
import tkinter.messagebox as msg   # Used for gui messages
import tkinter.filedialog          # Used for gui filedialog
import os                          # Create files, search directories
import shutil                      # Used for removing non-empty folders
import csv                         # for writing anonymization key
import subprocess                  # provide command line arguments to ECGToolkit
import xml.etree.ElementTree as ET # parse ecg xml files
import hashlib                     # hash identifiers
import datetime as dt              # work with date and time formats

# Class declarations
class Ecg:
    # Superclass for ecg conversion
    def __init__(self, dir, file):
        self.path   = str(dir + "/" + file)
        self.fname, self.ext = self.get_fname_fext(file)
        self.ext = self.ext.lower()

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
        """Set the target/output format"""
        self.target_format = target_form[0]
        self.target_ext    = target_form[1]

    def set_outdir(self, path):
        """Set the output directory"""
        self.outdir = path
        self.outpath = str(self.outdir + "/" + self.fname + self.target_ext)

    def convert_args(self):
        """Create command line arguments to ECGToolkit"""
        args = ['./lib/ECGTool', self.path, self.target_format, self.outpath]
        return args

class Ecg_xml(Ecg):
    # Childclass from Ecg for anonymization
    def __init__(self, dir, file):
        Ecg.__init__(self, dir, file)
        self.xml = ET.parse(self.path)
        self.pat_id = self.get_patdemo("PatientID")
        # Combine acq_date and acq_time to datetime MM/DD/YYYY HH:MM:SS
        self.acq_dt = str(self.get_testdemo("AcquisitionDate") + " " + self.get_testdemo("AcquisitionTime"))

    def get_patdemo(self, var):
        """Get PatientDemographics element"""
        return self.xml.find(str("./PatientDemographics/" + var)).text

    def set_patdemo(self, var, value):
        """Set PatientDemographics element"""
        self.xml.find(str("./PatientDemographics/" + var)).text = value

    def blank_patdemo(self, var):
        """Set PatientDemographics element to blank"""
        self.set_patdemo(var, value = "")
    
    def get_testdemo(self, var):
        """Get TestDemographics element"""
        return self.xml.find(str("./TestDemographics/" + var)).text

    def set_testdemo(self, var, value):
        """Set TestDemographics element"""
        self.xml.find(str("./TestDemographics/" + var)).text = value

    def blank_testdemo(self, var):
        """Set xml element to blank"""
        self.set_testdemo(var, value = "")

    def create_hash(self, var):
        """Apply sha256 alogrithm"""
        return hashlib.sha256(var.encode("utf8")).hexdigest()

    def anonymize(self):
        """Main anonymization function"""
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
        """Extract original and anonymized variables"""
        return list([self.pat_id, self.hash_id, self.acq_dt, self.acq_dt_hash])

    def write(self):
        """Write xml back to file"""
        self.xml.write(self.path, encoding = "utf-8", xml_declaration = True)


def create_tempdir(path):
    """Create temp folder"""
    temp_path = str(path + "/temp")
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
    return temp_path

def convert_ecg(in_dir, out_dir, file, target_form):
    """Convert ecg and return (n) success or fail"""
    ecg = Ecg(in_dir, file)
    if ecg.check_ext() is False:
        print("Skipping {} , wrong extension.".format(file))
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

def listfiles(path):
    """List files in directory"""
    files = []
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            files.append(file)
    return files

def convert_files(in_dir, out_dir, target_form, anonymize, progbar):
    """Orchestrate main functions"""
    files = listfiles(in_dir)
    n_proc_files = 0
    if len(files) == 0:
        msg.showinfo("Info", "Couldn't find any files to convert\nCurrently doesn't support searching subfolders.")
        return

    # Progressbar setup
    progbar["value"] = 0
    prog_step = float(100.0/len(files))

    if anonymize:
        # Setup record for identifiers
        anonymization_key = []
        anonymization_key.append(list(["pat_id", "ano_id", "acq_datetime", "acq_datetime_ano"]))
        prog_step = prog_step/3

        temp_path = create_tempdir(out_dir)

        # Step 1. convert to xml in preparation for anonymization
        for file in files:
            convert_ecg(in_dir, temp_path, file, ("MUSE-XML", ".xml"))
            progbar["value"] += prog_step
            progbar.update()

        temp_files = listfiles(temp_path)

        # Step 2. Perform anonymization
        for file in temp_files:
            ano_info = anonymize_ecg(temp_path, file)
            anonymization_key.append(ano_info)
            progbar["value"] += prog_step
            progbar.update()

        # Step 3. convert to destination format
        for file in temp_files:
            convert_ecg(temp_path, out_dir, file, target_form)
            n_proc_files += 1
            progbar["value"] += prog_step
            progbar.update()

        # Clean up temp folder
        shutil.rmtree(temp_path)

        with open(str(out_dir + "/" + "anonymization_key.csv"), "w") as outfile:
            writer = csv.writer(outfile, lineterminator = "\n")
            writer.writerows(anonymization_key)
    else:
        # If anonymizaiton option not choosen go ahead with conversion
        for file in files:
            convert_ecg(in_dir, out_dir, file, target_form)
            n_proc_files +=1
            progbar["value"] += prog_step
            progbar.update()

    msg.showinfo("Result", "Processed {} files".format(n_proc_files))
    #### END OF CONVERT_FILES FUNCTION #### 

class App(ttk.Frame):
    """Main application GUI"""
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()

        # Store input path
        self.in_dir  = tk.StringVar(self)

        # Store output path
        self.out_dir = tk.StringVar(self)

        # Store output format
        self.target_format = tk.StringVar(self)

        self.anonymize = tk.BooleanVar(self)
        self.create_widgets()


    def create_widgets(self):
        """Initialize main widgets"""

        # Choose input folder
        self.in_button = ttk.Button(self)
        self.in_button["text"] = "Choose input"
        self.in_button["command"] = lambda: self.askdir(self.in_dir)
        self.in_button["width"] = 14
        self.in_button.pack(fill="x")

        # Choose output folder
        self.out_button = ttk.Button(self)
        self.out_button["text"] = "Choose output"
        self.out_button["command"] = lambda: self.askdir(self.out_dir)
        self.out_button["width"] = 14
        self.out_button.pack(fill="x")

        # Extra space
        self.blank = ttk.Label(self)
        self.blank.pack(fill="x")

        # Dropdown list output options
        self.opt_label = ttk.Label(self)
        self.opt_label["text"] = "Target format:"
        self.opt_label.pack(fill="x")
        # Don't add spaces or reformat out_opts list
        # will break subsetting downstream
        self.out_opts = ["MUSE-XML .xml",
                         "DICOM .dcm",
                         "ISHNE .ecg",
                         "SCP-ECG .scp",
                         "aECG .xml",
                         "CSV .csv"]

        self.opt_list = ttk.OptionMenu(self,
                                       self.target_format, # Storage variable
                                       "MUSE-XML .xml",    # Start value
                                       *self.out_opts)     # Options
        self.opt_list.pack(fill="x")

        # Main function conversion button
        self.conv_button = ttk.Button(self)
        self.conv_button["text"] = "Convert"
        self.conv_button["command"] = self.convert
        self.conv_button.pack(fill="x")

        # Anonymization checkbox
        self.ano_box = ttk.Checkbutton(self)
        self.ano_box["text"] = "Anonymize"
        self.ano_box["variable"] = self.anonymize
        self.ano_box.pack(fill="x")

    def askdir(self, var, title = "Choose directory"):
        """Open OS filedialog for choosing directory"""
        dir = tk.filedialog.askdirectory(title = title)
        var.set(dir)
        print(var.get())

    def assert_input(self):
        """Assert that input folder is choosen"""
        if (self.in_dir.get() == ""):
            msg.showwarning("Warning", "No input folder choosen. Aborts...")
            return 1
        return 0

    def assert_output(self):
        """Assert that output folder is choosen"""
        if (self.out_dir.get() == ""):
            msg.showwarning("Warning", "No output folder choosen. Aborts...")
            return 1
        return 0


    def convert(self):
        if (self.assert_input()):
            return
        if (self.assert_output()):
            return
        popup = tk.Tk()
        progressbar = ttk.Progressbar(popup, length = 100, mode = "determinate")
        progressbar.pack(fill = "x")
        label = ttk.Label(popup, text = "Converting files ...")
        label.pack(fill = "x")
        target_format = self.target_format.get().split(" ")
        convert_files(self.in_dir.get(),    # set input directory
                      self.out_dir.get(),   # set output directory
                      target_format,        # provide choosen format
                      self.anonymize.get(), # anonymiz bool
                      progressbar)          # provide progressbar
        # kill progressbar window when done
        popup.destroy()
        

root  = tk.Tk()
style = ttk.Style()
style.theme_use("clam")
root.wm_geometry("220x190")
root.iconbitmap("ecgbutil.ico")
root.title("ECGButil")
app   = App(master = root)
app.mainloop()
