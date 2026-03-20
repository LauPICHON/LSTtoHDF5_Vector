#/*##########################################################################
#
# The AGLAE conversion functions
#
# Copyright (c) 2025 C2RMF
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#############################################################################*/
__author__ = "Laurent Pichon - C2RMF"
__contact__ = "laurent.pichon@culture.gouv.fr"
__license__ = "MIT"
__copyright__ = "Centre de Recherche et de Restauration des Musées de France, Paris, France"

import os, time, pathlib , fnmatch
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QWidget
from PyQt5.uic import loadUi
#from TestGUI import *
import win32api
#from IO_Fonction import AGLAEFile
from PyPIX_IO.IO_Fonction_Thread import AGLAEfunction
import numpy as np
import h5py
from time import perf_counter
from Hdf5Utils import *
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt

from PyPIX_IO import DataObject,EdfFile,EdfFileDataSource,EDFStack

def foo(bar, baz):
    print('hello  {0}'.format(bar))
    return 'foo' + baz

class MyThread(QThread):
    # Create a counter thread
    valueChanged = pyqtSignal(int)

    def run(self):
        cnt = 0
        while cnt < 100:
            cnt += 1
            time.sleep(0.3)
            self.valueChanged.emit(cnt)


class MainPage(QMainWindow):

    def __init__(self):
        super(MainPage, self).__init__()
        loadUi('GUI_LSTToHDF5_vector_2024.ui',self)
        self.button = self.findChild(QtWidgets.QPushButton, 'SelectFile')
        self.button.clicked.connect(self.select_lst)
        self.button2 = self.findChild(QtWidgets.QPushButton, 'SelectFolder')
        self.button2.clicked.connect(self.select_folder)
        self.input = self.findChild(QtWidgets.QLineEdit, 'input')
        self.filename_lst = self.findChild(QtWidgets.QTextEdit, 'textEdit_LST')
        self.txtparameter_lst = self.findChild(QtWidgets.QTextEdit, 'textEdit_paramater_lst')

        self.button1 = self.findChild(QtWidgets.QPushButton, 'SelectFile_EDF')
        self.button1.clicked.connect(self.select_file)
        self.filename_edf = self.findChild(QtWidgets.QTextEdit, 'textEdit_EDF')
        self.run1 = self.findChild(QtWidgets.QPushButton, 'pushButton_run')
        self.run1.clicked.connect(self.RunConvert)
        self.MyprogressBar = self.findChild(QtWidgets.QProgressBar, 'progressBar')
        self.MyprogressBar.setValue(2)
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        self.comboBox.addItems(drives)
        self.FinalLST = "c:/data/20200228_0049_Lapis_IBIL_IBA.LST"
        self.select_detector = list()
        self.select_detector.append("LE0")
        self.parameter_lst = list()
        self.totalprogress = 0
        self.readinglst = False
        self.parameter_edf = list()
        self.EDFasFile = False
        self.LSTasFile = False
        self.list_file = []
        self.pathfolder = ""
        self.detlist=[]
        self.list_file_type_edf = []
        self.FinalEDF = "c:/toto.edf"
        self.path_all_lst = "c:/"
        self.all_lst_fileName = []

    def Check_LE0(self, int):
        if self.CheckBoxLE0.isChecked():
            #self.ui.my_label.setText("CHECKED!")
            print("Checked")
            self.select_detector.append("LE0")
        else:
            print("UNCHECKED!")
            self.select_detector.remove("LE0")

    def Check_HE1(self, int):
        if self.CheckBoxHE1.isChecked():
            # self.ui.my_label.setText("CHECKED!")
            print("Checked")
            self.select_detector.append("HE1")
        else:
            print("UNCHECKED!")
            self.select_detector.remove("HE1")

    def Check_HE2(self, int):
        if self.CheckBoxHE2.isChecked():
            self.select_detector.append("HE2")
        else:
            self.select_detector.remove("HE2")

    def Check_HE3(self, int):
        if self.CheckBoxHE3.isChecked():
            self.select_detector.append("HE3")
        else:
            self.select_detector.remove("HE3")
    def Check_HE4(self, int):
        if self.CheckBoxHE4.isChecked():
            self.select_detector.append("HE4")
        else:
            self.select_detector.remove("HE4")

    def Check_HE10(self, int):
        if self.CheckBoxHE10.isChecked():
            self.select_detector.append("HE10")
        else:
            self.select_detector.remove("HE10")

    def Check_HE11(self, int):
        if self.CheckBoxHE11.isChecked():
            self.select_detector.append("HE11")
        else:
            self.select_detector.remove("HE11")

    def Check_HE12(self, int):
        if self.CheckBoxHE12.isChecked():
            self.select_detector.append("HE12")
        else:
            self.select_detector.remove("HE12")

    def Check_HE13(self, int):
        if self.CheckBoxHE13.isChecked():
            self.select_detector.append("HE13")
        else:
            self.select_detector.remove("HE13")

    def Check_RBS150(self, int):
        if self.CheckBoxRBS150.isChecked():
            self.select_detector.append("RBS150")
        else:
            self.select_detector.remove("RBS150")

    def Check_GAMMA70(self, int):
        if self.CheckBoxGAMMA70.isChecked():
            self.select_detector.append("GAMMA70")
        else:
            self.select_detector.remove("GAMMA70")

    def WaitReadinglst(self,reading):
        self.readinglst = reading
        print("Reading: " , reading)

    def setProgressVal(self, val):

        if val >= self.totalprogress:
            self.MyprogressBar.setValue(val)
            self.totalprogress = val
        elif val == 0:
            self.MyprogressBar.setValue(val)

    def RunConvert(self):
        
        if self.EDFasFile:
            self.parameter_lst = self.txtparameter_lst.toPlainText()
            i=0
            for root_edftype in self.list_file_type_edf:
                head_tail = os.path.split(self.FinalEDF)
               # AGLAEFile.finalhdf5(self.FinalEDF, root_edftype)
                if i == 0:
                    Final_HDF = AGLAEfunction.finalhdf5(self.FinalEDF, root_edftype)
                    AGLAEfunction.write_hdf5_metadata(self.FinalEDF, self.parameter_edf, root_edftype,Final_HDF)  # self.parameter_lst

                #AGLAEFile.write_hdf5_metadata(edfpath, parameter, detname)  # self.parameter_lst

                    # if fnmatch.fnmatch(file, root_file + det_aglae[j]+'_0001.edf'):

                for file in os.listdir(head_tail[0]):
                    if fnmatch.fnmatch(file, root_edftype + '*_0000' + '.edf'):
                        edffile = file #self.list_file.append(file)
                        AGLAEfunction.edf_To_hdf5(os.path.join(self.pathfolder, edffile), root_edftype, self.parameter_lst,
                                              Final_HDF,i)
                        i += 1
                        break
                #for edffile in self.list_file:

                #'EDFStack.loadIndexedStack(self.FinalEDF)
        else:
            self.runLst2hdf5()

    # def multi_process_lst2hdf5(self,one_lst):
    #         _dict_adc_metadata_arr, _dict_metadata_global = AGLAEfunction.open_header_lst(one_lst)
    #         AGLAEfunction.extract_lst_vector(self.MyprogressBar,one_lst, _dict_metadata_global, _dict_adc_metadata_arr,_progess_val)
        

    def runLst2hdf5(self):
        total_files = len(self.all_lst_fileName)
        _progess_val_start = 0
        _progess_val = 0
        self.MyprogressBar.setRange(0, 100)
        self.MyprogressBar.setValue(0)
        
        for i,one_lst in enumerate(self.all_lst_fileName, start=1):
            _dict_adc_metadata_arr,_dict_metadata_global = AGLAEfunction.open_header_lst(one_lst)
            print ("\nexctract: ",one_lst)
            taille_file = 0 
            taille_map_x=_dict_metadata_global["map size x (um)"]
            taille_map_y=_dict_metadata_global["map size y (um)"]
            taille_file = os.path.getsize(one_lst)

            min_file_size = 2000000
            if int(taille_map_x) >=1000 and int(taille_map_y) >=1000:
                min_file_size = 2000000
            elif int(taille_map_x) <1000 and int(taille_map_y) <1000:
                min_file_size = 1000000

            
            if taille_map_x !='0' and taille_map_y!='0' and taille_file > min_file_size:
                datapath = one_lst.split(".")
                datapath = datapath[0] + ".hdf5"
                # AGLAEfunction.write_hdf5_metadata(datapath, self.parameter_lst , self.select_detector[0],datapath) # self.parameter_lst
                AGLAEfunction.write_hdf5_metadata(one_lst,_dict_metadata_global) # self.parameter_lst
                self.readinglst = 1
                
                _progess_val = 100/total_files

                AGLAEfunction.extract_lst_vector(self.MyprogressBar,one_lst, _dict_metadata_global, _dict_adc_metadata_arr,_progess_val)
                f =i*(100/total_files)
                self.MyprogressBar.setValue(int(f))
                i=1
            print("Conversion Finished")
        
    def runThreadEDF(self):
        l = len(self.select_detector)
        self.parameter_lst = self.txtparameter_lst.toPlainText()  # AGLAEFile.open_header_lst(self.FinalLST)
        new_para = self.parameter_lst.split("\n")
        # para = new_para.split(":")
        para1 = list()
        for obj in new_para:
            try:
                para = obj.split(": ")
                if para[0] == " Map size X,Y (um)" or para[0] == ' Pixel size X,Y (um)':
                    para = para[1].split("x")
                    para1.append(para[0])
                    para1.append(para[1])
                else:
                    para1.append(para[1])
            except:
                pass

        self.parameter_lst = para1
        sizeX = int(self.parameter_lst[3]) / int(self.parameter_lst[5])
        sizeY = int(self.parameter_lst[4]) / int(self.parameter_lst[6])
        sizeX = int(sizeX)
        sizeY = int(sizeY)
        shape = (sizeX, sizeY, 2048)
        datapath = self.FinalEDF.split(".")
        datapath = datapath[0] + ".hdf5"
       ## AGLAEFile.write_hdf5_metadata(datapath, self.parameter_lst)  # self.parameter_lst

        clread = readrawlst(self.FinalEDF)  # LIT TOUT LE FICHIER LST
        rawlst = clread.extract()

        self.MyprogressBar.setRange(0, 100)
        self.totalprogress = 0
        self.setProgressVal(0)
        self.readinglst = 1

        for detector in self.select_detector:
            self.setProgressVal(0)
            print("detector :", detector)

            self.ThrLST = ThreadReadLst2(path=self.FinalLST, rawlst=rawlst, para=self.parameter_lst, detector=detector)
            self.ThrLST.valueChanged.connect(self.setProgressVal)
            # self.ThrLST.signalreadlst.connect(self.WaitReadinglst)
            # self.ThrLST.path = self.FinalLST
            # self.ThrLST.detector= detector
            # self.ThrLST.rawlst = rawlst
            self.ThrLST.start()
            self.ThrLST.wait(100)
            # self.ThrLST.join()
            # time.sleep(1)

            # while self.ThrLST.isFinished() == False:
            #    print("sleep 0.1 sec.")
            #    time.sleep(0.1)
            # time.sleep(2)
            # self.setProgressVal(0)
            # print(detector)
            # self.thread = ThreadReadLst2(path=self.FinalLST, detector="LE0")
            # self.thread.valueChanged.connect(self.setProgressVal)
            # self.thread.path = self.FinalLST
            # self.thread.detector = detector
            # self.thread.start()
            # print("fini")
            # self.thread.join(1)

    # self.Read_Lst(self.FinalLST)

    def select_folder(self):
        self.path_all_lst = QFileDialog.getExistingDirectory(self," Select folder with LST files",'c:\\')
        
                


    def select_lst(self):
        fileName,_ = QFileDialog.getOpenFileNames(self, "Select LST to extact in HDF5", "c:/", ("LST file (*.lst)"),'*.lst')
        #myshape = np.shape(fileName)

        if len(fileName) == 1: # and myshape[0] > 1:
            self.FinalLST = fileName[0][0]    
            self.all_lst_fileName = fileName[0]
        else:
            self.FinalLST = fileName[0]
            self.all_lst_fileName = fileName[0]
        
        self.FinalLST = fileName[0]
        self.all_lst_fileName = fileName
        

        head_tail = os.path.split(self.FinalLST) # Split le Path et le fichier
        #sp = self.FinalLST.split("/")
        root_text = os.path.splitext (head_tail[1]) # Split nom et ext du fichier
        name = root_text[0]
        #name = sp[-1]
        self.filename_lst.setText(name)
        self.filename_edf.setText("")
        sp = name.split("_")
        self.LSTasFile = True
        self.EDFasFile = False

        currentDirectory = pathlib.Path(head_tail[0])
        # define the pattern
        if len(sp) >1 :
            currentPattern = sp[0] + "_" + sp[1] + "*.jpg" # nouveau nom 20200308_0048_OBJ_PRJ_IBA.lst
        else:
            currentPattern = sp[0] + "*.jpg" # ancien nom "26jul008.lst"

            for currentFile in currentDirectory.glob(currentPattern): # Recherche si une image jpg à le même nom que le LST
                filejpg = currentFile

        #for file in os.listdir(head_tail[0]):
        #   if file.find(sp[0] + "_" + sp[1],0, len(file)) != -1:
        #       filejpg = file


        parameter = AGLAEfunction.open_header_lst_simple(self.FinalLST)
        self.parameter_lst = parameter

        txtparameter = " Date: {} \n Objet: {}\n Projet: {}\n".format(parameter[0], parameter[1], parameter[2])
        txtparameter =  txtparameter + " Map size X,Y (um): {} x {}\n Pixel size X,Y (um): {} x {}\n Pen size (um): {}\n".format(parameter[3], parameter[4], parameter[5], parameter[6],parameter[7])
        try: 
            txtparameter =  txtparameter + " Particule: {} \n Beam energy (keV): {} \n LE0 filter: {}\n HE1 filter: {}\n HE2 filter: {}\n" \
                                           " HE3 filter: {}\n HE4 filter: {}\n".format(parameter[8], parameter[9], parameter[10],parameter[11], parameter[12], parameter[13], parameter[14])
        except:
                txtparameter =  txtparameter + " Particule: ? \n Beam energy (keV): ? \n LE0 filter: ?\n HE1 filter: ?\n HE2 filter: ?\n" \
                                           " HE3 filter: ?\n HE4 filter: ?\n"

        self.txtparameter_lst.setText(txtparameter)

    def select_file(self):
        fileName = QFileDialog.getOpenFileName(self, "Select EDF to convert in HDF5", "c:/", ("EDF file (*.edf)"))
        self.FinalEDF = fileName[0]
        head_tail = os.path.split(self.FinalEDF)  # Split le Path et le fichier
        # sp = self.FinalLST.split("/")
        root_text = os.path.splitext(head_tail[1])  # Split nom et ext du fichier
        name = root_text[0]
        self.filename_edf.setText(name)
        self.filename_lst.setText("")
        self.pathfolder = head_tail[0]
        self.LSTasFile = False
        self.EDFasFile = True
        self.list_file = []
        self.list_file_type_edf = []

        if self.EDFasFile == True: # Cherche le nombre de type de détecteur présent dans le répertoire
            n = len(name)
            i = 1
            nchain = []

            while (i <= n):
                c = name[n - i:n - i + 1]
                if c not in ['0', '1', '2',
                             '3', '4', '5',
                             '6', '7', '8',
                             '9']:
                    break
                else:
                    nchain.append(c)
                i += 1

            suffix = name[n - i + 1:]
            new_root_name = name[:n-len(suffix)-1]
            # sp = name.split("_")
            det_aglae = ["LE0", "HE1", "HE2", "HE3","HE4", "HE10", "HE11"]
            filelisttmp = []

            nbedf = 0
            nb_type_edf = 0
            # if len(sp) ==7: # Format AGLAE '20200304_0012_OBJ_PRJ_IBA_BE0_0001.edf'
            #    root_file = sp[0] + "_" + sp[1] +"_" + sp[2] +"_" + sp[3] + "_" + sp[4] + "_"

            # for j in range(10):
            nb_total_edf = len(fnmatch.filter(os.listdir(head_tail[0]), '*.edf'))
            # for type_edf in list_file_type_edf:

            for file in os.listdir(head_tail[0]): # TROUVE LES DIFFERENTES TYPE EDF PRESENT DANS LE REPERTOIRE
                if fnmatch.fnmatch(file, '*' + '.edf'):
                    n = len(os.path.splitext(file)[0])
                    new_root_name2 = file[:n-len(suffix)-1]
                    if not new_root_name2 in self.list_file_type_edf:
                        self.list_file_type_edf.append(new_root_name2)
                        nb_type_edf +=1


            for file in os.listdir(head_tail[0]):
                # if fnmatch.fnmatch(file, root_file + det_aglae[j]+'_0001.edf'):
                if fnmatch.fnmatch(file, new_root_name + '*' + '.edf'):
                    self.list_file.append(file)
                    nbedf += 1

      
        currentDirectory = pathlib.Path(head_tail[0])
        if len(self.list_file[0]) == 0:
            self.list_file.append(fileName[0])

        parameter = AGLAEfunction.open_header_edf(self.FinalEDF) #os.path.join(head_tail[0] , self.list_file[0])
        self.parameter_edf = parameter

        if len(parameter) == 21:
            txtparameter = " Date: {} \n Objet: {}\n Projet: {}\n".format(parameter[0], parameter[1], parameter[2])
            txtparameter = txtparameter + " Map size X,Y (um): {}\n Pixel size X,Y (um): {}\n Pen size (um): {}\n".format(
            parameter[9], parameter[10], parameter[11])
            txtparameter = txtparameter + " Particule: {} \n Beam energy (keV): {} \n LE0 filter: {}\n HE1 filter: {}\n HE2 filter: {}\n" \
                                      " HE3 filter: {}\n HE4 filter: {}\n".format(parameter[14], parameter[15],
                                                                                  parameter[16], parameter[17],
                                                                                  parameter[18], parameter[19],
                                                                                  parameter[20])
        else:
            txtparameter = " Date: {} \n Objet: {}\n Projet: {}\n".format(parameter[0], parameter[1], parameter[2])
            txtparameter = txtparameter + " Map size X,Y (um): {}\n Pixel size X,Y (um): {}\n Pen size (um): {}\n".format(
                parameter[5],nbedf, parameter[11])
            #txtparameter = txtparameter + " Particule: ? \n Beam energy (keV): ? \n LE0 filter: ? \n HE1 filter: ? \n HE2 filter: ? \n" \
            #                              " HE3 filter: ? \n HE4 filter: ? \n"


        self.txtparameter_lst.setText(txtparameter)


    def finalname(self, detname):

        head_tail = os.path.split(Pathfile)  # Split le Path et le fichier
        destfile = head_tail[1].split(".")
        newdestfile = destfile[0] + ".hdf5"
        index_iba = destfile[0].find("_IBA_")
        index_l1 = destfile[0].find("_L1_")
        index_xrf = destfile[0].find("_XRF1_:")
        det_aglae = ["BE0", "HE1", "HE2", "HE3", "HE4", "HE10", "HE11", "IBIL", "FORS"]
        iba_para = False

        for det1 in det_aglae:
            if detname == det1:
                iba_para = True

        #   if index_l1 > 0:
        #  elif index_xrf > 0:

        if destfile[1] == 'lst':
            newdestfile = destfile[0] + ".hdf5"
        elif destfile[1] == 'edf':
            # n = len(destfile[0])
            name = os.path.basename(destfile[0])
            if index_iba > 0:
                Myname = name.split('_IBA')
                FinalHDF = Myname[0] + ".hdf5"
            else:
                Myname = name.split('_')
                FinalHDF = Myname[0] + "_" + Myname[1] + ".hdf5"

    def retrieveText(self):
        words = self.plainTextEdit.toPlainText ()
        self.textEdit1.setText(words)

    def majFolder(self):
        self.textEdit.setText(self.comboBox.currentText())
        currentHDD = self.comboBox.currentText()
        for folder in os.listdir(currentHDD):
            if os.path.isdir(os.path.join("c:/", folder)):
                self.textEdit.setText(folder)


