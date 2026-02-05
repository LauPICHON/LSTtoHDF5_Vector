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


import h5py, re
import numpy as np
import sys, os
from PyQt5.QtCore import  QThread, pyqtSignal
from PyPIX_IO import EdfFile, EDFStack , ArraySave, EdfFileDataSource,DataObject,PhysicalMemory
import threading
from datetime import datetime
from time import perf_counter
import matplotlib.pyplot as plt
from time import sleep
import configparser


class AGLAEfunction(object):
    _FILE_LOCK_1 = threading.Lock()

    def __init__(self):
        self.path = "c:/temp/toto.lst"
        self.detector = "LE0"

    @staticmethod
    def save_hdf5_antoine(filename, points_map, spectrums_list, group_name="XRF_Analysis", dataset_name="dataset"):
        try:
            assert (len(points_map) == len(spectrums_list))
        except AssertionError:
            raise (IndentationError(
                f"points_map length : {len(points_map)} and spectrum_list length : {len(spectrums_list)} do not match."))

        with h5py.File(filename, 'w') as h5file:

            data = np.zeros((3, 3, 3, len(spectrums_list[0])))

            for index, point in enumerate(points_map):
                x = point[0]
                y = point[1]
                z = point[2]
                data[x, y, z] = spectrums_list[index]

            subgroup = h5file.require_group(group_name)
            subgroup.attrs['Analysis date'] = datetime.now().strftime('%d/%m/%Y')
            subgroup.attrs['Analysis time'] = datetime.now().strftime("%H:%M:%S")
            dset = subgroup.create_dataset(dataset_name, data=data)

    @staticmethod
    def create_empty_hdf5(filename: str, data_shape, dtype=np.float64, group_name="XRF_analysis",
                          dataset_name="dataset", file_lock=_FILE_LOCK_1):
        with file_lock:
            with h5py.File(filename, 'w') as h5file:
                subgroup = h5file.require_group(group_name)
                dset = subgroup.create_dataset(dataset_name, shape=data_shape, dtype=dtype)

    @staticmethod
    def feed_existing_hdf5(filename, data, group_name="XRF_analysis", dataset_name="dataset", file_lock=_FILE_LOCK_1):

        with file_lock:
            with h5py.File(filename, 'a') as h5file:
                dset = h5file[f'{group_name}/{dataset_name}']
                dset[:] = data

    @staticmethod
    def get_dataset_data_hdf5(filename, group_name: str = "XRF_analysis", dataset_name: str = "dataset",
                              file_lock=_FILE_LOCK_1):

        with file_lock:
            with h5py.File(filename, 'r') as h5file:
                group = h5file.require_group(f'{group_name}')
                dset_data = group[f'{dataset_name}']
                np_dset_data = np.array(dset_data)

            return np_dset_data
    #
    # @staticmethod
    # def feed_spectrum(filename, spectrum: list[int], x_position: int, y_position: int, group_name="XRF_analysis",
    #                   dataset_name="dataset", file_lock=_FILE_LOCK_1) -> None:
    #     try:
    #         with file_lock:
    #             with h5py.File(filename, 'a') as h5file:
    #                 group = h5file.require_group(f'{group_name}')
    #                 dset = group[f'{dataset_name}']
    #                 dset[y_position, x_position] = spectrum
    #     except IndexError as idxerr:
    #         print(f'INDEXERROR : {x_position} or {y_position} out of range \n {idxerr}')
    #         raise IndexError(idxerr)

    @staticmethod
    def save_final_hdf5_from_tmp(save_filepath, tmp_file, channels, calibration, live_time,
                                 tmp_group_name="XRF_analysis", tmp_dataset_name="dataset"):
        with h5py.File(tmp_file, 'r') as tmp_file:
            group = tmp_file.require_group(f'{tmp_group_name}')
            dset_data = group[f'{tmp_dataset_name}']
            np_dset_data = np.array(dset_data)

        with h5py.File(save_filepath, 'w') as final_hdf5:
            mca0 = final_hdf5.require_group("mca_0")
            data = mca0.create_dataset("data", data=np_dset_data)
            chan = mca0.create_dataset("channels", data=channels)
            calib = mca0.create_dataset("calibration", data=calibration)
            ltime = mca0.create_dataset("live_time", data=live_time)

    @staticmethod
    def write_hdf5(mydata, Pathlst, detector,FinalHDF,num_det):

        # f = h5py.File('./Data/ReadLst_GZIP.hdf5', 'w')
        destfile = Pathlst.split(".")
        newdestfile = destfile[0] + ".hdf5"

        if destfile[1] == 'lst':
            newdestfile = destfile[0] + ".hdf5"
        elif destfile[1] == 'edf':

            # name = os.path.basename(destfile[0])
            # Myname = name.split('_IBA')
            # FinalHDF = Myname[0] + ".hdf5"
            newdestfile = os.path.join(os.path.dirname(Pathlst), FinalHDF)
       ##ArraySave.save3DArrayAsHDF5 (mydata,newdestfile)
        print(newdestfile)
        hdf = h5py.File(newdestfile, 'a')
        try:
            del hdf[detector]
        except:
            pass
        shape= mydata.shape
        dtype = mydata.dtype

       ###dset = f.create_dataset(detector, data=mydata, dtype='u4', compression="gzip", compression_opts=4)
        entryName = 'data' + str(num_det) + "_" + detector  # "data"

        nxData = hdf.require_group(entryName)
        #grp = f.create_group("stack/" + detector)
        ##dset = NxData.create_dataset("data",shape=shape, data=mydata, dtype=dtype) #'u8') #, compression="gzip", compression_opts=4)

        dset = nxData.require_dataset('maps', data = mydata, shape=shape, dtype=dtype, compression="gzip", compression_opts=4)
        nxData.attrs["signal"] = detector
        dset.flush()
        print("HDF5 write" + detector )
        hdf.close()
   
    # @staticmethod
    # def create_combined_pixe(cube_one_pass_pixe,pathlst,num_pass_y):
    
    #     detectors = [110,112,113]
    #     for num_det in detectors:
    #         detector = ret_adc_name(num_det)
    #         if detector == "X10":
    #             data = cube_one_pass_pixe[0] + cube_one_pass_pixe[1] + cube_one_pass_pixe[2] + cube_one_pass_pixe[3]
    #         elif detector == "X11":
    #             data = cube_one_pass_pixe[0] + cube_one_pass_pixe[1]
    #         elif detector == "X12":
    #             data = cube_one_pass_pixe[2] + cube_one_pass_pixe[3]
    #         elif detector == "X13":
    #             data = cube_one_pass_pixe[0] + cube_one_pass_pixe[1] + cube_one_pass_pixe[2]
        

    #         AGLAEfunction.feed_hdf5_map(data, pathlst, detector, num_pass_y)
    @staticmethod
    def create_combined_pixe(cube_one_pass_pixe,pathlst,num_pass_y,_dict_adc_metadata_arr):
        """Create combined PIXE data from multiple detectors."""
        detectors = [134,13,14,34] #"1+3+4","3+4","1+4","1+3"]
        for num_det in detectors:
           
            if num_det == 1234:
                data = cube_one_pass_pixe[0] + cube_one_pass_pixe[1] + cube_one_pass_pixe[2] + cube_one_pass_pixe[3]
                metadata_one_adc = _dict_adc_metadata_arr[0]
            elif num_det == 134:
                data = cube_one_pass_pixe[0] + cube_one_pass_pixe[2] + cube_one_pass_pixe[3]
                metadata_one_adc = _dict_adc_metadata_arr[0]
            elif num_det == 12:
                data = cube_one_pass_pixe[0] + cube_one_pass_pixe[1]
                metadata_one_adc = _dict_adc_metadata_arr[0]
            elif num_det == 34:
                data = cube_one_pass_pixe[2] + cube_one_pass_pixe[3]
                metadata_one_adc = _dict_adc_metadata_arr[2]
            elif num_det == 14:
                data = cube_one_pass_pixe[0] + cube_one_pass_pixe[1] + cube_one_pass_pixe[2]
                metadata_one_adc = _dict_adc_metadata_arr[0]
            elif num_det == 123:
                data = cube_one_pass_pixe[0] + cube_one_pass_pixe[1] + cube_one_pass_pixe[2]
                metadata_one_adc = _dict_adc_metadata_arr[0]
            
            detector_name = ret_adc_name(num_det)
            mysum1 = np.sum(data, axis=0)    # Somme des lignes
            mysum1 = np.sum(mysum1, axis=0)  # Somme des lignes
            mysum1 = np.sum(mysum1, axis=0)  # Somme des lignes
            if mysum1 > 0:
                AGLAEfunction.feed_hdf5_map(data, pathlst, detector_name, num_pass_y,metadata_one_adc)


    # @staticmethod
    # def feed_hdf5_map(mydata, Pathlst, detector, num_scan_y):
 
    #     destfile = Pathlst.split(".")
    #     newdestfile = destfile[0] + ".hdf5"
    
    #     with h5py.File(newdestfile, 'a') as h5file:
    #         #group_name = 'data' + str(num_det) + "_" + detector  # "data"
    #         group_name = detector  # "data"

    #         if num_scan_y != 0:
    #                 nxData = h5file[f'{group_name}/maps']
    #                 nxData.resize((nxData.shape[0] + mydata.shape[0],nxData.shape[1] ,nxData.shape[2]))
    #                 nxData[-mydata.shape[0]:,0:, :] = mydata
 
    #         else:
    #                 try:
    #                     del h5file[f'{group_name}']
    #                 except Exception:
    #                     pass
    #                 nxData = h5file.require_group(f'{group_name}')
    #                 dset = nxData.require_dataset('maps', data = mydata, shape =mydata.shape, dtype=np.uint32, maxshape=(None,None,None), chunks=True, compression="gzip",compression_opts=4)
    #     h5file.close()
    
    @staticmethod
    def feed_hdf5_map(mydata, Pathlst, detector, num_scan_y, dict_metadata_one_adc):
        """Feed an HDF5 file with map data."""
        if mydata.size == 0:
            print(f"No data to write for detector {detector}")
            return
 
        destfile = Pathlst.split(".")
        newdestfile = destfile[0] + ".hdf5"
    
        with h5py.File(newdestfile, 'a') as h5file:
            #group_name = 'data' + str(num_det) + "_" + detector  # "data"
            group_name = detector  # "data"

            if num_scan_y != 0:
                    nxData = h5file[f'{group_name}/maps']
                    nxData.resize((nxData.shape[0] + mydata.shape[0],nxData.shape[1] ,nxData.shape[2]))
                    nxData[-mydata.shape[0]:,0:, :] = mydata
            else:
                    try:
                        del h5file[f'{group_name}']
                    except Exception:
                        pass
                    nxData = h5file.require_group(f'{group_name}')
                    dset = nxData.require_dataset('maps', data = mydata, shape =mydata.shape, dtype=np.uint32, maxshape=(None,None,None), chunks=True, compression="gzip",compression_opts=4)
                    for exp_attr in dict_metadata_one_adc:
                        dset.attrs[exp_attr] = dict_metadata_one_adc[exp_attr]
                        
                    #dset = h5file.require_dataset(group_name, data = mydata, shape =mydata.shape, dtype=np.uint32, maxshape=(None,None,None), chunks=True, compression="gzip",compression_opts=4)
        h5file.close()

    def edf_To_hdf5(edfpath, detname, parameter, FinalHDF,num_det):
        edfout = EdfFile.EdfFile(edfpath)
        stack = EDFStack.EDFStack()
        stack.loadIndexedStack(edfpath)
        # self.detector
        edfheader = edfout.GetHeader(0)
        edfshape = edfout.GetStaticHeader(0)
        # edfout2 = EdfFile.EdfFile(edfpath, 'rb')
        # image1 = np.zeros((int(edfshape['Dim_2']), 10, int(edfshape['Dim_1'])), 'u4')
        image1 = edfout.GetData(0)
        edfshape = edfout.GetStaticHeader(0)
        det_aglae = ["LE0", "HE1", "HE2", "HE3", "HE4", "HE10", "HE11", "HE12", "HE13", "RBS", "RBS150", "RBS135",
                     "GAMMA", "GAMMA70", "GAMMA20", "IBIL", "FORS"]
        # for det in det_aglae :
        #   if detname == det:

        AGLAEfunction.write_hdf5(stack.data, edfpath, detname, FinalHDF,num_det)

    def write_hdf5_metadata(Pathfile,parametre,detname,FinalHDF):
        # f = h5py.File('./Data/ReadLst_GZIP.hdf5', 'w')
        head_tail = os.path.split(Pathfile)# Split le Path et le fichier
        destfile = head_tail[1].split(".")
        newdestfile = destfile[0] + ".hdf5"
        index_iba= destfile[0].find("_IBA_")
        index_l1 = destfile[0].find("_L1_")
        index_xrf = destfile[0].find("_XRF1_:")
        det_aglae = ["X0", "X1", "X2", "X3", "X4", "X10", "X11","X12","X13","RBS","RBS150","RBS135","GAMMA","GAMMA70","GAMMA20","IBIL","FORS"]
        iba_para = False

        for det1 in det_aglae:
            if detname == det1:
                iba_para = True


     #   if index_l1 > 0:
      #  elif index_xrf > 0:




        if destfile[1] == 'lst':
            newdestfile = destfile[0] + ".hdf5"
        

        newdestfile1 =  os.path.join(head_tail[0] , FinalHDF)

        # print(newdestfile)
        try:
            f = h5py.File(newdestfile1, 'a')

        except:
             f = h5py.File(newdestfile1, 'w')
        try:
            del f["parametres"]
        except:
            pass
        try:
            del f["stack/detector"]
        except:
            pass

        if iba_para == True:
            grp = f.create_group("parametres")
            grp.attrs["Date"] = parametre[0]
            grp.attrs["Projet"] = parametre[1]
            grp.attrs["Objet"] = parametre[2]
            grp.attrs["Particule"] = parametre[8]
            grp.attrs["Beam energy"] = parametre[9]
            grp.attrs["Map size X/Y (um)"] = '{} x {}'.format(parametre[3], parametre[4])
            grp.attrs["Pixel size X/Y (um)"] = "{} x {} ".format(parametre[5], parametre[6])
            grp.attrs["Pen size (um)"] = "{} ".format(parametre[7])
            #(\u03BC) code mu
            grp.attrs["Detector filter"] = "X0:{}, X1:{}, X2:{}, X3:{}, X4:{}".format(parametre[10], parametre[11],
                                                                                       parametre[12], parametre[13],
                                                                                       parametre[14])
            #print("HDF5 MetaData write")
        else:
        
            grp = f.create_group("parametres")
            grp.attrs["Date"] = parametre[0]
            grp.attrs["Objet"] = parametre[1]

        f.close()


    def finalhdf5(Pathfile,detname):
        head_tail = os.path.split(Pathfile)  # Split le Path et le fichier
        destfile = head_tail[1].split(".")
        newdestfile = destfile[0] + ".hdf5"
        index_iba = destfile[0].find("_IBA_")
        index_l1 = destfile[0].find("_L1_")
        index_xrf = destfile[0].find("_XRF1_:")
        det_aglae = ["LE0", "HE1", "HE2", "HE3", "HE4", "HE10", "HE11", "HE12", "HE13", "RBS", "RBS150", "RBS135",
                     "GAMMA", "GAMMA70", "GAMMA20", "IBIL", "FORS"]
        iba_para = False

        for det1 in det_aglae:
            if detname == det1:
                iba_para = True

        #   if index_l1 > 0:
        #  elif index_xrf > 0:
        Myname = []
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

        return FinalHDF

    def write_edf(self):
        image = np.zeros((10, 10, 2048), 'u4')
        image1 = np.zeros((10, 10, 2048), 'u4')
        #         GetData(self, Index, DataType="", Pos=None, Size=None):

        ddict = {}
        ddict['MCA a'] = "6.4"
        ddict['MCA b'] = "1"
        ddict['MCA c'] = "O"
        edfout = EdfFile.EdfFile("../test.edf")
        image = self.open_spe()
        edfout.WriteImage(ddict, image, Append=0)
        edfout2 = EdfFile.EdfFile("../test.edf", 'rb')
        image1 = edfout2.GetData(0)
        edfout1 = EdfFile.EdfFile("../test_read_write.edf", 'wb')
        edfout1.WriteImage(ddict, image1, Append=0)


    def listedfinfolder(edfpath):
        edfout = EdfFile.EdfFile(edfpath)



    def open_spe(self):
        """Ouvre un fichier PIXE
         Creation d'un fichier HDF5 avec les metadata issu du fichier X0
         contenant les data de la carto
         le spectre global de la carto

         """

        f = h5py.File('./myfile_GZIP.hdf5', 'w')
        #  dset1 = f.create_dataset("default", (100,),compression="gzip", compression_opts=9)
        # d1 = np.random.random(size=(1000, 20))

        mydata = np.zeros((10, 10, 2048), 'u4')  # numpy.array(10,2048)

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
            grp.attrs["dim2"] = len(data_spectre)
            x = np.arange(0, 2048, 1)

            x = x * (40 / 2048) + 0.5
            y = [int(i) for i in data_spectre]
            t = 10 * (np.random.rand(1) / 10)
            j = 0
            LE0 = np.array(y)

            while j < 3:  # Creation d'un tableau J,I de numpy pour ecriture dans HDF5 et EDF
                i = 0
                while i < 10:
                    new_y = y * (np.random.rand(1) / 100)
                    new_y = np.array(new_y, dtype='u8')
                    # y = val + val * (np.random.random() / 10)
                    mydata[j, i] = new_y
                    i += 1
                j += 1
            # mydata = np.array(y)
        dset = f.create_dataset("Data", data=mydata, dtype='u4', compression="gzip", compression_opts=9)
        dset.write_direct(mydata)
        dset2 = f.create_dataset("Total spectra LE0", data=LE0, dtype='u4', compression="gzip", compression_opts=9)
        dset2.write_direct(LE0)
        dset3 = f.create_dataset("Parametres", data=listpara, compression="gzip", compression_opts=9)
        dset3.write_direct(listpara)

        f.close()
        return mydata

    def open_hdf5(self):
        f = h5py.File('./myfile_No_GZIP.hdf5', 'r')
        # grp = f.create_group("parametres")
        cle = f.keys()
        for lescles in cle:
            i = +1

        par = f.require_group("parametres")
        par1 = par.attrs['Particule']
        dim1 = par.attrs['dim1']
        dim2 = par.attrs['dim2']
        spe = np.zeros((10, 10, 2048), 'u4')
        spe = f.get("data")

    #  dset = f.create_dataset("dset", (dim1,dim2), dtype='u8')
    #  arr = numpy.zeros((dim1,dim2), dtype='u8')
    #  dset.read_direct(arr) #, numpy.s_[0:10], numpy.s_[50:60])

    def open_header_edf(pathedf):
        import os
        # pathlst = "E:/21mai0106.lst"
        tmpheader = ""
        para2 = ""
        header1 = list()
        sizeX = 1
        sizeY = 1
        head_tail = os.path.split(pathedf)  # Split le Path et le fichier
        root_text = os.path.splitext(head_tail[1]) # Split le fichier et ext

        datainname = root_text[0].split("_")
        if len(datainname) > 4:
            dateacq = datainname[0]
            objetacq = datainname[2]
            projetacq = datainname[3]
        else:
            dateacq = datainname[0]
            objetacq = datainname[1]
            projetacq = "?"

        header1.append(dateacq)
        header1.append(objetacq)
        header1.append(projetacq)
        file_lst = open(pathedf, "rt",)
        file_lst.close()

        with open(pathedf, "rt", errors='ignore') as file_lst:
            import os
            size_lst = os.path.getsize(pathedf)

            while "   }" not in str(tmpheader) :
                try:
                    tmpheader = file_lst.readline()
                except UnicodeEncodeError:
                    pass

                            # Map size:1280,1280,64,64,0,2564,100000_
                if "COMMENTS =" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=' / ')
                    for newwpara in para:
                        para1 = str.split(newwpara, sep="= ")
                        header1.append(para1[1])
                    #regex = re.compile("[0-9]+\.[0-9]+")
                    #MyResultat = re.findall('\d',tmpheader)
                    #m = Matcher()

                    #MyResultat = matcher
                    #for newwpara in para:
                     #   header1.append(newwpara)
                if "DataType =" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=' = ')
                    para = str.split(para[1], sep=' ;')
                    header1.append(para[0])

                if "Dim_1 =" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=' = ')
                    para = str.split(para[1], sep=' ;')
                    header1.append(para[0])
                if "Dim_2 =" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=' = ')
                    para = str.split(para[1], sep=' ;')
                    header1.append(para[0])
                if "MCA a =" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=' = ')
                    para = str.split(para[1], sep=' ;')
                    header1.append(para[0])
                if "MCA b =" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=' = ')
                    para = str.split(para[1], sep=' ;')
                    header1.append(para[0])
                if "Size = " in str(tmpheader):
                    para = str.split(str(tmpheader), sep=' = ')
                    para = str.split(para[1], sep=' ;')
                    header1.append(para[0])
                    # header1.append(tmpheader)

        if len(header1) < 20:
            for i in range(7):
                header1.append("?")

        return header1

    @staticmethod
    def open_header_lst(pathlst:str):
        """Open the header of a .lst file and extract metadata."""
        import os
        # pathlst = "E:/21mai0106.lst"
        tmpheader = ""
        para2 = ""
        header1 = list()
                
        indexadc = -1
        adc_readed = np.array([0,0,0,0,0,0,0,0,0,0,0,0],dtype=bool)
        head_tail = os.path.split(pathlst)  # Split le Path et le fichier
        root_text = os.path.splitext(head_tail[1])  # Split le fichier et ext
        dict_adc_metadata_arr = np.full((20), {})
        dict_metadata_global = {}
        dict_metadata= {}
        toto = []
        end_adc = False
                
        datainname = root_text[0].split("_")
        if len(datainname) > 4:
            dateacq = datainname[0]
            num_analyse = datainname[1]
            objetacq = datainname[2]
            projetacq = datainname[3]
        else:
            dateacq = "?"
            objetacq = "?"
            projetacq = "?"

        t =0
        det_aglae = ["X0", "X1", "X3", "X4", "X10", "X11", "X12", "X13", "RBS", "RBS150", "RBS135",
                     "GAMMA", "GAMMA70", "GAMMA20", "IBIL", "FORS"]
        
        with open(pathlst, "r",errors='ignore') as file_lst:
            import os
            size_lst = os.path.getsize(pathlst)
            fin_header =False
            while fin_header ==False: 
                tmpheader = file_lst.readline()
                t+=1
                if t == 495:
                     t=t
                else:
                    t=t           
                # Map size:1280,1280,64,64,0,2564,100000_
                if "[ORS" in str.upper(tmpheader) or "[MAP" in str.upper(tmpheader): # Fin lecture ADC
                    end_adc = True


                if "[ADC" in str.upper(tmpheader): # Read metadata ADC1
                   mynumero = re.search(r'\[ADC(\d+)\]', tmpheader) #re.search(r'[ADC(\d+)]', tmpheader) 
                   indexadc = int(mynumero.group(1)) -1
                   dict_metadata.clear() #dict_metadata_arr[indexadc]
                   idx_metadata = 0
                   adc_readed[indexadc] = 1
            
                if indexadc == 0 and "REPORT-FILE from  written" in str(tmpheader): 
                    para = str.split(str(tmpheader), sep='written')
                    dict_metadata_global["timestamp"]= AGLAEfunction.clean_text(para[1])

                if "cmline1=" in str(tmpheader): # Nom detecteur
                    para = str.split(str(tmpheader), sep='=')
                    text_adc_name = AGLAEfunction.clean_text(para[1])
                    text_adc_name= text_adc_name.upper()
                    if text_adc_name in det_aglae:
                        dict_metadata["adc name"]= text_adc_name
                    else:
                        dict_metadata["adc name"]= "det. OFF"
                    

                    
