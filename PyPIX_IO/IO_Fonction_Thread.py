import h5py, re
import numpy as np
import sys, os
from PyQt5.QtCore import  QThread, pyqtSignal
#import EdfFile, EDFStack , ArraySave, EdfFileDataSource,DataObject,PhysicalMemory
import threading
from datetime import datetime
from time import perf_counter
import matplotlib.pyplot as plt


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

            AGLAEFile.write_hdf5(cube, self.path, self.detector)


class AGLAEFile(object):
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

    @staticmethod
    def feed_hdf5_map(mydata, Pathlst, detector, FinalHDF, num_det,sizeX,sizeY,nbcanaux,num_scan_y):
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
        #h5file = h5py.File(newdestfile, 'a')

        with h5py.File(newdestfile, 'a') as h5file:
            group_name = 'data' + str(num_det) + "_" + detector  # "data"

            if num_scan_y != 0:
                    nxData = h5file[f'{group_name}/maps']
                    print(np.shape(nxData))
                   # nxData.resize((nxData.shape[0] + mydata.shape[0]), axis=0)
                    nxData.resize((nxData.shape[0] + mydata.shape[0],nxData.shape[1] ,nxData.shape[2]))
                   # nxData.resize((nxData.shape[2] + mydata.shape[2]), axis=2)
                    nxData[-mydata.shape[0]:,0:, :] = mydata
                    print(np.shape(nxData))

            else:
                    try:
                        del h5file[f'{group_name}']
                    except Exception:
                        pass
                    nxData = h5file.require_group(f'{group_name}')
                    dset = nxData.require_dataset('maps', data = mydata, shape =mydata.shape, dtype=np.uint32, maxshape=(None,None,None), chunks=True, compression="gzip",compression_opts=4)
                   #dset[:,:,:] = mydata
                    #dset = group[f'maps']
                    #nxData = h5file.require_group(group)


            # shape = mydata.shape
            # dtype = mydata.dtype

            ###dset = f.create_dataset(detector, data=mydata, dtype='u4', compression="gzip", compression_opts=4)



            # grp = f.create_group("stack/" + detector)
            ##dset = NxData.create_dataset("data",shape=shape, data=mydata, dtype=dtype) #'u8') #, compression="gzip", compression_opts=4)

            #dset = nxData.require_dataset('maps', data=mydata, shape=shape, dtype=dtype, compression="gzip",compression_opts=4)
            #nxData.attrs["signal"] = detector
            #nxData.flush()
            print("HDF5 write" + detector)
        h5file.close()
    #bil Band interleaved by line[ncolumns, nbands, nrows]
    #bip Band interleaved by pixel[nbands, ncolumns, nrows]
    #bsq Band sequential [ncolumns, nrows, nbands]

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

        AGLAEFile.write_hdf5(stack.data, edfpath, detname, FinalHDF,num_det)

    def write_hdf5_metadata(Pathfile,parametre,detname,FinalHDF):
        # f = h5py.File('./Data/ReadLst_GZIP.hdf5', 'w')
        head_tail = os.path.split(Pathfile)# Split le Path et le fichier
        destfile = head_tail[1].split(".")
        newdestfile = destfile[0] + ".hdf5"
        index_iba= destfile[0].find("_IBA_")
        index_l1 = destfile[0].find("_L1_")
        index_xrf = destfile[0].find("_XRF1_:")
        det_aglae = ["LE0", "HE1", "HE2", "HE3", "HE4", "HE10", "HE11","HE12","HE13","RBS","RBS150","RBS135","GAMMA","GAMMA70","GAMMA20","IBIL","FORS"]
        iba_para = False

        for det1 in det_aglae:
            if detname == det1:
                iba_para = True


     #   if index_l1 > 0:
      #  elif index_xrf > 0:




        if destfile[1] == 'lst':
            newdestfile = destfile[0] + ".hdf5"
        #elif destfile[1] == 'edf':
            #newdestfile = FinalHDF
            #n = len(destfile[0])
            # name = os.path.basename(destfile[0])
            # if index_iba > 0:
            #     Myname = name.split('_IBA')
            #     FinalHDF = Myname[0] + ".hdf5"
            # else:
            #     Myname = name.split('_')
            #     FinalHDF = Myname[0] + "_" +  Myname[1] + ".hdf5"

            #newdestfile = os.path.join(os.path.dirname(Pathfile), FinalHDF)

        newdestfile1 =  os.path.join(head_tail[0] , FinalHDF)

        print(newdestfile)
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
            grp.attrs["Detector filter"] = "LE0:{}, HE1:{}, HE2:{}, HE3:{}, HE4:{}".format(parametre[10], parametre[11],
                                                                                       parametre[12], parametre[13],
                                                                                       parametre[14])
            print("HDF5 MetaData write")
        else:
          #  grp1 = f.create_group("stack/detector")
            #grp1.attrs["Data"] = "Test"
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


    def open_header_lst(pathlst):
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

        with open(pathlst, "rb") as file_lst:
            import os
            size_lst = os.path.getsize(pathlst)

            while tmpheader != b'[LISTDATA]\r\n':
                tmpheader = file_lst.readline()
                # Map size:1280,1280,64,64,0,2564,100000_
                if "Map size" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    para = str.split(para[1], sep=",")
                    for newwpara in para:
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

                # header1.append(tmpheader)
        if len(para2) == 0:
            for i in range(7):
                header1.append("?")

        return header1

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

    def return_index_adc_in_data_array(adjusted_indices,adc_values,num_line_adc):
        """
        Retourne l'indice
        """
        # Op�rations bitwise et filtrage des indices
        adc_masked = np.bitwise_and(adc_values[:], 0b0000000000000001 << num_line_adc)
        coord_X_masket = np.bitwise_and(adc_values[:], 0b0000000000000001 << 8)
        coord_Y_masket = np.bitwise_and(adc_values[:], 0b0000000000000001 << 9)
        condition = (adc_masked != 0) # and coord_X_masket[:] != 0 and coord_Y_masket[:] != 0
        conditionX = coord_X_masket[:] != 0
        conditionY = coord_Y_masket[:] != 0
        condition2 = np.logical_and(condition, conditionX)
        condition_final = np.logical_and(condition2, conditionY)
     #   filtered_indices = np.where(adc_masked[:] != 0 and coord_X_masket[:] != 0 and coord_Y_masket[:] != 0, adjusted_indices[:],
       #                             np.full(len(adc_masked), -1, dtype=np.int16))
        filtered_indices = np.where(condition_final, adjusted_indices[:],
                                     np.full(len(condition_final), -1, dtype=np.int16))
        # filtered_indices = np.where(coord_Y_masket[:] != 0, adjusted_indices[:],
        #                             np.full(len(coord_Y_masket), -1, dtype=np.int16))

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
        # recherche la dernire valeur de Y
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

    def read_max_x(coord_x,croissant):

        last_pos_x = np.empty(0, dtype=np.uint16)
        first_pos_x = np.empty(0, dtype=np.uint16)
        if len(coord_x) > 100:
            r1 = 100
        else:
            r1 = len(coord_x) -1

        for pos in range(r1):
            if croissant == True:
                last_pos_x = np.append(last_pos_x, coord_x[-pos-1])  # A partir de la fin
                first_pos_x = np.append(first_pos_x, coord_x[pos])  # A partir du d�but
            else:
                last_pos_x = np.append(last_pos_x, coord_x[pos])  # A partir du d�but
                first_pos_x = np.append(first_pos_x, coord_x[-pos-1])  # A partir de la fin

        last_pos_x = np.delete(last_pos_x, 0)
        count_x = np.bincount(last_pos_x)
        last_x_value = int(np.shape(count_x)[0]) - 1 # On enleve la derni�re colonne

        
        count_x_min = np.bincount(first_pos_x)
        first_x = np.where(count_x_min == max(count_x_min))
        first_x_value = int(first_x[0])
        
        # if croissant == True:
        #     last_x_value = last_x - 1  # int(last_x[0]) - 1
        # else:
        #     if last_x != 0:
        #         last_x_value = first_x_value  # int(last_x[0]) + 1
        #     else:
        #         last_x_value = 0  # fin de la ligne de retour

        return first_x_value, last_x_value


            # indice_x_max = np.where(coord_x == last_x_value)

            # if int(previous_last_x) != 0:
            #     if croissant == True:
            #         indice_x_prev = np.where(coord_x == previous_last_x + 1)  # recherche la colonne N+1 suivant dans ligne croissants
            #         indice_x_prev1 = indice_x_prev[0][0]

            #     else:
            #         indice_x_prev = np.where(coord_x == previous_last_x)  # recherche la colonne suivant dans ligne d�croissantes
            #         ind_fin = 0
            #         indice_x_prev1 = indice_x_prev[0][-1]
            #         ind1 = np.array(indice_x_prev[0])
            #         find = False
            #         while find == False:
            #             ind_fin_0 = -1 - ind_fin
            #             #ind_fin_1 = -1 - (ind_fin+1)
            #             if coord_x[ind1[ind_fin_0]] == previous_last_x and coord_x[ind1[ind_fin_0]-1] == previous_last_x: # Ignore valeur X isol�
            #                 indice_x_prev1 = indice_x_prev[0][-1-ind_fin]
            #                 find = True
            #             else:
            #                 ind_fin += 1


            # else:
            #     indice_x_prev1 = 0

            # if len(indice_x_max) == 0:
            #     return 0,0,0
            # indice_x_last = indice_x_max[0][-1]

        #    return indice_x_prev1, indice_x_last, last_x_value ,first_x_value
        # except:
        #     indice_x_prev1 = 0
        #     indice_x_last = len(coord_x)-1
        #     last_x_value = previous_last_x
        #     first_x_value = 0

        # return indice_x_prev1, indice_x_last, last_x_value, first_x_value

    def read_indice_max_x(sizeX,coord_x,croissant,find_x):
            indice_x_max = np.where(coord_x == find_x)
            # if int(previous_x) == 0 and croissant == True:
            #     previous_x = previous_x +1
            # elif int(previous_x) !=sizeX-1 and croissant == False:
            #     previous_x = previous_x - 1

            # if croissant == True:

            # indice_x_prev = np.where(coord_x == previous_x)  # recherche la colonne N+1 suivant dans ligne croissants
            # try:
            #     if croissant == True or int(previous_x) == sizeX-1:
            #         indice_x_prev1 = indice_x_prev[0][0]
            #     else:
            #         indice_x_prev1 = indice_x_prev[0][0]
            # except:
            #     if croissant == True:
            #         indice_x_prev1 = indice_x_prev[0]
            #     else:
            #         indice_x_prev1 = indice_x_prev[-1]

            if croissant == True:
                indice_x_last = indice_x_max[0][-1]
            else:
                indice_x_last = indice_x_max[0][0]

            # else:
            #     if croissant==True:
            #         indice_x_prev = np.where(coord_x == find_x)  # recherche la colonne N+1 suivant dans ligne croissants
            #     else:
            #         indice_x_prev = np.where(coord_x == previous_x)  # recherche la colonne N-1 suivant dans ligne décroissants
                    
            #     indice_x_prev1 = indice_x_prev[0][0]
            #     indice_x_max = np.where(coord_x == find_x)
            #     indice_x_last = indice_x_max[0][0]
                    # indice_x_prev = np.where(coord_x == previous_last_x)  # recherche la colonne suivant dans ligne d�croissantes
                    # ind_fin = 0
                    # indice_x_prev1 = indice_x_prev[0][-1]
                    # ind1 = np.array(indice_x_prev[0])
                    # find = False
                    # while find == False:
                    #     ind_fin_0 = -1 - ind_fin
                    #     #ind_fin_1 = -1 - (ind_fin+1)
                    #     if coord_x[ind1[ind_fin_0]] == previous_last_x and coord_x[ind1[ind_fin_0]-1] == previous_last_x: # Ignore valeur X isol�
                    #         indice_x_prev1 = indice_x_prev[0][-1-ind_fin]
                    #         find = True
                    #     else:
                    #         ind_fin += 1


            # else:
            #     indice_x_prev1 = 0
            #     indice_x_last = indice_x_max[0][-1]

            # if len(indice_x_max) == 0:
            #     return 0,0,0
           
            return indice_x_last

        #    return indice_x_prev1, indice_x_last, last_x_value ,first_x_value
        # except:
        #     indice_x_prev1 = 0
        #     indice_x_last = len(coord_x)-1
        #     last_x_value = previous_last_x
        #     first_x_value = 0

    
    
    def read_min_x(coord_x, croissant, previous_last_x):

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
        fin_ligne = False
        indice_y_last = np.where(coord_y > y_scan_total)  # recherche les val de la dernier colonne
        if len(indice_y_last[0]) < 50:
            fin_ligne = True
            indice_last = 0
        indice_last = indice_y_last[0][0] - 1
        return indice_last