def compare(a, b):
        s = ""
        for i in range(len(a)):
            if a[i] is not b[i]:
                s += str(a[i])
            #else:
             #   s += str(b[i])
        return s

class readrawlst:

    def __init__(self,path):
        self.path = path

    def extract(self):
        pathlst1 = self.path
        tmpheader = ""
        header1 = list()
        sizeX = 1
        sizeY = 1
        print("toto")
        print(pathlst1)

        # self.mutex.lock()

        print("lock done")


        with open(pathlst1, "rb") as file_lst:

            while tmpheader != b'[LISTDATA]\r\n':
                tmpheader = file_lst.readline()

                # Map size:1280,1280,64,64,0,2564,100000
                if "Map size" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    para = str.split(para[1], sep=",")
                header1.append(tmpheader)
            print(header1)
            print(para[0], para[1], para[2], para[3])
            sizeX = int(para[0]) / int(para[2])
            sizeY = int(para[1]) / int(para[3])
            sizeX = int(sizeX)
            sizeY = int(sizeY)

            # for i in range (0,50):
            val = b'\xff\xff\xff\xff'
            lstcontent = file_lst.read()
            ind1 = 0
            nrows = 0
            ncolumns = 0
            print(sizeY)
            print(sizeX)

            # MainPage.progress.setRange(1,len(lstcontent) -22000000)
        # self.mutex.unlock()
        time.sleep(3)
         # Libère le thread après avoir lu le contenu du fichier
        print("unlock")

        return lstcontent

