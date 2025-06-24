import sys, os
import numpy as np
from typing import *



def FortranRead(
    filename : str, 
    dType :str = None, 
    DataSize : int = None , 
    HeaderSize : int = 0,
    has_info : bool = False, 
):
    '''
    Read the binary file with Fortran format (markers before/after each data chunk saved). 
    
    Parameters
    ----------
    filename : str
    dType : str
        The data type for Numpy array, e.g. 'float32', 'int32', etc.
    DataSize : int
        The total data size of the file { == (file size - markers size) / element size }. 
        If it is not set, the data chunks are read separately and stacked finally. It takes more time.
    HeaderSize : int
        Size of the file header. 
    has_info : bool
    Returns
    ----------
    DataArray : Fortran data array stacked as dim-1 Numpy array
    '''
    filesize = os.path.getsize(filename) - HeaderSize
    fopen = open( filename, "rb" )
    fopen.read(HeaderSize)

    dTypeSize = np.dtype(dType).itemsize
    if DataSize is None :
        unknow_size = True
        DataArray = [ ]
    else :
        unknow_size = False
        DataArray = np.zeros((DataSize), dtype=dType, )

    Nbytes_incomplete = 0
    Dbytes_incomplete = b""
    AllRead = 0
    while AllRead < filesize:
        marker_int_header = np.fromfile(fopen, count=1, dtype='int32', )
        if not marker_int_header.shape[0] : break
        marker_int_header = abs(marker_int_header[0])
        
        current_hasRead = 0
        if Nbytes_incomplete > 0:
            current_hasRead = dTypeSize - Nbytes_incomplete
            Dbytes_incomplete += fopen.read(current_hasRead)
            if unknow_size:
                DataArray.append( np.frombuffer( Dbytes_incomplete, dtype=dType, ) )
            else:
                DataArray[AllRead:AllRead+1] = np.frombuffer( Dbytes_incomplete, dtype=dType, )
            AllRead += 1
        
        current_counts    = (marker_int_header - current_hasRead) //dTypeSize
        Nbytes_incomplete = (marker_int_header - current_hasRead)  %dTypeSize
        if unknow_size:
            DataArray.append( np.fromfile(fopen, count=current_counts, dtype=dType, ) )
        else:
            DataArray[AllRead:AllRead+current_counts] = np.fromfile(fopen, count=current_counts, dtype=dType, )
        AllRead += current_counts
        
        Dbytes_incomplete = fopen.read(Nbytes_incomplete)
        marker_int_tailer = np.fromfile(fopen, count=1, dtype='int32', )
        if abs(marker_int_tailer[0]) != marker_int_header:
            raise ValueError("The Fortran header-marker does NOT match the tailer-marker! " +
                             "Possible wrong data type or file header information. ")
        
        if has_info:
            print( "%12d, %12d, %12d"%(AllRead, marker_int_header, marker_int_tailer) , 
                " "*10, current_counts* dTypeSize, Nbytes_incomplete, Dbytes_incomplete , flush=True )
    fopen.close()

    if unknow_size:
        return np.hstack( DataArray )
    return DataArray





class FortranReader:
    '''
    same as `FortranRead`, but return the data chunk one by one 
    to avoid memory issues for large data size. 

    usage :: 
    >> freader = FortranReader(...)
    >> while True:
    >>     data_chunk = freader()
    >>     if data_chunk is None : break
    >>     ## TO DO
    '''
    def __init__(self, 
        filename : str, 
        dType :str = None, 
        DataSize : int = None , 
        HeaderSize : int = 0,
        has_info : bool = False, 
        ):
        '''
        see `FortranRead` 
        '''
        self.filename = filename
        self.dType = dType
        self.DataSize = DataSize
        self.HeaderSize = HeaderSize
        self.flag_have_info = has_info
        
        self.filesize = os.path.getsize(filename) - HeaderSize
        self.fopen = open( filename, "rb" )
        self.fopen.read(HeaderSize)
        self.dTypeSize = np.dtype(dType).itemsize
        
        self.DataArray = [ ]
        self.Nbytes_incomplete = 0
        self.Dbytes_incomplete = b""
        self.AllRead = 0
    
    def file_is_closed(self, ):
        return self.fopen.closed
    

    def __update(self, ):
        if self.AllRead < self.filesize:
            marker_int_header = np.fromfile(self.fopen, count=1, dtype='int32', )
            if not marker_int_header.shape[0] : 
                self.DataArray = None
                self.fopen.close()
                return None
            marker_int_header = abs(marker_int_header[0])

            current_hasRead = 0
            if self.Nbytes_incomplete > 0:
                current_hasRead = self.dTypeSize - self.Nbytes_incomplete
                self.Dbytes_incomplete += self.fopen.read(current_hasRead)
                temp_data = np.frombuffer( self.Dbytes_incomplete, dtype=self.dType, )
                self.DataArray.append(temp_data.copy())
                self.AllRead += 1

            current_counts    = (marker_int_header - current_hasRead) //self.dTypeSize
            Nbytes_incomplete = (marker_int_header - current_hasRead)  %self.dTypeSize
            self.DataArray.append( np.fromfile(self.fopen, count=current_counts, dtype=self.dType, ) )
            self.AllRead += current_counts
            
            self.Nbytes_incomplete = Nbytes_incomplete
            self.Dbytes_incomplete = self.fopen.read(Nbytes_incomplete)
            marker_int_tailer = np.fromfile(self.fopen, count=1, dtype='int32', )
            if abs(marker_int_tailer[0]) != marker_int_header:
                raise ValueError("The Fortran header-marker does NOT match the tailer-marker! " +
                                 "Possible wrong data type or file header information. ")
            if self.flag_have_info :
                print( "%12d, %12d, %12d"%(self.AllRead, self.marker_int_header, self.marker_int_tailer) , 
                    " "*10, current_counts* self.dTypeSize, self.Nbytes_incomplete, self.Dbytes_incomplete , flush=True )
            
        else:
            self.DataArray = None
            self.fopen.close()
    
    def __call__(self, ):
        while self.DataArray is not None \
        and len(self.DataArray)==0:
            self.__update()
        if self.DataArray is None:
            return None
        else:
            output = self.DataArray[0]
            self.DataArray = self.DataArray[1:]
            return output