# Fonction d'extraction du fichier LST avec vectorisation
    def extract_lst_vector(path, detector, path_lst, para):
        pathlst1 = path
        tmpheader = ""
        header1 = list()
        sizeX = 1
        sizeY = 1
        print("toto100")
        print(pathlst1)
        print(para[0], para[1], para[2], para[3])
        sizeX = int(para[3]) / int(para[5])
        sizeY = int(para[4]) / int(para[6])
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

        nbcanaux = switcher.get(detector)
        # cube = np.zeros((sizeX, sizeY, nbcanaux), 'u4')
        ## for i in range (0,50):
        file = open(pathlst1, 'rb')
        size_lst = getSize(file)
        file.close()
        allheader = ""
        with open(pathlst1, "rb") as file_lst:  # Trop long
            while tmpheader != b'[LISTDATA]\r\n':
                tmpheader = file_lst.readline()
                tmp1 = str(tmpheader)
                allheader = allheader + tmp1.replace("\\r\\n", '')

                size_lst -= len(tmp1) - 2
                if "condition" in str(tmpheader):
                    toto = 1
                # Map size:1280,1280,64,64,500,2564,100000
                if "Map size" in str(tmpheader):
                    para = str.split(str(tmpheader), sep=':')
                    para = str.split(para[1], sep=",")
                # header1.append(tmpheader)

            print(para[0], para[1], para[2], para[3])
            sizeX = int(para[0]) / int(para[2])
            sizeY = int(para[1]) / int(para[3])
            sizeX = int(sizeX)
            sizeY = int(sizeY)
            pensize = int(para[4])
            nb_pass_y = int(sizeY / (pensize / int(para[3])))
            #           cube_final= np.zeros((sizeY,sizeX,nbcanaux-1),dtype=np.uint16)
            # for i in range (0,50):

            val = b'\xff\xff\xff\xff'
            # Pas possible gros LST
            # lstcontent = self.lstcontent #  file_lst.read()
            range_very_small = 10 ** 5
            range_small = 10 ** 6  # range(1, 10**6) #50 Mo
            range_100mega = 10 ** 7  # range(10**6+1, 10**7) #100 Mo
            range_giga = 10 ** 8  # range(10**7 + 1, 1**12)  # 100 Mo
            size_lst = int(size_lst / 2)  # car on lit des Uint16 donc 2 fois moins que le nombre de bytes (Uint8)
            size_block = size_lst

            if size_lst < range_very_small: size_block = 10 ** 4
            if size_lst < range_small: size_block = size_lst
            if size_lst > range_100mega: size_block = 1000000  # 2*10**5 #10Mo
            if size_lst > range_giga: size_block = 2 * 10 ** 7  # 50Mo
            # size_block = 100000
            nb_read_total = 0
            if size_lst > size_block:
                nb_loop = int(size_lst / size_block)
                nb_loop += 1
                reste = size_lst % size_block
            else:
                nb_loop = 1
                reste = 0
                nb_pass_y = 1
            nb_byte_to_read = size_block
            indice_in_datablock = 0
            nb_read_total = 0
            max_val_y_lue = 0
            croissant = True
            y_scan = int(sizeY / nb_pass_y) - 1
            nb_column = int(sizeY / nb_pass_y)
            data_array_previous = np.empty(0, dtype=np.uint16)
            end_extract = False
            last_x_maps = 0

            if nb_pass_y % 2 == 0:
                last_x_maps = 0
            else:
                last_x_maps = sizeX - 1

            for num_pass_y in range(nb_pass_y):

                if (num_pass_y % 2 == 0):
                    croissant = True
                    next_x_value = np.zeros(12, dtype=np.uint16)

                else:
                    croissant = False
                    next_x_value = np.full(12, sizeX - 1, dtype=np.uint16)


                end_extract = False
                y_scan_total = y_scan + (num_pass_y * nb_column)

                cube_one_pass_pixe = np.empty((5, nb_column, sizeX, nbcanaux), dtype=np.uint32)
                cube_one_pass_gamma = np.empty((2, nb_column, sizeX, nbcanaux), dtype=np.uint32)
                cube_one_pass_rbs = np.empty((3, nb_column, sizeX, 512), dtype=np.uint32)

                fin_ligne = False

                while (fin_ligne == False):  # max_val_y_lue <= y_scan): # or croissa nte == False ):

                    adc2read = 0
                    adc_values = np.empty(0, dtype=np.uint16)
                    data_array = np.empty(0, dtype=np.uint16)
                    adjusted_indices = np.empty(0, dtype=np.uint16)
                    adjusted_indices_previous = np.empty(0, dtype=np.uint16)

                    min_last_pos_x_y_in_array = 0 #nb_byte_to_read
                    data_array = np.fromfile(file_lst, dtype=np.uint16, count=int(nb_byte_to_read))
                    if len(data_array) < nb_byte_to_read:
                        end_extract = True

                    adjusted_indices,data_array ,shape_data_array = AGLAEFile.return_adc_adjusted_index (data_array_previous, data_array)
                    adc_values = np.array(data_array[adjusted_indices])


                    nb_read_total += (nb_byte_to_read * 2) + len(data_array_previous)
                    t1 = perf_counter()

                    array_adc = [0,1,2,3,4,6,7,10,11]
                    #array_adc = [0,4]
                    for num_line_adc in array_adc: #range(12):
                        if num_line_adc == 1 or num_line_adc == 8 or num_line_adc == 9 or num_line_adc == 5: continue

                        switcher = {5: 2048, 0: 2048, 1: 2048, 2: 2048, 3: 2048, 4: 2048, 80: 2048, 81: 2048,
                                    82: 2048, 6: 512, 7: 512, 10: 2048, 11: 2048}
                        nbcanaux = switcher.get(num_line_adc)

                        detector = ret_adc_name(num_line_adc)
                        adc2read = num_line_adc + 1
                        # adc2read = ret_num_adc(self.detector)
                        t0 = perf_counter()
                        non_zero_indices = AGLAEFile.return_index_adc_in_data_array(adjusted_indices,adc_values,num_line_adc)
                        if non_zero_indices[0] == -1:
                            continue
                        adc_words = data_array[non_zero_indices]
                        indice_val_to_read = AGLAEFile.return_val_to_read(adc_words,non_zero_indices)

                        max_size_x = ret_range_bytes(sizeX - 1)
                        max_size_y = ret_range_bytes(sizeY - 1)
                        coord_x = data_array[indice_val_to_read[8, :]]  # non_zero_indices]]
                        coord_x = coord_x & max_size_x  # 2047 #
                        coord_y = data_array[indice_val_to_read[9, :]]  # non_zero_indices]]
                        c1 = indice_val_to_read[9, :]
                        c1 = c1[c1 != 0]
                        # count_nby = len(coord_y[coord_y!=0])
                        if len(c1) < 100:
                            continue
                        coord_y = coord_y & max_size_y  # 2047 #sizeY - 1

                        # sup_max_sizex = np.where(coord_x > sizeX - 1)
                        # Met des -1 aux coord X et Y sup�rieur � la valeur de la carto
                        out_range_x = np.where(coord_x > sizeX - 1)
                        coord_x = np.delete(coord_x, out_range_x)
                        coord_y = np.delete(coord_y, out_range_x)
                        coord_x = np.where(coord_x <= sizeX - 1, coord_x, np.full(len(coord_x), 0))
                        coord_y = np.where(coord_y <= sizeY - 1, coord_y, np.full(len(coord_y), 0))
                    
                        max_val_y_lue,min_val_y_lue = AGLAEFile.read_min_max_y(coord_y)

                        print("Y:", max_val_y_lue)
                        if max_val_y_lue==29:
                            max_val_y_lue = max_val_y_lue
                        #last_x_value = AGLAEFile.read_min_x(coord_x,croissant,1)
                        first_x_value, last_x_value = AGLAEFile.read_max_x(coord_x, croissant)

                        # if croissant==False: #inverse last et first X value
                        #     a1 = last_x_value
                        #     last_x_value = first_x_value
                        #     first_x_value = a1
                        if croissant==True:
                            val_x_fin_map = last_x_value
                        else:
                            val_x_fin_map = first_x_value
                        
                        if max_val_y_lue==sizeY-1 and val_x_fin_map == last_x_maps:
                            fin_lst = True
                        else: 
                            fin_lst = False

                        if max_val_y_lue > y_scan_total:
                            if val_x_fin_map == last_x_maps or first_x_value > last_x_value :
                                change_line= True
                        else:
                            change_line= False

                        if change_line==True or fin_lst== True: #(max_val_y_lue==sizeY-1 and val_x_fin_map == last_x_maps ):  # Contient le scan suivant
                            #indice_x_prev1, indice_last, last_x_value,first_x_value = AGLAEFile.read_max_x(coord_x, croissant, next_x_value[num_line_adc])
                         #   first_x_value, last_x_value = AGLAEFile.read_max_x(coord_x, croissant)
                            if last_x_value < first_x_value and croissant==True:
                                last_x_value = sizeX-1
                            
                            if fin_lst==False:
                                indice_last = AGLAEFile.read_indice_max_x(sizeX,coord_x,croissant,last_x_value)#,next_x_value[num_line_adc])
                                indice_last = AGLAEFile.read_max_indice_change_colonne(coord_y,y_scan_total) #REcherche last_indice avec Y < scan total
                            else:
                                indice_last = len(coord_y) -1

                            fin_ligne = True
                            coord_x = coord_x[:indice_last]
                            coord_y = coord_y[:indice_last]
                            max_data_array = indice_val_to_read[8, indice_last]

                            if max_data_array > min_last_pos_x_y_in_array:
                                  min_last_pos_x_y_in_array = max_data_array

                        else:  # recherche la dernire valeur de X

                            if end_extract == False:
                                ########################## RECUPERE INDICE VAL PREVIOUS et ACTUAL
                                #indice_x_prev1, indice_last, last_x_value,first_x_value = AGLAEFile.read_max_x(coord_x, croissant, next_x_value[num_line_adc])
                                # first_x_value, last_x_value = AGLAEFile.read_max_x(coord_x, croissant)
                                # indice_x_prev1, indice_last = AGLAEFile.read_indice_max_x(coord_x,first_x_value,last_x_value)
                            
                            #    first_x_value, last_x_value = AGLAEFile.read_max_x(coord_x, croissant)
                                #indice_x_prev1, indice_last = AGLAEFile.read_indice_max_x(coord_x,croissant,last_x_value-1,next_x_value[num_line_adc])
                                if croissant== True:
                                    columns = last_x_value -1 > first_x_value
                                    find_x = last_x_value
                                    if columns==True: find_x -=1 # recherche X -1
                                else:
                                    columns = first_x_value +1 < last_x_value
                                    find_x = first_x_value
                                    
                                    if columns==True: 
                                    #     find_x +=1 # recherche X +1
                                         first_x_value +=1

                                if columns == True: # plus de 1 colonne
                                    indice_last = AGLAEFile.read_indice_max_x(sizeX,coord_x,croissant,find_x)#,next_x_value[num_line_adc])
                                else:
                                    indice_last = AGLAEFile.read_indice_max_x(sizeX,coord_x,croissant,first_x_value)#,next_x_value[num_line_adc])
                            
                                
                                print("X:", last_x_value-1)
                                if last_x_value == 37:
                                    last_x_value = last_x_value
                                max_data_array = indice_val_to_read[8, indice_last]
                                coord_x = coord_x[:indice_last]
                                coord_y = coord_y[:indice_last]

                                #if max_data_array < nb_byte_to_read and max_data_array > min_last_pos_x_y_in_array:
                                if max_data_array > min_last_pos_x_y_in_array:
                                     min_last_pos_x_y_in_array = max_data_array

                            else: # Fin du fichier on mets les bornes max pour X
                                if croissant == True:
                                    # indice_x_prev1, indice_last, last_x_value,first_x_value = AGLAEFile.read_max_x(coord_x, croissant, next_x_value[num_line_adc])
                                    #last_x_value = sizeX - 1
                                    #first_x_value = last_x_value
                                    first_x_value, last_x_value = AGLAEFile.read_max_x(coord_x, croissant)
                                else:
                                    last_x_value = 0


                                indice_x_last = len(coord_x)


                        non_zero_indices = np.nonzero(indice_val_to_read[num_line_adc, :indice_last])
                        if len(non_zero_indices[0]) < 2:  # pas de valeur pour cet adc dans ce Block de Data Array
                            continue

                        adc1 = data_array[indice_val_to_read[num_line_adc, non_zero_indices]]
                        adc1 = np.array(adc1 & nbcanaux - 1)
                        if num_pass_y != 0:
                            coord_y = coord_y - (num_pass_y * nb_column)

                        new_coord_x = coord_x [non_zero_indices]
                        new_coord_y = coord_y [non_zero_indices]

                        # if croissant == True: # Valeurs X croissantes

                        #     if last_x_value - 1 == first_x_value:
                        #         range_histo = 1
                        #     else:
                        #         #range_histo = int(last_x_value - next_x_value[num_line_adc])
                        #         range_histo = int(last_x_value - first_x_value)

                        #      # if int(next_x_value[num_line_adc]) == 0:  # Pour la ligne 0
                        #      #     range_histo += 1
                        #     # if int(next_x_value[num_line_adc]) != 0 and int(next_x_value[num_line_adc]) !=sizeX-1:
                        #     #     next_x_value[num_line_adc] += 1  # ajoute +1 a la valeur precedente

                        # else:# Valeur X decroissantes
                        #     #range_histo = int(next_x_value[num_line_adc] - last_x_value)
                        #     if last_x_value - 1 == first_x_value:
                        #         range_histo = 1
                        #     else:
                        #         range_histo = int(last_x_value - first_x_value)
                            
                        #     if int(next_x_value[num_line_adc]) == 0 and last_x_value ==0: # Colonne 0
                        #         range_histo =1



                        if croissant == True and last_x_value==sizeX-1:
                            fin_ligne = True
                        elif croissant == False and last_x_value == 0:
                            fin_ligne = True
                      
                        # if range_histo == 1:
                        #     range_histo = 1
                        # 
                        p1 = first_x_value
                        
                        if last_x_value == sizeX-1:
                            p2 = last_x_value # Je prend la dernier column en compte dans mon histogramme
                        elif croissant == False:
                            p2 = last_x_value
                        else:
                            p2 = last_x_value -1

                        if croissant == True:
                            adc3 =adc1[0]
                            del adc1
                         
                            if first_x_value == last_x_value - 1 and fin_ligne == False: # Une seule column dans le dataArray
                                range_histo = 1
                            else:
                                r1 = [p1, p2]
                                range_histo = (p2 - p1) + 1

                        else:
                            new_coord_x = np.delete(new_coord_x, 0)
                            new_coord_x = np.flip(new_coord_x)
                            new_coord_y = np.delete(new_coord_y, 0)
                            new_coord_y = np.flip(new_coord_y)
                            adc2 = np.delete(adc1[0], 0)
                            adc3 = np.flip(adc2)
                            del adc1

                            if p1 == p2:
                                range_histo = 1
                            else:
                                r1 = [p1, p2]
                                range_histo = (p2 - p1) + 1
                                #range_histo = int(last_x_value - first_x_value)

                        if last_x_value == 10 and max_val_y_lue ==39:
                            last_x_value = last_x_value
                        if range_histo==1:
                           H1, xedges, yedges= np.histogram2d(new_coord_y,adc3,bins=(nb_column,nbcanaux),range= ({0, nb_column-1},{0, nbcanaux-1}))
                           # H1, xedges = np.histogram(adc3, bins=nb_column)
                        else:
                            H1, edges = np.histogramdd((new_coord_y, new_coord_x, adc3),
                                                   range=({0, nb_column-1}, r1, {0, nbcanaux-1}),
                                                   bins=(nb_column, range_histo, nbcanaux))
                        # fig, ax = plt.subplots()
                        print(np.shape(H1))
                        
                        # cube_one_pass= np.add((cube_one_pass,H1),axis=2)
                        if croissant == True:
                            if last_x_value == sizeX-1:
                                last_x_value = last_x_value +1 # Incrément de 1 pour la derniere column car H1 a une dimension +1
                        else:
                            #if last_x_value == 0 or last_x_value == sizeX-1:
                            last_x_value = last_x_value +1


                        if num_line_adc <=4:
                            if range_histo == 1:
                                cube_one_pass_pixe[num_line_adc ,:, first_x_value, :] = H1
                            else:
                                cube_one_pass_pixe[num_line_adc][0:,first_x_value:last_x_value, 0:] = H1

                        elif num_line_adc == 6 or  num_line_adc == 7:
                            if range_histo == 1:
                                cube_one_pass_rbs[num_line_adc - 6][0:, int(next_x_value[num_line_adc]),0:] = H1
                            else:
                                cube_one_pass_rbs[num_line_adc - 6][0:,first_x_value:last_x_value, 0:] = H1

                        elif num_line_adc == 10 or num_line_adc == 11:
                            if range_histo == 1:
                                cube_one_pass_gamma[num_line_adc - 10][0:, int(next_x_value[num_line_adc]),0:] = H1
                            else:
                                cube_one_pass_gamma[num_line_adc - 10][0:,first_x_value:last_x_value, 0:] = H1

                        if range_histo == 1:
                            if croissant == True:
                                next_x_value[num_line_adc] = first_x_value #+1  # -next_x_value[num_line_adc]
                            else:
                                next_x_value[num_line_adc] = first_x_value     
                        else:
                            if croissant == True:
                                next_x_value[num_line_adc] = last_x_value
                            else:
                                next_x_value[num_line_adc] = first_x_value

                        # else:
                        #    # plt.plot(H1[0, 0, :])
                        #    # plt.show()
                        #    if last_x_value != 0:
                        #        last_x_value = last_x_value -1
                        #    else:
                        #        last_x_value = last_x_value
                        #        next_x_value[num_line_adc] = next_x_value[num_line_adc] +1

                        #    if num_line_adc <= 4:
                        #         cube_one_pass_pixe[num_line_adc][0:, last_x_value:int(next_x_value[num_line_adc]),
                        #         0:] = H1
                        #    elif num_line_adc == 6 or num_line_adc == 7:
                        #        cube_one_pass_rbs[num_line_adc-6][0:, last_x_value:int(next_x_value[num_line_adc]),
                        #        0:] = H1
                        #    elif num_line_adc == 10 or num_line_adc == 11:
                        #        cube_one_pass_gamma[num_line_adc - 10][0:,last_x_value:int(next_x_value[num_line_adc]),
                        #        0:] = H1
                        #    next_x_value[num_line_adc] = first_x_value



                    if min_last_pos_x_y_in_array < int(shape_data_array):
                        data_array_previous = []
                        data_array_previous = data_array[min_last_pos_x_y_in_array+5:]
                        adjusted_indices_previous = adjusted_indices

                # data_array_previous = np.empty(0, dtype=np.uint16)
                for num_line_adc in range(12):
                    if num_line_adc == 1 or num_line_adc == 8 or num_line_adc == 9 or num_line_adc == 5: continue
                    adc2read = num_line_adc + 1
                    detector = ret_adc_name(num_line_adc)
                    if num_line_adc <= 4 :
                        data = cube_one_pass_pixe[num_line_adc]
                    elif num_line_adc == 6 or num_line_adc == 7:
                        data = cube_one_pass_rbs[num_line_adc-6]
                    elif num_line_adc == 10 or num_line_adc == 11:
                        data = cube_one_pass_gamma[num_line_adc-10]

                    AGLAEFile.feed_hdf5_map(data, path, detector, "FinalHDF", adc2read, sizeX, sizeY,nbcanaux,num_pass_y)