def getSize(fileobject):
    fileobject.seek(0,2) # move the cursor to the end of the file
    size = fileobject.tell()
    return size

class ThreadReadLst2():

    # Create a counter thread
    # valueChanged = pyqtSignal(int)
    #signalreadlst = pyqtSignal(int) # Signal de blocage durant la lecture du fichier LST

    #def __init__(self,path,detector,rawlst, para, parent = None):
    def __init__(self, path, detector, path_lst, para, parent=None):
        # QThread.__init__(self, parent)
        self.path = path
        self.detector = detector
        #self.lstcontent = rawlst
        self.path_lst = path_lst
        self.para = para
        #self.mutex = QMutex()



    # def run(self):
    #
    #     # pathlst = "C:\\Dev\\PyPIX\\Data\\26jul0068.lst" #26jul0068.lst
    #     pathlst1 = self.path
    #     tmpheader = ""
    #     header1 = list()
    #     sizeX = 1
    #     sizeY = 1
    #     print("toto")
    #     print(pathlst1)
    #     print(self.para[0], self.para[1], self.para[2], self.para[3])
    #     sizeX = int(self.para[3]) / int(self.para[5])
    #     sizeY = int(self.para[4]) / int(self.para[6])
    #     sizeX = int(sizeX)
    #     sizeY = int(sizeY)
    #     adcnum = []
    #     nbcanaux = 1024
    #     switcher = {
    #         "LE0": 2048,
    #         "HE1": 2048,
    #         "HE2": 2048,
    #         "HE3": 2048,
    #         "HE4": 2048,
    #         "HE10": 2048,
    #         "HE11": 2048,
    #         "HE12": 2048,
    #         "HE13": 2048,
    #         "RBS": 512,
    #         "GAMMA": 4096,
    #     }
    #     nbcanaux = switcher.get(self.detector)
    #     cube = np.zeros((sizeX, sizeY, nbcanaux), 'u4')
    #     # for i in range (0,50):
    #     file = open(pathlst1, 'rb')
    #     size_lst = getSize(file)
    #     file.close()
    #
    #     with open(pathlst1, "rb") as file_lst:
    #
    #         while tmpheader != b'[LISTDATA]\r\n':
    #             tmpheader = file_lst.readline()
    #
    #             # Map size:1280,1280,64,64,0,2564,100000
    #             if "Map size" in str(tmpheader):
    #                 para = str.split(str(tmpheader), sep=':')
    #                 para = str.split(para[1], sep=",")
    #             header1.append(tmpheader)
    #         print(header1)
    #         print(para[0], para[1], para[2], para[3])
    #         sizeX = int(para[0]) / int(para[2])
    #         sizeY = int(para[1]) / int(para[3])
    #         sizeX = int(sizeX)
    #         sizeY = int(sizeY)
    #
    #         # for i in range (0,50):
    #         val = b'\xff\xff\xff\xff'
    #
    #
    #
    #
    #
    #         val = b'\xff\xff\xff\xff'
    #         #Pas possible gros LST
    #        # lstcontent = self.lstcontent #  file_lst.read()
    #         ind1 = 0
    #         nrows = 0
    #         ncolumns = 0
    #         print(sizeY)
    #         print(sizeX)
    #         adc2read = 0
    #         adc2read = ret_num_adc(self.detector)
    #         print("adc2read:", adc2read)
    #         FastcomtecX = 8
    #         FastcomtecY = 9
    #         switch_xy = 0
    #         nb_count = 0
    #
    #         #while ind1 < len(file_lst) - len(tmpheader) - 20:
    #         while True:
    #             lstcontent = file_lst.read(4)
    #             if not lstcontent:
    #                 # eof
    #                 break
    #
    #
    #             try:
    #                 # val = file_lst.read(4)
    #                 val = lstcontent #lstcontent[ind1:ind1 + 4]
    #                 ind1 += 4
    #             except:
    #                 val = b'\xff\xff\xff\xff'
    #                 # QtCore.QCoreApplication.processEvents()
    #                 # MainPage.progress.setValue(ind1)
    #
    #             if val == b'\xff\xff\xff\xff':
    #                 # val = file_lst.read(4)
    #                 val = file_lst.read(4) # Read 4 Bytes in LST file  before (lstcontent[ind1:ind1 + 4])
    #                 ind1 += 4
    #                 text = "Events"
    #                 #print(int(100/len(lstcontent)*ind1)+1)
    #
    #                 #time.sleep(1)
    #
    #             val3 = int.from_bytes(val, byteorder='little', signed=False)
    #             low1 = val3 & 0xFFFF
    #             hight1 = int(val3 >> 16)
    #
    #             if ind1 % 100000 < 10:
    #                 self.valueChanged.emit(int(100 *(ind1 /size_lst)))
    #                 #self.signalreadlst.emit(0)
    #
    #             if 0x4000 == hight1:
    #                 text = "Valeur tempo"
    #                 tempo = low1
    #
    #             if 0xFFFF == low1:
    #                 text = "Valeur channel"
    #                 channel = hight1
    #
    #             if 0x8000 == hight1:
    #                 text = "TAG ADC"
    #                 adc = low1
    #
    #                 readval = False
    #                 adcnum = []
    #                 channel_num = []
    #
    #                 if adc & adc2read:
    #                     readval = True # ADC en cours est un detector demandé
    #                 else:
    #                     readval = False
    #
    #                 for bits in range(16):
    #                     if adc & (0b0000000000000001 << bits):
    #                         adcnum.append(bits)
    #
    #                 if len(adcnum) % 2 == 1:  # & len(adcnum) > 1:
    #                     # toto = file_lst.read(2) #Nb paire ADC !!
    #                     val = file_lst.read(2) #Read 2 bytes in LST File #lstcontent[ind1:ind1 + 2]
    #                     ind1 += 2
    #
    #                 if readval == True:
    #                     for f in adcnum:
    #
    #                             val = file_lst.read(2) #Read 2 bytes in LST File    # lstcontent[ind1:ind1 + 2]
    #
    #                             if f != FastcomtecX and f != FastcomtecY:
    #                                 val1 = int.from_bytes(val, byteorder='little', signed=False)
    #                                 val = val1&(nbcanaux-1)  #Opération logique binaire pour enlever les bits de poids fort-1)
    #                                 channel_num.append(val) #int.from_bytes(val, byteorder='little', signed=False))
    #                             if f == FastcomtecX:
    #                                 val1 = int.from_bytes(val, byteorder='little', signed=False)
    #                                 val = val1&2047
    #                                 nrows = val #int.from_bytes(val, byteorder='little', signed=False)  # Valeur X
    #                             if f == FastcomtecY:
    #                                 val1 = int.from_bytes(val, byteorder='little', signed=False)
    #                                 val = val1&2047
    #                                 ncolumns = val #int.from_bytes(val1, byteorder='little', signed=False)
    #                             ind1 += 2
    #
    #                             if ncolumns == 0 and ind1 < 10000:
    #                                 switch_xy += 1
    #                                 if switch_xy > 1000:  # Change les num. de voies FastComtec vers X = 4 et Y = 5 (ancien LST)
    #                                     print("Switch XY FastXomtec")
    #                                     FastcomtecX = 4
    #                                     FastcomtecY = 5
    #                                     ind1 = 0
    #                                     switch_xy = 0
    #                                     cube[0, 0, :] = 0
    #                             else:
    #                                 switch_xy = 0
    #                 else:
    #                     file_lst.seek(len(adcnum)*2, 1)  #val = file_lst.read(2)
    #
    #                 # if readval == False:
    #                 #     ind1 += 4 * len(adcnum)
    #
    #                 for c in channel_num:
    #                     if (c < nbcanaux) & (nrows < sizeX) & (ncolumns < sizeY):
    #                         cube[nrows, ncolumns, c] += 1
    #                         nb_count += 1
    #
    #     self.valueChanged.emit(100)
    #     print("nb events : ", nb_count)
    #     #AGLAEFile.write_hdf5(cube, self.path, self.detector)
    #     AGLAEFile. write_hdf5(cube, self.path, self.detector, "FinalHDF", adc2read)
    #
    #     self.valueChanged.emit(0)
    #     print("emit 0")

    def run(self):

        # pathlst = "C:\\Dev\\PyPIX\\Data\\26jul0068.lst" #26jul0068.lst
        pathlst1 = self.path
        tmpheader = ""
        header1 = list()
        sizeX = 1
        sizeY = 1
        print("toto")
        print(pathlst1)
        print(self.para[0], self.para[1], self.para[2], self.para[3])
        sizeX = int(self.para[3]) / int(self.para[5])
        sizeY = int(self.para[4]) / int(self.para[6])
        sizeX = int(sizeX)
        sizeY = int(sizeY)
        adcnum = []

        nbcanaux = 1024
        switcher = {
            "LE0": 2048,
            "HE1": 2048,
            "HE2": 2048,
            "HE3": 2048,
            "HE4": 2048,
            "HE10": 2048,
            "HE11": 2048,
            "HE12": 2048,
            "HE13": 2048,
            "RBS": 512,
            "RBS150": 512,
            "RBS135": 512,
            "GAMMA": 4096,
            "GAMMA20": 4096,
            "GAMMA70": 4096,
        }

        nbcanaux = switcher.get(self.detector)
        #cube = np.zeros((sizeX, sizeY, nbcanaux), 'u4')
        ## for i in range (0,50):
        file = open(pathlst1, 'rb')
        size_lst = getSize(file)
        file.close()

        with open(pathlst1, "rb") as file_lst: # Trop long
            while tmpheader != b'[LISTDATA]\r\n':
                tmpheader = file_lst.readline()
                size_lst -=(len(tmpheader)-2)
                if "condition" in str(tmpheader):
                    toto=1
                # Map size:1280,1280,64,64,500,2564,100000
                if "Map size" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    para = str.split(para[1], sep=",")
                #header1.append(tmpheader)

            print(para[0], para[1], para[2], para[3])
            sizeX = int(para[0]) / int(para[2])
            sizeY = int(para[1]) / int(para[3])
            sizeX =  int(sizeX)
            sizeY = int(sizeY)
            pensize = int(para[4])
            nb_pass_y = int(sizeY/(pensize/int(para[3])))
