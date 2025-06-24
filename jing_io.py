import sys, os
import numpy as np
from typing import *
from FortranReader import *



def read_Pos( 
    files, 
    is_header :bool = None , 
    if_stack = False ,
    Nparticles = None,  
    is_IC = False, 
    has_info = False, 
    ):
    '''
    Read the simluation snapshot Position/Velocity with format `jing`.

    Parameters
    ----------
    files : string or list. 
            string if there is single file for a snapshot.
            list   if there are multi-file for a snapshot, and the first file should be the file with header.
    is_header : bool
        If read only a single file, one should specify whether it is a header file.
    if_stack : bool.
            When requiring read multi-files :
            `True`  if stack the multi-file in a ndarray with shape (Np, 3)
            `False` if return the type `list(np.ndarray)`
    Nparticles : Number of simulation particles.
    is_IC : bool.
            True if it is a initial condition file, like 
            >> /home/cossim/CosmicGrowth/6620/IC/pos6620.0025.01
            They should be treated differently because there are more bytes in the header (though I don't know what's that ... )

    Returns
    snapshot : Position data normalized to range(0, 1) , with type `np.ndarray` or `list(ndarray)`
    -----------

    Usage:
    >>> data = read_Pos([ '/home/cossim/CosmicGrowth/6620/simu/pos6620.5000.01', 
                        '/home/cossim/CosmicGrowth/6620/simu/pos6620.5000.02', 
                        '/home/cossim/CosmicGrowth/6620/simu/pos6620.5000.03', 
                        '/home/cossim/CosmicGrowth/6620/simu/pos6620.5000.04', ], 
                Nparticles = 3072**3 ,  
                is_IC = False, 
                has_info = False,  )
    '''
    HeaderSize = 48
    if isinstance(files, str):
        if is_header is None:
            raise ValueError(" `is_header` should be set. ")
        file_list = [files]
        HeaderSize_list = [ HeaderSize*(is_header+is_IC) ]
    elif isinstance(files, list):
        file_list = files
        HeaderSize_list = [ HeaderSize*(1+is_IC) ] + [ 0, ]*(len(files)-1)
    else:
        raise FileNotFoundError(" `files` should be a string or a list. ")
    if Nparticles is None:
        raise ValueError(" The total number of simulation particles `Nparticles` should be set. ")
    
    DataList = []
    for ifile, filename in enumerate(file_list):
        dataRead = FortranRead( filename, 
                                dType = "float32", 
                                DataSize = Nparticles*3//4,   ## (x, y, z)-componets. The pos/vel data is splitted into 4 parts
                                HeaderSize = HeaderSize_list[ifile], 
                                has_info = has_info, )
        DataList.append( dataRead.reshape(-1, 3) )
        print( "read file: "+filename+" done ... " )
    
    if isinstance(files, str):
        return DataList[0]
    elif if_stack:
        print("stacking ... ")
        return np.vstack( DataList )
    else:
        return DataList





def read_ID( 
    files, 
    if_stack = True ,
    Nparticles = None,  
    has_info = False, 
    ):
    '''
    similar to `read_Pos`, but read the ID of the particles.
    '''
    if isinstance(files, str):
        file_list = [files]
    elif isinstance(files, list):
        file_list = files
    else:
        raise FileNotFoundError(" `files` should be a string or a list. ")
    if Nparticles is None:
        raise ValueError(" The total number of simulation particles `Nparticles` should be set. ")
    
    DataList = []
    for ifile, filename in enumerate(file_list):
        dataRead = FortranRead( filename, 
                                dType = "int64", 
                                DataSize = Nparticles //2, 
                                HeaderSize = 0, 
                                has_info = has_info, )
        DataList.append( dataRead )
        print( "read file: "+filename+" done ... " )
    if if_stack:
        print("stacking ... ")
        return np.vstack( DataList )
    else:
        if isinstance(files, str):
            return DataList[0]
        return DataList