def getSize(fileobject):
    fileobject.seek(0,2) # move the cursor to the end of the file
    size = fileobject.tell()
    return size

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

def ret_range_bytes(val):
    for bits in range(16):
        if val & (0b0000000000000001 << bits):
            nombre_bytes = bits
    return  2**(nombre_bytes+1) - 1

class HDF5Store(object):
    """
    Simple class to append value to a hdf5 file on disc (usefull for building keras datasets)

    Params:
        datapath: filepath of h5 file
        dataset: dataset name within the file
        shape: dataset shape (not counting main/batch axis)
        dtype: numpy dtype

    Usage:
        hdf5_store = HDF5Store('/tmp/hdf5_store.h5','X', shape=(20,20,3))
        x = np.random.random(hdf5_store.shape)
        hdf5_store.append(x)
        hdf5_store.append(x)

    From https://gist.github.com/wassname/a0a75f133831eed1113d052c67cf8633
    """

    def __init__(self, datapath, dataset, shape, dtype=np.float32, compression="gzip", chunk_len=1):
        self.datapath = datapath
        self.dataset = dataset
        self.shape = shape
        self.i = 0

        with h5py.File(self.datapath, mode='w') as h5f:
            self.dset = h5f.create_dataset(
                dataset,
                shape=(0,) + shape,
                maxshape=(None,) + shape,
                dtype=dtype,
                compression=compression,
                chunks=(chunk_len,) + shape)

    def append(self, values):
        with h5py.File(self.datapath, mode='a') as h5f:
            dset = h5f[self.dataset]
            dset.resize((self.i + 1,) + shape)
            dset[self.i] = [values]
            self.i += 1
            h5f.flush()