#           cube_final= np.zeros((sizeY,sizeX,nbcanaux-1),dtype=np.uint16)

            val = b'\xff\xff\xff\xff'
            #Pas possible gros LST
           # lstcontent = self.lstcontent #  file_lst.read()
            range_small = 10**6 #range(1, 10**6) #50 Mo
            range_100mega = 10**7#range(10**6+1, 10**7) #100 Mo
            range_giga =10**8 # range(10**7 + 1, 1**12)  # 100 Mo
            size_lst =int(size_lst/2) #car on lit des Uint16 donc 2 fois moins que le nombre de bytes (Uint8)

            if size_lst < range_small: size_block = size_lst
            if size_lst > range_100mega: size_block =1000000#2*10**5 #10Mo
            if size_lst > range_giga: size_block = 1*10**7 #50Mo
            #size_block = 100000
            nb_read_total = 0
            if size_lst > size_block:
                nb_loop = int(size_lst / size_block)
                nb_loop +=1
                reste = size_lst % size_block
            else:
                nb_loop= 1
                reste= 0
            nb_byte_to_read = size_block
            indice_in_datablock = 0
            nb_read_total = 0
            max_val_y_lue = 0
            pair = True
            y_scan = int(sizeY/nb_pass_y) -1
            nb_column = int(sizeY/nb_pass_y)
            data_array_previous = np.empty(0, dtype=np.uint16)
            pair = False
            end_extract = False

            for num_pass_y in range(nb_pass_y):

                if (num_pass_y %2 ==0):
                    pair = True
                    last_x_value_prev = np.zeros(12,dtype= np.uint16)
                else:
                    pair = False
                    end_extract = False
                    last_x_value_prev = np.full(12,sizeX-1,dtype= np.uint16)

                y_scan_total = y_scan + (num_pass_y * nb_column)

                cube_one_pass = np.empty((12, nb_column, sizeX, nbcanaux), dtype=np.uint32)
                fin_ligne = False
                while (fin_ligne == False): #max_val_y_lue <= y_scan): # or end_ligne_impaire == False ):

                    adc_values = np.empty(0, dtype=np.uint16)
                    data_array = np.empty(0, dtype=np.uint16)
                    adjusted_indices = np.empty(0, dtype=np.uint16)

                    # Divise en 10 block , recherche indice ="0X8000" = 32768 et retrouve les indices des valeurs
                    # des adcs qui ont déclanchés
                   # for nb_block in range(10):
                    min_last_pos_x_y_in_array = nb_byte_to_read
                    data_array = np.fromfile(file_lst, dtype=np.uint16, count=int(nb_byte_to_read))

                    if len(data_array) < nb_byte_to_read:
                        end_extract= True
                    data_array = data_array[data_array != 65535]
                    data_array = np.append(data_array_previous,data_array)
                    min_last_pos_x_y_in_array = np.shape(data_array)
                    shape_data_array =min_last_pos_x_y_in_array
                    # Recherche de la valeur 0x8000 (32768) dans le tableau de données
                    indices_32768 = np.where(data_array == 32768)
                    indices_32768 = np.array(indices_32768[0])
                    indices_32768 = np.delete(indices_32768, len(indices_32768) - 1)


                    # Création d'indices ajustés et filtrage
                    one_array = np.full(np.shape(indices_32768), 1)
                    adjusted_indices = indices_32768 - one_array
                    adc_values = np.array(data_array[adjusted_indices])




                    nb_read_total += (nb_byte_to_read * 2)
                    t1 =perf_counter()


                    for num_line_adc in range(6):
                        if  num_line_adc == 1 or num_line_adc == 8 or num_line_adc == 9 or num_line_adc==5: continue

                        switcher = {5: 2048, 0: 2048,1: 2048,2 : 2048,3: 2048,4: 2048,80: 2048,81: 2048,
                            82: 2048,6: 512,7: 512,9: 512,10: 512,11: 2048,12: 2048}
                        nbcanaux = switcher.get(num_line_adc)

                        self.detector= ret_adc_name(num_line_adc)
                        adc2read = num_line_adc + 1
                        #adc2read = ret_num_adc(self.detector)
                        t0 = perf_counter()

                        # Opérations bitwise et filtrage des indices
                        adc_masked = np.bitwise_and(adc_values[:], 0b0000000000000001 << num_line_adc)
                        #filtered_indices = np.where(adc_masked[:] != 0, adjusted_indices[:], np.zeros(len(adc_masked)))
                        filtered_indices = np.where(adc_masked[:] != 0, adjusted_indices[:], np.full(len(adc_masked),-1,dtype=np.int16))
                        non_zero_indices = filtered_indices[filtered_indices != -1]
                        if len(non_zero_indices) < 10:
                            continue
                        #libère de la RAM
                        del adc_masked
                        del filtered_indices

                        # Initialisation et boucle de traitement (optimisée)


                        # Convert `non_zero_indices` to a NumPy array for better performance
                        non_zero_indices = np.array(non_zero_indices)

                        # Extract `adc_word` values from `data_array` at indices `non_zero_indices`
                        adc_words = data_array[non_zero_indices]

                        # Initialize an array to store the number of bits set to 1 for each `adc_word`
                        bit_count_array = np.empty(len(adc_words), dtype=int)
                        qui_a_declanche = np.empty((12,len(adc_words)),dtype= int)
                        ind10 = []
                        # Loop through each bit position and count the bits set to 1
                        for bit_position in range(12):
                            # Create a mask for the current bit position
                            bit_mask = 0b0000000000000001 << bit_position
                            # Use bitwise AND to check if the current bit is set
                            adc_declanche = adc_words & bit_mask
                            bit_count_array += adc_declanche > 0
                            ind10 = np.where(adc_declanche != 0, non_zero_indices+1, np.zeros(len(adc_declanche)))
                            qui_a_declanche[bit_position,:] =ind10

                        del ind10


                        # Store th=[]e number of bits set to 1 for each `adc_word` in `bit_count_list`
                        #####bit_count_list.extend(bit_count_array)

                        # Calculate indices adjusted by the length of bits set to 1
                        adjusted_indices_array = non_zero_indices - bit_count_array
                        compteur_valeur= np.empty((12, len(adc_words)), dtype=np.int8)
                        mysum = np.zeros((1, len(adc_words)), dtype=np.int8)
                       # for arr in qui_a_declanche:
                       #          zero_els = jnp.count_nonzero(arr == 0)
                        del adc_words


                        for x in range(12): #15, -1,-1):
                            #r= np.where(qui_a_declanche[x,:] !=0, qui_a_declanche[x,:] - bit_count_array[:],qui_a_declanche[x,:])
                            compteur_valeur[x,:]= np.where(qui_a_declanche[x,:]!=0,mysum+1,qui_a_declanche[x,:])
                            mysum = np.where(compteur_valeur[x,:]!=0,mysum+1,mysum)



                        indice_val_to_read = qui_a_declanche + compteur_valeur  #np.full(len(compteur_valeur),1)

                        max_size_x = ret_range_bytes(sizeX - 1)
                        max_size_y = ret_range_bytes(sizeY - 1)
                        coord_x = data_array[indice_val_to_read[8, :]]#non_zero_indices]]
                        coord_x = coord_x & max_size_x #2047 #
                        coord_y = data_array[indice_val_to_read[9, :]]  # non_zero_indices]]
                        c1 = indice_val_to_read[9, :]
                        c1 =c1[c1!=0]

                        if len(c1) < 100:
                            continue
                        coord_y = coord_y & max_size_y  # 2047 #sizeY - 1

                        #sup_max_sizex = np.where(coord_x > sizeX - 1)
                        # Met des -1 aux coord X et Y supérieur à la valeur de la carto
                        coord_x = np.where(coord_x <= sizeX - 1, coord_x, np.full(len(coord_x),-1))
                        coord_y = np.where(coord_y <= sizeY - 1, coord_y, np.full(len(coord_y),-1))

                        # recherche la dernire valeur de Y
                        last_pos_y = np.empty(0, dtype=np.uint16)
                        for pos in range(500):
                            last_pos_y = np.append(last_pos_y, coord_y[-pos])
                        max_val_y_lue = np.max(last_pos_y)

                       

                        if max_val_y_lue > y_scan_total: # Contient le scan suivant
                            print("Next scan Y:") #,max_val_y_lue)    
                            indice_y_last = np.where(coord_y == y_scan_total) #recherche les val de la dernier colonne
                            if len(indice_y_last[0]) < 50:
                                fin_ligne=True
                                continue
                            max_data_array_y = indice_val_to_read[9, indice_y_last]
                            coord_x = coord_x[:indice_y_last[0][-1]]
                            coord_y = coord_y[:indice_y_last[0][-1]]
                            indice_x_last = indice_y_last[0][-1]
                            max_data_array = indice_val_to_read[8, indice_x_last]
                            if max_data_array < min_last_pos_x_y_in_array: min_last_pos_x_y_in_array = max_data_array

                        else:# recherche la dernire valeur de X
                            last_pos_x = np.empty(0, dtype=np.uint16)
                            first_pos_x = np.empty(0, dtype=np.uint16)
                            for pos in range(500):
                                if pair==True:
                                    last_pos_x = np.append(last_pos_x, coord_x[-pos]) # A partir de la fin
                                    first_pos_x = np.append(first_pos_x, coord_x[pos])  # A partir du début
                                else:
                                    last_pos_x = np.append(last_pos_x, coord_x[pos])  # A partir du début
                                    first_pos_x = np.append(first_pos_x, coord_x[-pos])  # A partir de la fin


                            last_pos_x = np.delete(last_pos_x,0)
                            count_x = np.bincount(last_pos_x)
                            last_x = int(np.shape(count_x)[0]) -1  #np.where(count_x == max(count_x))
                            count_x_min = np.bincount(first_pos_x)
                            first_x = np.where(count_x_min == max(count_x_min))
                            first_x_value = int(first_x[0])


                            if pair== True:
                                last_x_value = last_x -1 #int(last_x[0]) - 1
                            else:
                                if last_x != 0:
                                    last_x_value = first_x_value  # int(last_x[0]) + 1

                                else:
                                    last_x_value = 0 # fin de la ligne de retour

                            print("X:",last_x_value)


                            if last_x_value == 15:
                                last_x_value =last_x_value

                            if end_extract == False:
                                indice_x_max = np.where(coord_x == last_x_value)

                                if int(last_x_value_prev[num_line_adc]) != 0 :
                                    if pair == True:
                                        indice_x_prev = np.where(coord_x == int(last_x_value_prev[num_line_adc])+1) #recherche la colonne suivant dans ligne pair
                                        indice_x_prev1 = indice_x_prev[0][0]

                                    else:
                                        indice_x_prev = np.where(coord_x == int(last_x_value_prev[num_line_adc]))  # recherche la colonne suivant dans ligne pair
                                        indice_x_prev1 = indice_x_prev[0][-1]

                                else:
                                    indice_x_prev1 = 0

                                if len(indice_x_max) ==0:continue
                                indice_x_last = indice_x_max[0][-1]
                                max_data_array = indice_val_to_read[8, indice_x_last]

                                coord_x = coord_x[indice_x_prev1:indice_x_last]
                                coord_y = coord_y[indice_x_prev1:indice_x_last]
                                if max_data_array < min_last_pos_x_y_in_array :
                                    min_last_pos_x_y_in_array = max_data_array
                            else:
                                if pair == True:
                                    last_x_value = sizeX -1
                                else:
                                    last_x_value = 0
                                indice_x_last = len(coord_x)

                        # last_pos_y = np.empty(0, dtype=np.uint16)
                        # for pos in range(500):
                        #     last_pos_y = np.append(last_pos_y, coord_y[-pos])
                        #
                        # count_y = np.bincount(last_pos_y)
                        # if count_y[-1] > 10: max_val_y_lue = len(count_y)-1

                        #sup_max_sizey = np.where(coord_y > sizeY - 1)
                        #all_max = np.concatenate(np.array(sup_max_sizex), np.array(sup_max_sizey), axis=0)
                        #all_max= [np.append(i, sup_max_sizey[0]) for i in sup_max_sizex]

                        #if num_line_adc== 0:
                        # indice_true_value = indice_val_to_read[num_line_adc, :]
                        # adc0= data_array[indice_true_value[:]]
                        non_zero_indices = np.nonzero(indice_val_to_read[num_line_adc, indice_x_prev1:indice_x_last])
                        adc1 = data_array[indice_val_to_read[num_line_adc, non_zero_indices]]
                        adc1 = np.array(adc1 & nbcanaux-1)
                        new_coord_x = coord_x[non_zero_indices]
                        new_coord_y = coord_y[non_zero_indices]

                        if pair==True:
                            range_histo = int(last_x_value - last_x_value_prev[num_line_adc])  #last_x_value_prev[num_line_adc])
                            if int(last_x_value_prev[num_line_adc]) == 0:
                                range_histo += 1
                            if int(last_x_value_prev[num_line_adc]) != 0:
                                last_x_value_prev[num_line_adc] += 1


                        else:
                            range_histo = int(last_x_value_prev[num_line_adc]-last_x_value)

                        if range_histo == 0:
                            continue
                            print(f'range_histo : {range_histo}')

                        p1 = int(last_x_value_prev[num_line_adc])
                        p2 = last_x_value
                        if pair==True:
                            r1= [p1,p2]
                        else:
                            r1 = [p2, p1]
                        r2 = {p1,p2}
                        H1, edges = np.histogramdd((new_coord_y, new_coord_x, adc1[0]), range=({0, nb_column},r1 , {0, nbcanaux}), bins=(nb_column, range_histo, nbcanaux-1))
                        # fig, ax = plt.subplots()
                        print(np.shape(H1))
                        plt.plot(H1[0, 0, :])
                        plt.show()
                       # cube_one_pass= np.add((cube_one_pass,H1),axis=2)
                        if pair == True:

                            cube_one_pass[num_line_adc][0:,int(last_x_value_prev[num_line_adc]):last_x_value+1,0:nbcanaux-1] = H1
                            last_x_value_prev[num_line_adc] = last_x_value #-last_x_value_prev[num_line_adc]
                        else:
                            cube_one_pass[num_line_adc] [0:, last_x_value:int(last_x_value_prev[num_line_adc]),0:nbcanaux-1] = H1
                            last_x_value_prev[num_line_adc] = first_x_value

                    if min_last_pos_x_y_in_array < shape_data_array:
                        data_array_previous =[]
                        data_array_previous = data_array[min_last_pos_x_y_in_array:]

               # data_array_previous = np.empty(0, dtype=np.uint16)
                for num_line_adc in range(6):
                    adc2read = num_line_adc + 1
                    self.detector = ret_adc_name(num_line_adc)
                    data = cube_one_pass[num_line_adc]
                    AGLAEfunction.feed_hdf5_map (data, self.path, self.detector, "FinalHDF", adc2read,sizeX,sizeY,nbcanaux)



               # AGLAEFile.write_hdf5(cube_one_pass, self.path, self.detector, "FinalHDF", adc2read,sizeX,sizey,nbcanaux)
                Tps_bit_and = perf_counter() - t0

                # for x in range(np.max(coord_x)+1):
                #     val_adc_x_fixed = np.where(coord_x == x, adc1[:], np.full(len(adc1),-1))
                #     for y in range(np.max(coord_x)+1):
                #         val_adc_x_y_fixed = np.where(coord_y == y, val_adc_x_fixed[:], np.full(len(val_adc_x_fixed),-1))
                #         val_adc_y_fixed = val_adc_x_y_fixed[val_adc_x_y_fixed != -1]
                #         val_adc_x_y_fixed = np.ndarray.astype(val_adc_y_fixed,dtype=int)
                #         #new_adc = ret_x_y_fixed(x, y, 0, adc1, coord_x, coord_y)
                #         #new_adc1 = np.array([i for i in new_adc[0][:] if i != 0])
                #         if len(val_adc_x_y_fixed) > 2:
                #             val_adc_x_y_fixed[0] = 0 # Pour Histogram
                #             val_adc_x_y_fixed[1] = nbcanaux-1 # pour Histogram
                #         counts, bins = np.histogram(val_adc_x_y_fixed, bins=nbcanaux-1)
                #         counts[0]=0
                 #       cube_final[y,x, :] += counts
                #new_adc1 = np.where(new_adc[0][:]!=0,new_adc[0][:],)

                        #coord_ok = np.array(coord_ok)

                        #r1 = adc1[coord_ok[1,:]]


                        #qui_a_declanche[x,:] -= bit_count_array[:]-x


                Tps_final = perf_counter() - t1
            # self.valueChanged.emit(100)
           # print("nb events : ", nb_count)
            # AGLAEFile.write_hdf5(cube, self.path, self.detector)
           # AGLAEFile.write_hdf5(H, self.path, self.detector, "FinalHDF", adc2read)

            # self.valueChanged.emit(0)
            print("emit 0")

   