def read_Pos_rand( files:str, randrate:float=0.001 ):
    '''
    see read_Pos.
        return a random choice sample of snapshot data
    '''
    data_list = read_Pos( files, if_stack=False )
    shape0 = data_list[0].shape[0]
    shape1 = int( randrate* shape0 *1.01 )
    ndata = len(data_list)
    # DO NOT use the function 'numpy.random.choice' with option replace=False. This method fails when 'a' is large
    # 'numpy.random.choice' + 'np.unique' work well
    index_rand = np.random.choice( shape0, shape1, replace=True )
    index_rand = np.unique( index_rand )
    shape1 = index_rand.shape[0]
    print( "random choice, particle number: %1.0f -> %1.0f "%( shape0*ndata, shape1*ndata ) )
    data_stack = np.zeros((shape1*ndata, 3))
    for idata in range(ndata):
        data_stack[ idata*shape1 : (idata+1)*shape1 ] = data_list[idata][index_rand]
    return np.vstack( data_stack )



def read_header( filename:str ):
    '''
    header of the particle snapshot data
    '''
    fopen = open( filename, "rb" )
    fopen.read(4)
    npp, ips = np.fromfile( fopen, count=2, dtype=np.dtype('i8') )
    ztp, omgt, lbdt, boxsize, xscale, vscale = np.fromfile( fopen, count=6, dtype=np.dtype('f4') )
    fopen.close()
    #npp,ips, = np.fromfile( filename, offset=4, count=2, dtype=np.dtype('i8') )
    #[ ztp, omgt, lbdt, boxsize, xscale, vscale ] = np.fromfile( filename, offset=4+8*2, count=6, dtype=np.dtype('f4') )
    return { "Np":npp, "nstepf":ips, 
            "redshift":ztp, "Omega_m":omgt, "Omega_l":lbdt, 
            "boxsize":boxsize, "xscale":xscale, "vscale":vscale }



def read_header_IC( 
    filename:str = f'/home/cossim/CosmicGrowth/6620/IC/pos6620.0025.01', 
    ):
    '''
    header of the IC particle
    '''
    fopen = open( filename, "rb" )
    fopen.read(4)
    ng, npp = np.fromfile( fopen, count=2, dtype=np.dtype('i8') )
    omega0, lambda0, ztp, boxsize = np.fromfile( fopen, count=4, dtype=np.dtype('f4') )
    ips, = np.fromfile( fopen, count=1, dtype=np.dtype('i8') )
    delta, = np.fromfile( fopen, count=1, dtype=np.dtype('f4') )
    iseed, ipos, = np.fromfile( fopen, count=2, dtype=np.dtype('i8') )
    alpha, omgt, lbdt, = np.fromfile( fopen, count=3, dtype=np.dtype('f4') )
    xscale=1.
    vscale=1.
    ztp=ztp-1.
    return { "Np":npp, "nstepf":ips, 
            "redshift":ztp, "Omega_m":omgt, "Omega_l":lbdt, 
            "boxsize":boxsize, "xscale":xscale, "vscale":vscale }





def read_unit( filename:str, option='vel' ):
    '''
    In the snapshot data, the position and velocity are normalized, where 
        the position is normalized to [0, 1], 
        the velocity is normalized to `s_{redshift-space} = x + v * vfact2`.
    Here, we return the unit of the position, rescale to [Mpc/h].
                    the unit of the velocity, rescale to v/(aH) --> [ (km/s)/(aH) ].
    After the rescaling, one can get the redshift-space position by `s = x + v`.
    '''
    info = read_header( filename )
    if option=='pos':
        return info["boxsize"]
    elif option=='vel':
        ips = info["nstepf"]
        alpha = 1.
        dp = 0.0288      # depends on the simulation `nstepf`
        scalep = ips*dp + 1.
        vfact2 = alpha*scalep
        return vfact2 *info["boxsize"]
    else:
        raise ValueError("option should be 'pos' or 'vel' ")



def read_VelUnit( L=1200, ips=5000, ):
    '''
    return the velocity unit, rescale to v/(aH) --> [ (km/s)/(aH) ].

    similar to:
    ----------
    read_unit( filename:str, option='vel' )
    '''
    alpha = 1.
    dp = 0.0288
    scalep = ips*dp + 1.
    vfact2 = alpha*scalep
    return vfact2 *L