#cmline2= detector:SDD Ketek ,dia:50mm2 ,window:4um Be, S/N:xxxxx, Angle:50° 
#cmline2= detector:pips ,dia:50mm2 ,window:4um Be, S/N:xxxxx, Angle:50° 

                if "DET:" in str.upper(tmpheader): # Info detecteur
                    para = str.split(str(tmpheader), sep='=')
                    para2 = str.split(para[1], sep=',') # 
                    par_det= str.split(para2[0], sep=':')
                    for i, text in enumerate(para2):
                        text = AGLAEfunction.clean_text(text)
                        text2 = str.split(text, sep=':')[1]
                        if "DET:" in str.upper(text):
                            dict_metadata["det. type"] = str.split(text, sep=':')[1]
                        if "AREA:" in str.upper(text):
                            dict_metadata["det. active area"]= str.split(text, sep=':')[1]
                        if "TCK:" in str.upper(text):
                            dict_metadata["det. thickness"] =str.split(text, sep=':')[1]
                        if "WIN:" in str.upper(text):
                            dict_metadata["det. entrance window"] =str.split(text, sep=':')[1]
                        if "ANGLE:"in str.upper(text) :
                            dict_metadata["det. angle"] =str.split(text, sep=':')[1]
                        if  "S/N:" in str.upper(text): 
                            dict_metadata["det. S/N"] =str.split(text, sep=':')[1]
                
                if "FILTER:" in str.upper(tmpheader): 
                    para = str.split(str(tmpheader), sep='=')
                    para2 = str.split(para[1], sep=',')
                    #para = str.split(str(tmpheader), sep=':')
                    #text = AGLAEFile.clean_text(para[1])  #remplace µ par u et supprime \\r\\n
                    for i, text in enumerate(para2):
                        text = AGLAEfunction.clean_text(text)
                        #dict_metadata["filter"] =text
                        if "WIN:" in str.upper(text):
                            dict_metadata["det. entrance window"] =str.split(text, sep=':')[1]
                        if "ANGLE:"in str.upper(text) :
                            dict_metadata["det. angle"] =str.split(text, sep=':')[1]
                        if "FILTER:"in str.upper(text) :
                            dict_metadata["det. filter"] =str.split(text, sep=':')[1]
                        if  "S/N:" in str.upper(text): 
                            dict_metadata["det. S/N"] =str.split(text, sep=':')[1]

                if "CALIBRATION:" in str.upper(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    text = AGLAEfunction.clean_text(para[1])
                    dict_metadata["calibration"] = text

                if "INSTITUTION:" in str.upper(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    text = AGLAEfunction.clean_text(para[1])  #remplace µ par u et supprime \\r\\n
                    dict_metadata_global["institution"] = text

                if "SAMP. INFO:" in str.upper(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    text = AGLAEfunction.clean_text(para[1])
                    dict_metadata_global["analyse description"] = text

                if "REF ANALYSE:" in str.upper(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    text = AGLAEfunction.clean_text(para[1])
                   # if "STANDARD:" in str.upper(text): #if text == "satndar":
                    dict_metadata_global["ref. analyse"] = text
                   # else:
                    #    dict_metadata_global["ref. object"] = text
                        

                if "USERNAME:" in str.upper(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    text = AGLAEfunction.clean_text(para[1])  
                    dict_metadata_global["username"] =text

                if "PRJ EUPHROSYNE:" in str.upper(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    text = AGLAEfunction.clean_text(para[1])  
                    dict_metadata_global["prj euphrosyne"] =text

                if "OBJ EUPHROSYNE:" in str.upper(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    text = AGLAEfunction.clean_text(para[1])  
                    dict_metadata_global["obj euphrosyne"] =text
                    if str.upper (text) == "STANDARD":
                        dict_metadata_global["target type"] = "standard"
                    else:
                        dict_metadata_global["target type"] = "object"


                if "MAP SIZE:" in str.upper(tmpheader):
                    para2 = str.split(str(tmpheader), sep=':')
                    para2 = str.split(para2[1], sep=",")
                    map_info = ["map size x (um)","map size y (um)","pixel size x (um)","pixel size y (um)","pen size (um)","dose/column","dose" ]
                    for i, text in enumerate(para2): 
                        text = AGLAEfunction.clean_text(text)
                        para2[i] = text
                        dict_metadata_global[map_info[i]] = text
                        
    #cmline7= calibration: MCA a= 1, MCA b= 1, MCA c= 0
              
                #cmline9= Exp.Info:Proton , 2976 keV        
                if "EXP.INFO" in str.upper(tmpheader): 
                    para2 = str.split(str(tmpheader), sep=':')
                    para2 = str.split(para2[1], sep=",")
                    para2 = para2[0:2]
                    beam_info = ["particle", "beam energy"]

                    for i, text in enumerate(para2): 
                        text = AGLAEfunction.clean_text(text)
                        dict_metadata_global[beam_info[i]] = text
                                     
             
                
                if np.any(adc_readed) == True and end_adc == False:
                    dict_adc_metadata_arr[indexadc] = dict_metadata.copy()
                    
                
                #toto.append(dict_metadata.copy())
                
                fin_header = '[LISTDATA]' in str.upper(tmpheader) or t > 5000
                # header1.append(tmpheader)
        # Info IBIL en constant
        dict_metadata= {}
        dict_metadata["spectro name"] = "IBIL"
        dict_metadata["calibration"] = "MCA a= 0.801, MCA b= 189.0, MCA c= 0"
        dict_metadata["spectro. S/N"]= "unknown"
        dict_metadata["spectro. angle"] = "45"
        dict_metadata["spectro. slit size"] = "100 um"
        dict_metadata["fiber diameter"] = "1000 um"
        dict_metadata["fiber S/N"] = "unknown"
        dict_metadata["spectro. type"] = "QE65000 Ocean Optics"
        dict_adc_metadata_arr[12] = dict_metadata.copy() # GAMMA

        return dict_adc_metadata_arr,dict_metadata_global
    

    def open_header_lst_simple(pathlst):
        import os
        # pathlst = "E:/21mai0106.lst"
        tmpheader = ""
        para2 = ""
        header1 = list()
        sizeX = 1
        sizeY = 1
        head_tail = os.path.split(pathlst)  # Split le Path et le fichier
        root_text = os.path.splitext(head_tail[1])  # Split le fichier et ext

        datainname = root_text[0].split("_")
        if len(datainname) > 4:
            dateacq = datainname[0]
            objetacq = datainname[2]
            projetacq = datainname[3]
        else:
            dateacq = "?"
            objetacq = "?"
            projetacq = "?"

        header1.append(dateacq)
        header1.append(objetacq)
        header1.append(projetacq)
        t =0    
        with open(pathlst, "rb") as file_lst:
            import os
            size_lst = os.path.getsize(pathlst)
            fin_header =False
            while fin_header ==False: # != b'[LISTDATA]\r\n' or tmpheader != b'[LISTDATA]\n':
                tmpheader = file_lst.readline()
                t+=1
                if t == 615:
                     t=t
                else:
                    t=t           
                # Map size:1280,1280,64,64,0,2564,100000_
                if "Map size" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    para = str.split(para[1], sep=",")
                    for newwpara in para:
                        newwpara = newwpara.replace("\\n", '')
                        newwpara = newwpara.replace("'", '')
                        if len(header1) < 8:
                            header1.append(newwpara)
                        

                if "Exp.Info" in str(tmpheader):
                    para2 = str.split(str(tmpheader), sep=':')
                    para2 = str.split(para2[1], sep=",")

                    for i, text in enumerate(para2):  # remplace le code \\xb5 mu par la lettre u pour um
                        text = text.replace("\\xb5", 'u')
                        text = text.replace("\\r\\n", '')
                        text = text.replace("\\", 'jj')
                        para2[i] = text
                        header1.append(text)

                    para = para + para2
                fin_header = tmpheader == b'[LISTDATA]\r\n' or tmpheader == b'[LISTDATA]\n' or t > 5000
                # header1.append(tmpheader)
        if len(para2) == 0:
            for i in range(7):
                header1.append("?")

        return header1
    
    @staticmethod
    def clean_text(text):
        """Nettoie le texte en remplaçant les caractères spéciaux et en supprimant les retours à la ligne."""
        text = text.replace("\\xb5", 'u')
        text = text.replace("\r\n", '')
        text = text.replace('\n', '')
        text = text.replace("\\", 'jj')
        text = text.strip()
                        
        return text
    def return_adc_adjusted_index(data_array_previous,data_array):

        data_array = data_array[data_array != 65535]
        data_array = np.append(data_array_previous, data_array)
        min_last_pos_x_y_in_array = np.shape(data_array)
        shape_data_array = int(min_last_pos_x_y_in_array[0])
        # Recherche de la valeur 0x8000 (32768) dans le tableau de donnees
        indices_32768 = np.where(data_array == 32768)
        indices_32768 = np.array(indices_32768[0])
        indices_32768 = np.delete(indices_32768, len(indices_32768) - 1)
        # Cr�ation d'indices ajust�s et filtrage
        one_array = np.full(np.shape(indices_32768), 1)
        adjusted_indices = indices_32768 - one_array
        return adjusted_indices, data_array ,shape_data_array
    def get_X_Y_condition(adc_values,ADC_X,ADC_Y):
        coord_X_masket = np.bitwise_and(adc_values[:], 0b0000000000000001 << ADC_X)
        coord_Y_masket = np.bitwise_and(adc_values[:], 0b0000000000000001 << ADC_Y)
        conditionX = coord_X_masket[:] != 0
        conditionY = coord_Y_masket[:] != 0
        conditionXY = np.logical_and(conditionY, conditionX)
        return conditionXY

    
    def return_index_adc_in_data_array(adjusted_indices,adc_values,num_line_adc,conditionXY):
        """ Retourne tout les indices des ADC dans DataArray"""
        
        # Op�rations bitwise et filtrage des indices
        adc_masked = np.bitwise_and(adc_values[:], 0b0000000000000001 << num_line_adc)
        conditionADC = (adc_masked != 0) 
        condition_final = np.logical_and(conditionADC, conditionXY)
        filtered_indices = np.where(condition_final, adjusted_indices[:],
                                     np.full(len(condition_final), -1, dtype=np.int16))
        non_zero_indices = filtered_indices[filtered_indices != -1]
        
        if len(non_zero_indices) < 10:
           return [-1]
        # Convert `non_zero_indices` to a NumPy array for better performance
        non_zero_indices = np.array(non_zero_indices)
        return non_zero_indices

    def return_val_to_read(adc_words,non_zero_indices):

        ind10 = []
        bit_count_array = np.empty(len(adc_words), dtype=np.uint32)
        qui_a_declanche = np.empty((12, len(adc_words)), dtype=np.uint32)
        # Loop through each bit position and count the bits set to 1
        for bit_position in range(12):
            # Create a mask for the current bit position
            bit_mask = 0b0000000000000001 << bit_position
            # Use bitwise AND to check if the current bit is set
            adc_declanche = adc_words & bit_mask
            bit_count_array += adc_declanche > 0
            ind10 = np.where(adc_declanche != 0, non_zero_indices + 1, np.zeros(len(adc_declanche)))
            qui_a_declanche[bit_position, :] = ind10

        del ind10

        compteur_valeur = np.empty((12, len(adc_words)), dtype=np.uint8)
        mysum = np.zeros((1, len(adc_words)), dtype=np.uint8)
        # for arr in qui_a_declanche:
        #          zero_els = jnp.count_nonzero(arr == 0)
        del adc_words

        for x in range(12):  # 15, -1,-1):
            # r= np.where(qui_a_declanche[x,:] !=0, qui_a_declanche[x,:] - bit_count_array[:],qui_a_declanche[x,:])
            compteur_valeur[x, :] = np.where(qui_a_declanche[x, :] != 0, mysum + 1, qui_a_declanche[x, :])
            mysum = np.where(compteur_valeur[x, :] != 0, mysum + 1, mysum)

        indice_val_to_read = qui_a_declanche + compteur_valeur  # np.full(len(compteur_valeur),1)
        return indice_val_to_read

    def read_min_max_y(coord_y):
        """ recherche la derniere valeur de Y du tableau en Input"""
        last_pos_y = np.empty(0, dtype=np.uint16)
        if len(coord_y) > 300:
            r1 = 300
        else:
            r1 = len(coord_y) -1

        for pos in range(r1):
            last_pos_y = np.append(last_pos_y, coord_y[-pos+1])

        max_val_y_lue = np.max(last_pos_y)
        min_val_y_lue = np.min(last_pos_y)
        nb_max_value = np.count_nonzero(last_pos_y == max_val_y_lue)
        if nb_max_value > 2:
            max_val_y_lue = max_val_y_lue
        else:
            max_val_y_lue = min_val_y_lue


        return max_val_y_lue,min_val_y_lue

    def min_max_coordx(coord_x,croissant):
        
        local_max_x = np.max(coord_x)
        local_min_x = np.min(coord_x)
        nb_max = np.where(coord_x == local_max_x)
        nb_min = np.where(coord_x == local_max_x)
        if len(nb_max[0] > 10):
            last_x_value = local_max_x
        
        if len(nb_min[0] > 10):
            first_x_value = local_min_x

        
        return first_x_value, last_x_value

    def read_range_x(coord_x,croissant):
        local_max_x = np.max(coord_x)
        last_pos_x = np.empty(0, dtype=np.uint16)
        first_pos_x = np.empty(0, dtype=np.uint16)
        if len(coord_x) > 100:
            r1 = 100
        else:
            r1 = len(coord_x) -1

        for pos in range(r1):
            if croissant == True:
                last_pos_x = np.append(last_pos_x, coord_x[-pos-1])  # A partir de la fin
                first_pos_x = np.append(first_pos_x, coord_x[pos])  # A partir du debut
            else:
                last_pos_x = np.append(last_pos_x, coord_x[pos])  # A partir du debut
                first_pos_x = np.append(first_pos_x, coord_x[-pos-1])  # A partir de la fin

        last_pos_x = np.delete(last_pos_x, 0)
        count_x = np.bincount(last_pos_x)
        last_x_value = int(np.shape(count_x)[0]) - 1 # On enleve la derniere colonne

        
        count_x_min = np.bincount(first_pos_x)
        first_x = np.where(count_x_min == max(count_x_min))
        try:
            first_x_value = int(first_x[0]) 
        except:
            first_x_value = int(first_x[0][0]) # plusieurs valeur superieur X identique , on prend la 1ere

        return first_x_value, last_x_value

        
    def read_indice_max_x(croissant,coord_x,included_x):
        """Recherche la derniere valeur de X du tableau en Input"""              
        indice_x_max = np.where(coord_x == included_x)
        len_x_max = len(np.shape(indice_x_max[0]))
        if len_x_max < 1: #Pas ce X dans le Dataarray , faisceau OFF ?"

            while len_x_max < 1:
                if croissant == True:
                    included_x -=1
                else:
                    included_x +=1
                indice_x_max = np.where(coord_x == included_x)
                len_x_max = len(np.shape(indice_x_max[0]))    

        if croissant == True:
            try:
                indice_x_last = indice_x_max[0][-1]
            except:
                indice_x_last = indice_x_max[-1]
        else:
            try:
                indice_x_last = indice_x_max[0][-1]
            except:
                indice_x_last = indice_x_max[-1]

    
        return indice_x_last
    
    
    def read_min_x(coord_x, croissant, previous_last_x):
        """Recherche la derniere valeur de X du tableau en Input"""
        last_pos_x = np.empty(0, dtype=np.uint16)
        first_pos_x = np.empty(0, dtype=np.uint16)
        for pos in range(100):

            if croissant == True:
                last_pos_x = np.append(last_pos_x, coord_x[-pos-1])  # A partir de la fin
                first_pos_x = np.append(first_pos_x, coord_x[pos])  # A partir du d�but
            else:
                last_pos_x = np.append(last_pos_x, coord_x[pos])  # A partir du d�but
                first_pos_x = np.append(first_pos_x, coord_x[-pos-1])  # A partir de la fin



        last_pos_x = np.delete(last_pos_x, 0)
        count_x = np.bincount(last_pos_x)
        last_x = int(np.shape(count_x)[0]) - 1  # On enleve la derni�re colonne
        if len(first_pos_x) == 0:
            count_x_min = 0
        else:
            try:
                count_x_min = np.bincount(first_pos_x)
                first_x = np.where(count_x_min == max(count_x_min))
                first_x_value = int(first_x[0])

            except:
                first_x_value = 0

        return first_x_value

    def read_max_indice_change_colonne(coord_y,y_scan_total):
        """Recherche la derniere valeur de Y du tableau en Input"""
        fin_ligne = False
        indice_y_last = np.where(coord_y > y_scan_total)  # recherche les val de la dernier colonne
        if len(indice_y_last[0]) < 50:
            fin_ligne = True
            indice_last = 0
        indice_last = indice_y_last[0][0] - 1
        return indice_last

    def get_colums_range(croissant,first_x_value,last_x_value):
        """True si plusieurs column dans le Data array"""
        columns = False
        if croissant== True:
            columns = last_x_value > first_x_value
        else:
            columns = first_x_value < last_x_value
        return columns


    def clean_coord(sizeX,sizeY,coord_x,coord_y,b_previous_find_x,previous_find_x):
        error_y =False
        max_size_x = ret_range_bytes(sizeX - 1)
        max_size_y = ret_range_bytes(sizeY - 1)
        coord_x = coord_x & max_size_x  # & binaire pour masquer bits > max_size à 0
        c1 = coord_y
        c1 = c1[c1 != 0]
        
        if len(c1) < 100:
            error_y = True
        coord_y = coord_y & max_size_y 

        # Met des -1 aux coord X et Y > valeur de la carto
        val_out_range_x = np.where(coord_x > sizeX - 1)
        coord_x = np.delete(coord_x, val_out_range_x)
        coord_y = np.delete(coord_y, val_out_range_x)
        if b_previous_find_x == True:
            val_out_range_x = np.where(coord_x == previous_find_x)
            coord_x = np.delete(coord_x, val_out_range_x)
            coord_y = np.delete(coord_y, val_out_range_x)
    
    
        return coord_x,coord_y,error_y


    def all_clean_coord(sizeX,sizeY,coord_x,coord_y):
        """Nettoie les coordonnées X et Y en fonction de la taille de la cartographie."""
        error_y =False
        max_size_x = ret_range_bytes(sizeX - 1)
        max_size_y = ret_range_bytes(sizeY - 1)
        coord_x = coord_x & max_size_x  # & binaire pour masquer bits > max_size à 0
        c1 = coord_y
        c1 = c1[c1 != 0]
        
        if len(c1) < 100:
            error_y = True
        coord_y = coord_y & max_size_y 

        # Met des -1 aux coord X et Y > valeur de la carto
        val_out_range_x = np.where(coord_x > sizeX - 1)
        coord_x = np.delete(coord_x, val_out_range_x)
        coord_y = np.delete(coord_y, val_out_range_x)

  
        return coord_x,coord_y,error_y

    def search_min_x_all_adc(array_adc,adc_values,conditionXY,adjusted_indices,data_array,
                             ADC_X,ADC_Y,sizeX,sizeY,croissant,y_max_current_scan,
                             b_previous_find_x,previous_find_x,end_lst_file_found):
        """ recherche la derniere valeur de X, nb adc et changement de line du tableau en Input pour tous les ADC et retourne le minimum trouvé"""
        if croissant == True:
            final_x_found = 0
        else:
            final_x_found = sizeX-1
            
        nb_adc_not_found =0
        for num_line_adc in array_adc: #range(12):
                        sleep(0.002)
                        if num_line_adc == 1 or num_line_adc == 8 or num_line_adc == 9 or num_line_adc == 55: continue

                        non_zero_indices = AGLAEfunction.return_index_adc_in_data_array(adjusted_indices,adc_values,num_line_adc,conditionXY)
                        if non_zero_indices[0] == -1 or len(non_zero_indices) < 50:
                            nb_adc_not_found +=1
                            continue
                        adc_words = data_array[non_zero_indices]  # -1 car on veut la valeur avant le mot ADC
                        indice_val_to_read = AGLAEfunction.return_val_to_read(adc_words,non_zero_indices)

                        coord_x = data_array[indice_val_to_read[ADC_X, :]]  
                        coord_y = data_array[indice_val_to_read[ADC_Y, :]]
                       
                        coord_x, coord_y,error_y = AGLAEfunction.clean_coord(sizeX, sizeY,coord_x,coord_y,b_previous_find_x,previous_find_x) # del 
                        max_val_y_lue,min_val_y_lue = AGLAEfunction.read_min_max_y(coord_y)
                        change_line = look_if_next_line(max_val_y_lue,y_max_current_scan)
                        first_x_value, last_x_value = AGLAEfunction.read_range_x(coord_x, croissant)
                            
                        if croissant == True:
                            _1st_x_found = first_x_value
                            if (last_x_value - 1) >= 0 and last_x_value - 1 >= final_x_found and end_lst_file_found == False:
                                final_x_found = last_x_value -1 # Ignore la dernière valeur de X qui est souvent erronée
                            else:
                                final_x_found = last_x_value # sauf en cas de end LST file ou on prend la valeur de X max trouvée
                         
                        else:
                            _1st_x_found = last_x_value
                            if first_x_value + 1 <= sizeX and first_x_value + 1 <= final_x_found and end_lst_file_found == False:
                                final_x_found = first_x_value + 1
                            else:
                                final_x_found = first_x_value

        return final_x_found, _1st_x_found,nb_adc_not_found,change_line
    
    @staticmethod    
    def resource_path(relative_path):
        """Obtenir le chemin absolu vers une ressource, fonctionne pour dev et build PyInstaller"""
        # try:
        #     base_path = sys._MEIPASS
        # except AttributeError:
        #     base_path = os.path.abspath(".")

        base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    @staticmethod    
    def read_cfg_adc(path=None):
        dict_channel_adc = {}
        dict_config_mpawin_adc = {} 
        dict_combined_adc = {}
        
        if not path: path = 'config_lst2hdf5.ini'

        try :
            config = configparser.ConfigParser()
            config.read(path)  # Utilise resource_path pour trouver le fichier de configuration
            config.sections()

            section_name = 'PACKED_DATA_SIZE'
            for key, value in config[section_name].items():
                print(f"{key}: {value}")
                dict_channel_adc[key] = value

            section_name = 'NB_CHANNEL'
            for key, value in config[section_name].items():
                print(f"{key}: {value}")
                dict_channel_adc[key] = value
            # Lecture des valeurs de la section MPAWIN
            
            section_name = 'CFG_MPAWIN'
            for key, value in config[section_name].items():
                print(f"{key}: {value}")
                dict_config_mpawin_adc[key] = value
            
            section_name = 'CFG_CONBINED'
            for key, value in config[section_name].items():
                print(f"{key}: {value}")
                dict_combined_adc['combined' + key] = value

        except Exception as e:
            print(f"Erreur lors de la lecture du fichier de configuration : {e}")
            dict_config_mpawin_adc = {0: "X1", 1: "OFF", 2: "X3", 3: "OFF", 4: "X0", 
                                  5: "OFF", 6: "RBS135", 7: "RBS150", 8: "Coord_X", 9: "Coord_Y",
                                    10: "GAMMA20", 11: "GAMMA70"}
            dict_channel_adc = {"PIXE": 2048, "RBS": 512, "GAMMA20": 2048, "GAMMA70": 4096}
            dict_combined_adc ={12: "X1+X2",13: "X1+X3",14: "X1+X4",23: "X2+X3",134:"X1+X3+X4",
                            34: "X3+X4",1234:"X1+X2+X3",10: "X1+X2+X3+X4"}
            dict_channel_adc["nb_column"] = 6 

        return dict_channel_adc,dict_config_mpawin_adc,dict_combined_adc
    
# Fonction d'extraction du fichier LST avec vectorisation
    #def extract_lst_vector(path_lst, detector, para, ADC_X = 8, ADC_Y = 9):

    @staticmethod
    def extract_lst_vector(MyProgressBar,path_lst:str, dict_para_global,_dict_adc_metadata_arr,progress_val=0):
        pathlst1 = path_lst
        progress = MyProgressBar.value()
        _dict_channel_adc,_dict_config_mpawin_adc,_dict_combined_adc = AGLAEfunction.read_cfg_adc(AGLAEfunction.resource_path("config_lst2hdf5.ini"))
        print(_dict_channel_adc)
       
        #array_adc = [0,2,3,4,6,7,10,11]
        array_adc = []
        for key,value in _dict_config_mpawin_adc.items():
               if str.upper(value) == "COORD_X":
                   ADC_X= int(key)
               elif str.upper(value) == "COORD_Y": 
                   ADC_Y= int(key)
               elif str.upper(value) != "OFF":
                   array_adc.append(int(key))

        #array_adc =np.flip(array_adc)
        #array_adc.append(1)
        print("ADC used :",array_adc)
        
        tmpheader = ""
        header1 = list()
        sizeX = 1
        sizeY = 1
        #print(path_lst)
        print("map size = ",dict_para_global['map size x (um)'], dict_para_global['map size y (um)'])
        
        sizeX = int(dict_para_global['map size x (um)']) / int(dict_para_global['pixel size x (um)'])
        sizeY = int(dict_para_global['map size y (um)']) / int(dict_para_global['pixel size y (um)'])
        sizeX = int(sizeX)
        sizeY = int(sizeY)
   
        adcnum = []
        

        nbcanaux = 1024
        nbcanaux_pixe = int(_dict_channel_adc['pixe'])
        nbcanaux_gamma20 = int(_dict_channel_adc['gamma20'])
        nbcanaux_gamma70 = int(_dict_channel_adc['gamma70'])
        nbcanaux_rbs = int(_dict_channel_adc['rbs'])
    
       # nbcanaux = switcher.get(detector)
        # cube = np.zeros((sizeX, sizeY, nbcanaux), 'u4')
        ## for i in range (0,50):
        file = open(path_lst, 'rb')
        size_lst = getSize(file)
        file.close()
        allheader = ""
        fin_header = False
        t=0
        error_in_lst_file = False

        with open(path_lst, "rb") as file_lst:  # Trop long
            while fin_header == False: #tmpheader != b'[LISTDATA]\r\n':
                tmpheader = file_lst.readline()
                tmp1 = str(tmpheader)
                allheader = allheader + tmp1.replace("\\r\\n", '')
                t+=1    
                size_lst -= len(tmp1) - 2
                if "condition" in str(tmpheader):
                    toto = 1
              
                fin_header = tmpheader == b'[LISTDATA]\r\n' or tmpheader == b'[LISTDATA]\n' or t > 5000
                # header1.append(tmpheader)
           
            pensize = int(dict_para_global["pen size (um)"])
            nb_pass_y = int(sizeY / (pensize / int(dict_para_global["pixel size y (um)"])))
            nb_column_total = sizeX*nb_pass_y
           
        
   
            size_lst = int(size_lst)  # car on lit des Uint16 donc 2 fois moins que le nombre de bytes (Uint8)
            size_block = size_lst
            size_one_scan = size_lst / nb_pass_y
            size_4_column_scan = size_one_scan / (sizeX/(sizeX/4))  # taille 4 column
            # if size_4_column_scan < 10*10**6 and sizeX > 20:
            #     size_4_column_scan = size_one_scan / (sizeX/8) # taille 8 column 

            size_block = int(size_4_column_scan)

            nb_col = 2
            if size_lst < 5*10**6:
                nb_col = np.int16((nb_column_total /nb_pass_y )/6)
            else:
                nb_col = 6

            size_one_scan = size_lst / (nb_pass_y)
            size_4_column_scan = (size_one_scan / (sizeX)) * nb_col #/(sizeX/40))  # taille 4 column
            size_block = int(size_4_column_scan)
            
            # if nb_pass_y == 1 and size_lst < 50*10**6: 
            #     size_block = size_lst
            # # size_block = 100000
            # nb_read_total = 0
            
            
            if size_lst > size_block:
                nb_loop = int(size_lst / size_block)
                nb_loop += 1
                reste = size_lst % size_block
            else:
                nb_loop = 1
                reste = 0
                nb_pass_y = 1
            
            y_scan = int(sizeY / nb_pass_y) - 1
            nb_column = int(sizeY / nb_pass_y)

            nb_byte_to_read = size_block
            indice_in_datablock = 0
            nb_read_total = 0
            max_val_y_lue = 0
            croissant = True
            data_array_previous = np.empty(0, dtype=np.uint16)
            end_lst_file_found = False
            last_x_maps = 0
            columns = True
            nb_adc_not_found = 0
            
            if nb_pass_y % 2 == 0:
                last_x_maps = 0
            else:
                last_x_maps = sizeX - 1

            nb_total_event = 0

                    # Main loop to read the LST file and build the data cube par line
            for num_pass_y in range(nb_pass_y):
                print(num_pass_y ,"//",nb_pass_y)

                if end_lst_file_found==True: # fin LST avant fin de la taille de la carto (ABORT sur New Orion)
                    break   
                if (num_pass_y % 2 == 0):
                    croissant = True
                    next_x_value = np.zeros(12, dtype=np.uint16)

                else:
                    croissant = False
                    next_x_value = np.full(12, sizeX - 1, dtype=np.uint16)


                end_lst_file_found = False
                y_max_current_scan = y_scan + (num_pass_y * nb_column)

                # nbcanaux_pixe = 2048
                # nbcanaux_gamma20 = 2048
                # nbcanaux_gamma70 = 2048
                # nbcanaux_rbs = 512
                cube_one_pass_pixe = np.empty((5, nb_column, sizeX, nbcanaux_pixe), dtype=np.uint32)
                cube_one_pass_gamma20 = np.empty((1, nb_column, sizeX, nbcanaux_gamma20), dtype=np.uint32)
                cube_one_pass_gamma70 = np.empty((1, nb_column, sizeX, nbcanaux_gamma70), dtype=np.uint32)
                cube_one_pass_rbs = np.empty((3, nb_column, sizeX, nbcanaux_rbs), dtype=np.uint32)

                fin_ligne = False
                change_line= False
                zero_off = False
                previous_find_x = 0
                b_previous_find_x = False
                array_adc = [0,1,2,3,4,5,6,7,10,11]
                    
                while (fin_ligne == False and end_lst_file_found == False):  # max_val_y_lue <= y_scan): # or croissa nte == False ):

                    adc2read = 0
                    adc_values = np.empty(0, dtype=np.uint16)
                    data_array = np.empty(0, dtype=np.uint16)
                    adjusted_indices = np.empty(0, dtype=np.uint16)
                    adjusted_indices_previous = np.empty(0, dtype=np.uint16)
            
                    nb_byte_to_read = size_block
                              
                    min_last_pos_x_y_in_array = 0 #nb_byte_to_read
                    data_array = np.fromfile(file_lst, dtype=np.uint16, count=int(nb_byte_to_read))
                    progress += int((len(data_array)*2)*(progress_val/size_lst))
                    MyProgressBar.setValue(progress)
                    sleep(0.002)
                    if len(data_array) < nb_byte_to_read:
                        end_lst_file_found = True
                        print("\n End LST file found",end='\n' )
                    
                    nb_32768 = np.count_nonzero(data_array == 32768)
                    nb_total_event = nb_total_event + nb_32768
                    
                    #""" Process Data Array to extract ADC values and coordinates"""
                    adjusted_indices, data_array ,shape_data_array = AGLAEfunction.return_adc_adjusted_index (data_array_previous, data_array)

                    adc_values = np.array(data_array[adjusted_indices])
                    if len(data_array) < 1 : 
                        exit 

                    nb_read_total += (nb_byte_to_read * 2) + len(data_array_previous)

                    print("progress : ", progress, "%", end='\n')
                    conditionXY= AGLAEfunction.get_X_Y_condition(adc_values,ADC_X,ADC_Y)
                    nb_adc_not_found = 0
                    last_indx_x = 0
                    next_x_value_col = 0
                    first_adc_in_block = False
                    #"""returne min X pour tous les ADC"""
                    last_x_in_array,_1st_x_found, nb_adc_not_found,change_line= AGLAEfunction.search_min_x_all_adc(array_adc,adc_values,conditionXY,
                                                                                                                    adjusted_indices,data_array,ADC_X,ADC_Y,
                                                                                                                    sizeX,sizeY,croissant,y_max_current_scan,
                                                                                                                    b_previous_find_x,previous_find_x,end_lst_file_found)
                    nb_adc_not_found = 0
                    first_adc_in_block = True
                    val_x_fin_map = get_x_end_line_scan(croissant,sizeX)

                    # Cas particulier X dans le block pas present (faisceau OFF) ou dernier colonne (0 et sizeX-1)
                    if change_line == True:
                        if croissant == True:
                            last_x_in_array = sizeX-1
                        else:
                            last_x_in_array = 0
                    else:
                        if last_x_in_array == 0 and croissant == False and end_lst_file_found == False and change_line == False:
                            last_x_in_array = 1

                        if last_x_in_array == sizeX-1 and croissant == True and end_lst_file_found == False and change_line == False:
                            last_x_in_array = sizeX -2
                    
                    if croissant:
                        first_x_value = _1st_x_found
                        last_x_value = last_x_in_array

                    else:
                        first_x_value = last_x_in_array
                        last_x_value = _1st_x_found
                    print("minimum x = {} , maximum x = {}".format(first_x_value, last_x_value), end='\n')
                
                    for num_line_adc in array_adc: #range(12):
                        sleep(0.002)
                        if num_line_adc == 1 or num_line_adc == 8 or num_line_adc == 9 or num_line_adc == 55: continue

                        switcher = {5: nbcanaux_pixe, 0: nbcanaux_pixe, 1: nbcanaux_pixe, 2: nbcanaux_pixe, 3: nbcanaux_pixe, 4: nbcanaux_pixe, 80: nbcanaux_pixe, 81: nbcanaux_pixe,
                                    82: nbcanaux_pixe, 6: nbcanaux_rbs, 7: nbcanaux_rbs, 10: nbcanaux_gamma20, 11: nbcanaux_gamma70}
                        nbcanaux = switcher.get(num_line_adc)
                        detector = ret_adc_name(num_line_adc)
                        adc2read = num_line_adc + 1
                        # adc2read = ret_num_adc(self.detector)
                        t0 = perf_counter()
                        # Return 
                        non_zero_indices = AGLAEfunction.return_index_adc_in_data_array(adjusted_indices,adc_values,num_line_adc,conditionXY)
                       
                       # Si aucuns events pour cet ADC dans ce block de data array , on passe au suivant
                        if non_zero_indices[0] == -1:
                            nb_adc_not_found +=1
                            continue

                        adc_words = data_array[non_zero_indices]
                        indice_val_to_read = AGLAEfunction.return_val_to_read(adc_words,non_zero_indices)

                        coord_x = data_array[indice_val_to_read[ADC_X, :]]  
                        coord_y = data_array[indice_val_to_read[ADC_Y, :]] 
                        coord_x, coord_y ,error= AGLAEfunction.clean_coord(sizeX,sizeY,coord_x,coord_y,b_previous_find_x,previous_find_x) # del 
                                             
                        if coord_x[0] !=0: x_zero_error = np.where(coord_x ==0) # Recherche si des X=0  présents dans X !=0

                        max_val_y_lue,min_val_y_lue = AGLAEfunction.read_min_max_y(coord_y)
                       
                        if first_x_value !=0 and len(x_zero_error[0]) > 1: #coord_X =0 anormal
                            coord_x = np.delete(coord_x, x_zero_error)
                            coord_y = np.delete(coord_y, x_zero_error)
                            first_x_value, last_x_value = AGLAEfunction.read_range_x(coord_x, croissant)
                                

                        #change_line = look_if_next_line(max_val_y_lue,y_max_current_scan) #True or False si Changement de Y sup.
                        # val_x_fin_map = get_x_end_line_scan(croissant,sizeX) # retourne val final 0 ou SizeX-1
                        
                        if change_line == False:
                            fin_lst = look_if_end_lst(max_val_y_lue,sizeY,val_x_fin_map,last_x_value)
                        elif change_line == True:
                            if croissant:
                                last_x_value = sizeX - 1
                            else:
                                first_x_value = 0
                        else:
                            fin_lst = False # change line -> fin lst impossible
                       
                    #    # Dertermine la dernière valeur X
                    #     included_x = get_last_x_to_include(croissant, columns, last_x_value,first_x_value,change_line,fin_lst)
                    #     columns= get_colums_range(croissant,first_x_value,last_x_value,included_x,end_lst_file_found)

                         # Dertermine la dernière valeur X
                        if first_adc_in_block == True:
                            first_adc_in_block = False
                            #included_x =last_x_in_array# AGLAEfunction.get_last_x_to_include(croissant, columns, last_x_value,first_x_value,change_line,fin_lst)
                            columns= AGLAEfunction.get_colums_range(croissant,first_x_value,last_x_value)
                                                   
                            if last_x_value < first_x_value and croissant==True: # Cas trop lus de columns
                                last_x_value = sizeX-1
                                columns= AGLAEfunction.get_colums_range(croissant,first_x_value,last_x_value)
                            
                            if first_x_value > last_x_value and croissant==False: # Cas trop lus de columns
                                first_x_value = 0
                                columns= AGLAEfunction.get_colums_range(croissant,first_x_value,last_x_value)
           
                       
                        if end_lst_file_found == True or fin_lst == True:
                                 indice_last = len(coord_y) -1
                        else:
                            if columns == True and change_line == False: # plus de 1 colonne
                                indice_last = AGLAEfunction.read_indice_max_x(croissant,coord_x,last_x_in_array)#,next_x_value[num_line_adc])
                            elif columns == False and change_line == False: # 1 Colonne
                                indice_last = AGLAEfunction.read_indice_max_x(croissant,coord_x,last_x_in_array)#,next_x_value[num_line_adc])
                            elif change_line == True:
                                indice_last = AGLAEfunction.read_max_indice_change_colonne(coord_y,y_max_current_scan) #Recherche last_indice avec Y < scan total
                                fin_ligne = True
                           
                        # if first_adc_in_block == True:
                        #     first_adc_in_block = False
                        #     if croissant == True:
                        #         print("X:", first_x_value,"To",last_x_in_array,end=",")
                        #         sleep(0.02)
                                
                        #     else:
                        #         print("X:", last_x_value,"To",last_x_in_array,end=",")
                        #         sleep(0.02)
                
                        #         if last_x_in_array == 25:
                        #             last_x_in_array = 25
                            
                        max_data_array = indice_val_to_read[ADC_X, indice_last]
                        coord_x = coord_x[:indice_last]
                        coord_y = coord_y[:indice_last]

                        if max_data_array > min_last_pos_x_y_in_array:
                                min_last_pos_x_y_in_array = max_data_array

                 
                        non_zero_indices = np.nonzero(indice_val_to_read[num_line_adc, :indice_last])
                        if len(non_zero_indices[0]) < 2:  # pas de valeur pour cet adc dans ce Block de Data Array
                            continue

                        adc1 = data_array[indice_val_to_read[num_line_adc, non_zero_indices]]
                        adc1 = np.array(adc1 & nbcanaux - 1)
                        if num_pass_y != 0:
                            coord_y = coord_y - (num_pass_y * nb_column)

                        new_coord_x = coord_x [non_zero_indices]
                        new_coord_y = coord_y [non_zero_indices]

                        #if (croissant == True and last_x_value==sizeX-1) or (croissant == False and last_x_value == 0):
                        if (croissant == True and last_x_in_array==sizeX-1) or (croissant == False and last_x_in_array == 0):
                            fin_ligne = True
                                                                      
                        # if croissant == True and end_lst_file_found == True: # Si carto stopper avant fin de la ligne
                        #     p2 = last_x_value # Je prend la dernier column en compte dans mon histogramme
                        #     p1 = first_x_value
                        # if croissant == False and end_lst_file_found == True: # Si carto stopper avant fin de la ligne
                        #     p2 = first_x_value # Je prend la dernier column en compte dans mon histogramme
                        #     p1 = last_x_value
                        # elif croissant == False:
                        #     p2 = last_x_value
                        #     p1 = included_x
                        # elif croissant == True:
                        #     p2 = included_x #last_x_value -1
                        #     p1 = first_x_value

                       
                        # if croissant == True:
                        #     adc3 =adc1[0]
                        #     del adc1
                         
                        #     if columns == False:
                        #         range_histo = 1
                        #     else:
                        #         r1 = [p1, p2]
                        #         range_histo = (p2 - p1) + 1


                        # else:
                        #     new_coord_x = np.delete(new_coord_x, 0)
                        #     #new_coord_x = np.flip(new_coord_x)
                        #     new_coord_y = np.delete(new_coord_y, 0)
                        #     #new_coord_y = np.flip(new_coord_y)
                        #     adc2 = np.delete(adc1[0], 0)
                        #     adc3 = np.flip(adc2)
                        #     del adc1

                        #     if columns == False:
                        #         range_histo = 1
                        #     elif p2>p1:
                        #         r1 = [p1, p2]
                        #         range_histo = (p2 - p1) + 1
                        #     else:
                        #         range_histo = 1
                        
                        # if range_histo < 0:
                        #     print('error range_histo') 
                        # if range_histo==1:
                        #    H1, xedges, yedges= np.histogram2d(new_coord_y,adc3,bins=(nb_column,nbcanaux),range= ({0, nb_column-1},{0, nbcanaux-1}))
                        
                        # else:
                        #     H1, edges = np.histogramdd((new_coord_y, new_coord_x, adc3),
                        #                            range=({0, nb_column-1}, r1, {0, nbcanaux-1}),
                        #                            bins=(nb_column, range_histo, nbcanaux))
                       
                        if croissant == True:
                            adc1 =adc1[0]
                        else:
                            adc1 = np.flip(adc1[0])

                        if columns == False:
                            range_histo = 1
                            H1, xedges, yedges= np.histogram2d(new_coord_y,adc1,bins=(nb_column,nbcanaux),range= ({0, nb_column-1},{0, nbcanaux-1}))
                        else:
                            r1 = [first_x_value, last_x_value + 1]
                            range_histo = (last_x_value - first_x_value)  + 1
                            H1, edges = np.histogramdd((new_coord_y, new_coord_x, adc1),
                                                   range=({0, nb_column}, r1, {0, nbcanaux}), 
                                                   bins=(nb_column, range_histo, nbcanaux))

                        if range_histo < 0:
                            print('error range_histo') 

                        indx_1 = first_x_value
                        indx_2 = last_x_value + 1 # Numpy array exclu le dernier indice  

                       
                        # if croissant == True:
                        #     ind_1 = first_x_value
                        #     ind_2 = included_x + 1 # Numpy array exclu le dernier indice
                        # else:
                        #     ind_1 = included_x 
                        #     ind_2 =  last_x_value + 1 # Numpy array exclu le dernier indice


                        if first_x_value == 0:
                            first_x_value=0
                        if num_line_adc <=4: # PIXE HE
                            if range_histo == 1:
                                cube_one_pass_pixe[num_line_adc][:, indx_1, :] = H1
                            else:
                                cube_one_pass_pixe[num_line_adc][0:,indx_1:indx_2, 0:] = H1
                                #print("ok")

                        elif num_line_adc == 5 or num_line_adc == 6 or  num_line_adc == 7: # RBS ou RBS135 ou RBS150    
                            if range_histo == 1:
                                cube_one_pass_rbs[num_line_adc - 5][:, indx_1, :] = H1
                            else:
                                cube_one_pass_rbs[num_line_adc - 5][0:,indx_1:indx_2, 0:] = H1


                        elif num_line_adc == 10: # Gamma20
                            if range_histo == 1:

                                cube_one_pass_gamma20[0][0:, int(next_x_value[num_line_adc]),0:] = H1
                            else:
                               # cube_one_pass_gamma20[0][0:,first_x_value:last_x_value, 0:] = H1
                                cube_one_pass_gamma20[0][0:,indx_1:indx_2, 0:] = H1

                        elif num_line_adc == 11: # Gamma70
                            if range_histo == 1:
                                cube_one_pass_gamma70[0][0:, first_x_value,0:] = H1
                            else:
                               # cube_one_pass_gamma70[0][0:,first_x_value:last_x_value, 0:] = H1
                                cube_one_pass_gamma70[0][0:,indx_1:indx_2, 0:] = H1
                                #print("ok")
                                               
                      
                        # if range_histo != 1 and croissant == True:
                        # if range_histo != 1 and croissant == True:
                        #     next_x_value[num_line_adc] = last_x_value
                        # else:
                        #     next_x_value[num_line_adc] = first_x_value
                        
                    if nb_adc_not_found < 9:
                        if first_x_value ==0 and croissant == True:
                            zero_off = True     
                    

                        if min_last_pos_x_y_in_array < int(shape_data_array):
                            data_array_previous = []
                            data_array_previous = data_array[min_last_pos_x_y_in_array:]
                            adjusted_indices_previous = adjusted_indices
                            b_previous_find_x = True
                            previous_find_x = last_x_in_array
                    else:
                        end_lst_file_found = True

                    if len(data_array_previous) <1:
                        end_lst_file_found = True

                # data_array_previous = np.empty(0, dtype=np.uint16)
                
                if nb_adc_not_found < 9: # RBS, RBS135, RBS150, Gamma20 et Gamma70 peuvent être éteins
                    for num_line_adc in array_adc:
                        if num_line_adc == 1 or num_line_adc == ADC_X or num_line_adc == ADC_Y or num_line_adc == 55: continue
                        adc2read = num_line_adc + 1
                        detector = ret_adc_name(num_line_adc)
                        if num_line_adc <= 4 :
                            data = cube_one_pass_pixe[num_line_adc]
                        elif num_line_adc == 5 or num_line_adc == 6 or num_line_adc == 7:
                            data = cube_one_pass_rbs[num_line_adc-5]
                        elif num_line_adc == 10:
                             data = cube_one_pass_gamma20[0]
                        elif num_line_adc == 11:
                            data = cube_one_pass_gamma70[0]

                        mysum1 = np.sum(data, axis=0)
                        mysum1 = np.sum(mysum1, axis=0)  # Somme des lignes
                        mysum1 = np.sum(mysum1, axis=0)  # Somme des lignes
                        if mysum1 > 0:
                            AGLAEfunction.feed_hdf5_map(data, path_lst, detector, num_pass_y,_dict_adc_metadata_arr[num_line_adc])
                        
                    AGLAEfunction.create_combined_pixe(cube_one_pass_pixe,path_lst,num_pass_y,_dict_adc_metadata_arr)
                    
                    print('\n')


                # if nb_adc_not_found < 9: # RBS, RBS135, RBS150, Gamma20 et Gamma70 peuvent être éteins
                #     for num_line_adc in range(12):
                #         if num_line_adc == 1 or num_line_adc == ADC_X or num_line_adc == ADC_Y or num_line_adc == 55: continue
                #         adc2read = num_line_adc + 1
                #         detector = ret_adc_name(num_line_adc)
                #         if num_line_adc <= 4 :
                #             data = cube_one_pass_pixe[num_line_adc]
                #         elif num_line_adc == 5 or num_line_adc == 6 or num_line_adc == 7:
                #             data = cube_one_pass_rbs[num_line_adc-5]
                #         elif num_line_adc == 10 or num_line_adc == 11:
                #             data = cube_one_pass_gamma[num_line_adc-10]

                #         AGLAEfunction.feed_hdf5_map(data, path_lst, detector, num_pass_y)

                #     AGLAEfunction.create_combined_pixe(cube_one_pass_pixe,path_lst,num_pass_y)
                

                # print("\n")



def getSize(fileobject):
    fileobject.seek(0,2) # move the cursor to the end of the file
    size = fileobject.tell()
    return size
                        
def get_last_x_to_include(croissant,columns,last_x_value,first_x_value,change_line,fin_lst):
    """Recupére Last X à inclure dans ce process"""
    # if columns== False:
    #     included_x = last_x_value
    if columns==True and change_line==False and fin_lst==False:
        if croissant== True:
            included_x = last_x_value -1 #on va eclure le X-1
        elif croissant== False:
            included_x = first_x_value +1
    else:
        if croissant== True:
            included_x = last_x_value
        else:
            included_x = first_x_value
        
    return included_x



def get_x_end_line_scan(croissant,sizex):
    """Get le X max du scan suivant ligne pair/impaire"""
    if croissant==True:
        end_x=sizex-1
    else:
        end_x=0
    return end_x

def look_if_end_lst(max_val_y_lue,sizeY,val_x_fin_map,val_fin_x):
    """informe si on atteins la fin du fichier LST"""
    if max_val_y_lue==sizeY-1 and val_x_fin_map == val_fin_x: #Fin du fichier LST ?
        fin_lst = True
    else: 
        fin_lst = False
    return fin_lst

def look_if_next_line(max_val_y_lue,y_scan_total):
    """informe si le dataset contient la fin du scan """
    
    if max_val_y_lue > y_scan_total: 
        change_line= True
    else:
        change_line =False

    return change_line
    # if last_x_value == 0:
    #             last_x_value = last_x_value
    
    # if croissant==True: # Donne dernière valeur X du Dataset 
    #     val_x_fin_map = last_x_value
    #     val_fin_x = sizeX -1
    # else:
    #     if max_val_y_lue > y_scan_total and first_x_value > last_x_value: # Contient X du prochaine scan
    #         val_x_fin_map = 0
    #         val_fin_x = 0    
    #     else:
    #         val_x_fin_map = first_x_value
    #         val_fin_x = 0
    
    

    # if max_val_y_lue > y_scan_total: # Changement de ligne de scan
    #     if val_x_fin_map == val_fin_x or (first_x_value > last_x_value and croissant==True) or (first_x_value > last_x_value and croissant==True): # Le dataset contient une partie du la ligne de retour -> 
    #         change_line= True
    # else:
    #     change_line= False

                            
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
               5: "RBS",
               6: "RBS135",
               7: "RBS150",
               8: "Coord_X",
               9: "Coord_Y",
               10: "GAMMA20",
               11: "GAMMA70",
               12: "X12",
               13: "X13",
               14: "X14",
               23: "X23",
               134:"X134",
               34: "X34",
                            }
   return switcher.get(num_adc)

def ret_range_bytes(val):
    """Donne n°bits max pour valeur"""
    for bits in range(16):
        if val & (0b0000000000000001 << bits):
            nombre_bytes = bits
    return  2**(nombre_bytes+1) - 1



class ThreadReadLst(QThread):

    valueChanged = pyqtSignal(int)

    def __init__(self,path):
        self.path = path
        self.detector = "LE0"

    # Create a counter thread


    def run(self):

        # pathlst = "C:\\Dev\\PyPIX\\Data\\26jul0068.lst" #26jul0068.lst
        pathlst1 = self.path
        tmpheader = ""
       # MyResultat = list()
        header1 = list()
        sizeX = 1
        sizeY = 1
        print("toto")
        print(pathlst1)
        fin_header = False
        t=0
        with open(pathlst1, "rb") as file_lst:

            while fin_header == False: #tmpheader != b'[LISTDATA]\r\n':
                tmpheader = file_lst.readline()
                t+=1
                # Map size:1280,1280,64,64,0,2564,100000
                if "Map size" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    para = str.split(para[1], sep=",")
                header1.append(tmpheader)
                fin_header = tmpheader == b'[LISTDATA]\r\n' or tmpheader == b'[LISTDATA]\n' or t > 5000
                
            print(header1)
            print(para[0], para[1], para[2], para[3])
            sizeX = int(para[0]) / int(para[2])
            sizeY = int(para[1]) / int(para[3])
            sizeX = int(sizeX)
            sizeY = int(sizeY)
            print(sizeY)
            print(sizeX)
            adcnum = []
            cube = np.zeros((sizeX, sizeY, 2048), 'u4')

            # for i in range (0,50):
            val = b'\xff\xff\xff\xff'
            lstcontent = file_lst.read()
            ind1 = 0
            nrows = 0
            ncolumns = 0

            # MainPage.progress.setRange(1,len(lstcontent) -22000000)

            while ind1 < len(lstcontent) - 22000000:

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
                    self.valueChanged.emit(int(100/len(lstcontent)*ind1))

                val3 = int.from_bytes(val, byteorder='little', signed=False)
                low1 = val3 & 0xFFFF
                hight1 = int(val3 >> 16)

                if 0x4000 == hight1:
                    text = "Valeur tempo"
                    tempo = low1
                if 0xFFFF == low1:
                    text = "Valeur channel"
                    channel = hight1

                if 0x8000 == hight1:
                    text = "TAG ADC"
                    adc = low1
                    adcnum = []
                    channel_num = []
                    for bits in range(8):
                        if adc & (0b00000001 << bits):
                            adcnum.append(bits)
                    if len(adcnum) % 2 == 1:  # & len(adcnum) > 1:
                        # toto = file_lst.read(2) #Nb croissa nte ADC !!
                        val = lstcontent[ind1:ind1 + 2]
                        ind1 += 2

                    for f in adcnum:
                        val_lue = lstcontent[ind1:ind1 + 2]
                        ind1 += 2
                        # val_lue = file_lst.read(2)

                        if f != 4 and f != 5: channel_num.append(int.from_bytes(val_lue, byteorder='little', signed=False))
                        if f == 4: nrows = int.from_bytes(val_lue, byteorder='little', signed=False)  # Valeur X
                        if f == 5: ncolumns = int.from_bytes(val_lue, byteorder='little', signed=False)
                    for c in channel_num:
                        if (c < 2048) & (nrows < 20) & (ncolumns < 20):
                            cube[nrows, ncolumns, c] += 1

            AGLAEfunction.write_hdf5(cube, self.path, self.detector)