class MultiThreadReadLst():

    # Create a counter thread
    valueChanged = pyqtSignal(int)
    #signalreadlst = pyqtSignal(int) # Signal de blocage durant la lecture du fichier LST

    def __init__(self,path,detector,rawlst, para, parent = None):
        QThread.__init__(self, parent)
        self.path = path
        self.detector = detector
        self.lstcontent = rawlst
        self.para = para
        #self.mutex = QMutex()



    def run(self):

        # pathlst = "C:\\Dev\\PyPIX\\Data\\26jul0068.lst" #26jul0068.lst
        pathlst1 = self.path
        tmpheader = ""
        header1 = list()
        sizeX = 1
        sizeY = 1
        print("toto")
        print(pathlst1)
        print(self.para[0], self.para[1], self.para[2], self.para[3])
        sizeX = int(self.para[0]) / int(self.para[2])
        sizeY = int(self.para[1]) / int(self.para[3])
        sizeX = int(sizeX)
        sizeY = int(sizeY)
        adcnum = []
        switcher = {
            "LE0": 2048,
            "HE1": 2048,
            "HE2": 2048,
            "HE3": 2048,
            "HE4": 2048,
            "HE10": 2048,
            "HE11": 2048,
            "HE12": 2048,
            "HE13": 2048,
            "RBS": 512,
            "GAMMA": 4096,
        }
        nbcanaux = switcher.get(self.detector)
        cube = np.zeros((sizeX, sizeY, nbcanaux), 'u4')
        # for i in range (0,50):
        val = b'\xff\xff\xff\xff'
        lstcontent = self.lstcontent #  file_lst.read()
        ind1 = 0
        nrows = 0
        ncolumns = 0
        print(sizeY)
        print(sizeX)
        adc2read = 0
        adc2read = ret_num_adc(self.detector)
        print("adc2read:", adc2read)
        FastcomtecX = 8
        FastcomtecY = 9
        switch_xy = 0
        nb_count = 0

        while ind1 < len(lstcontent) -20:

            try:
                # val = file_lst.read(4)
                val = lstcontent[ind1:ind1 + 4]
                ind1 += 4
            except:
                val = b'\xff\xff\xff\xff'
                # QtCore.QCoreApplication.processEvents()
                # MainPage.progress.setValue(ind1)

            if val == b'\xff\xff\xff\xff':
                # val = file_lst.read(4)
                val = lstcontent[ind1:ind1 + 4]
                ind1 += 4
                text = "Events"
                #print(int(100/len(lstcontent)*ind1)+1)
                #time.sleep(1)

            val3 = int.from_bytes(val, byteorder='little', signed=False)
            low1 = val3 & 0xFFFF
            hight1 = int(val3 >> 16)

            if ind1 % 50000 < 10:
                self.valueChanged.emit(int(100 / len(lstcontent) * ind1))
                #self.signalreadlst.emit(0)

            if 0x4000 == hight1:
                text = "Valeur tempo"
                tempo = low1

            if 0xFFFF == low1:
                text = "Valeur channel"
                channel = hight1

            if 0x8000 == hight1:
                text = "TAG ADC"
                adc = low1
                readval = False
                adcnum = []
                channel_num = []

                if adc & adc2read:
                    readval = True # ADC en cours est un detector demandé
                else:
                    readval = False

                for bits in range(16):
                    if adc & (0b0000000000000001 << bits):
                        adcnum.append(bits)

                if len(adcnum) % 2 == 1:  # & len(adcnum) > 1:
                    # toto = file_lst.read(2) #Nb paire ADC !!
                    val = lstcontent[ind1:ind1 + 2]
                    ind1 += 2

                for f in adcnum:
                    if readval == True:
                        val = lstcontent[ind1:ind1 + 2]
                        if f != FastcomtecX and f != FastcomtecY: channel_num.append(int.from_bytes(val, byteorder='little', signed=False))
                        if f == FastcomtecX: nrows = int.from_bytes(val, byteorder='little', signed=False)  # Valeur X
                        if f == FastcomtecY: ncolumns = int.from_bytes(val, byteorder='little', signed=False)
                        ind1 += 2

                        if ncolumns == 0 and ind1 < 10000:
                            switch_xy += 1

                            if switch_xy > 1000:  # Change les num. de voies FastComtec vers X = 4 et Y = 5 (ancien LST)
                                print("Switch XY FastXomtec")
                                FastcomtecX = 4
                                FastcomtecY = 5
                                ind1 = 0
                                switch_xy = 0
                                cube[0, 0, :] = 0
                        else:
                            switch_xy = 0

                    else:
                        ind1 += 2 * len(adcnum)

                for c in channel_num:
                    if (c < 1024) & (nrows < sizeX) & (ncolumns < sizeY):
                        cube[nrows, ncolumns, c] += 1
                        nb_count += 1


        self.valueChanged.emit(100)

        print("nb events : ", nb_count)
        AGLAEfunction.write_hdf5(cube, self.path, self.detector)
        self.valueChanged.emit(0)
        print("emit 0")

def ret_num_adc(detector):
   switcher = {
                "LE0":  0b0000000000010000, #2A
                "HE1":  0b0000000000000001,
                "HE2":  0b0000000000000010,
                "HE3":  0b0000000000000100,
                "HE4":  0b0000000000001000,
                "HE10": 0b0000000000001111,
                "HE11": 0b0000000000000011,
                "HE12": 0b0000000000001100,
                "HE13": 0b0000000000000111,
                "RBS" : 0b0000000010000000, #2D
                "GAMMA": 0b0000000000100000, #2B
                            }
   return switcher.get(detector)

def ret_adc_name(num_adc):
   switcher = {
               0: "X1",
               1: "X2",
               2: "X3",
               3: "X4",
               4: "X0",  # 2A
               5: "HE10",
               6: "RBS135",
               7: "RBS150",
               8: "Coord_X",
               9: "Coord_Y",
               10: "GAMMA20",
               11: "GAMMA70",
                            }
   return switcher.get(num_adc)

class Writehdf5(QThread):

    def __init__(self,cube,path):
        self.path = path
        self.cube = cube

    def run(self):
        # f = h5py.File('./Data/ReadLst_GZIP.hdf5', 'w')
        destfile = self.path.split(".")
        newdestfile = destfile[0] + ".hdf5"
        f = h5py.File(newdestfile, 'w')
        #  dset1 = f.create_dataset("default", (100,),compression="gzip", compression_opts=9)
        # d1 = np.random.random(size=(1000, 20))

        with open("c:\\temp\\toto.x0", "r") as File_Spectre:
            header1 = File_Spectre.readline()
            header1 = File_Spectre.readline()
            listpara = header1.split(",")
            listpara1 = listpara[0].split(" ")

            grp = f.create_group("parametres")
            grp.attrs["Particule"] = listpara[8]
            grp.attrs["Map size"] = 'X:{} x Y:{} (\u03BCm)'.format(listpara[1], listpara[2])
            grp.attrs["Pixel size"] = "X:{} x Y:{} (\u03BCm)".format(listpara[1], listpara[2])
            grp.attrs["Detector filter"] = "LE0:{} HE1:{} HE2:{} HE3:{} HE4:{}".format(listpara[10], listpara[11],
                                                                                       listpara[12], listpara[13],
                                                                                       listpara[14])
            grp.attrs["dim1"] = 10
            data_spectre = File_Spectre.readlines()
            y = [int(i) for i in data_spectre]
            LE0 = np.array(y)
            grp.attrs["dim2"] = len(data_spectre)

            # mydata = np.array(y)
        dset = f.create_dataset("Data", data=self.cube , dtype='u4', compression="gzip", compression_opts=4)
        dset.write_direct(self.cube)
        dset2 = f.create_dataset("Total spectra LE0", data=LE0, dtype='u4', compression="gzip", compression_opts=4)
        dset2.write_direct(LE0)
        print("HDF5 write")
        f.close()

def ret_range_bytes(val):
    for bits in range(16):
        if val & (0b0000000000000001 << bits):
            nombre_bytes = bits
    return  2**(nombre_bytes+1) - 1

def ret_x_y_fixed (x,y,num_line,adc,X,Y):
    x_fixed = np.where(X==x, adc[:],np.zeros(len(adc)))
    y_fixed = np.where(Y==y, x_fixed[:],np.zeros(len(x_fixed)))#,x_fixed[1],np.zeros(len(x_fixed)))
    #x_y_fixed = np.where(Y==y,x_fixed[:],y)
    return y_fixed

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = MainPage()
    widget.show()
    sys.exit(app.exec_())