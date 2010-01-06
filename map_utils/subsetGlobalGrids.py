# import libraries
from mbgw import master_grid
import tables as tb
from numpy import *

# set some parameters
#resRatio=5  # ratio between resolution of grids defines in master_grid, and the ones being subsetted here
datafolder = "/home/pwg/mbg-world/datafiles/auxiliary_data/GridsForCS/"



################################################################################################################################################
# using row/col numbers of a subset specified for 5km grids (and stored in master_grid), extract the same subset for corresponding 1km grids

def subsetGlobalGrids (region,lims,gridname,resRatio = 1):
    # build input path for the global grid
    input_path = datafolder+gridname+".hdf5"

    # build ouput paths for this region and grid 
    output_path = datafolder+gridname+"_"+region+".hdf5"

    # open link to full sized 1km file
    fullHDF5 = tb.openFile(input_path, mode = "r")    

    # get 1km row/cols for this subset from the pre-defined object in mbgw 'master_grid' (NB - the values therein were entered manually after running the R script DefineSubsetCoordinates.R)
    br=(lims['bottomRow'])*resRatio
    tr=(lims['topRow']-1)*resRatio
    lc=(lims['leftCol']-1)*resRatio
    rc=(lims['rightCol'])*resRatio

    # define subsetted lat and long vector
    long = fullHDF5.root.long[lc:rc:1]
    lat = fullHDF5.root.lat[tr:br:1]

    nrows = len(lat)
    ncols = len(long)

    #print(ncols)
    #print(nrows)

    # define subsetted grid
    gridsubset = fullHDF5.root.data[tr:br:1,lc:rc:1]
    #print(mean(gridsubset))
    #print(shape(gridsubset))
    #print (type(gridsubset))
    ##
    ## now build new hdf5 file for subsetted grid
    ##

    # Initialize hdf5 archive
    outHDF5 = tb.openFile(output_path, mode='w', title=gridname+'_'+region)

    # build grid metadata 
    outHDF5.root._v_attrs.asc_file = 'subsetted from hdf5 file: '+input_path
    outHDF5.root._v_attrs.ncols = ncols
    outHDF5.root._v_attrs.nrows = nrows
    outHDF5.root._v_attrs.missing = fullHDF5.root._v_attrs.missing
    outHDF5.root._v_attrs.order = fullHDF5.root._v_attrs.order
    outHDF5.root._v_attrs.cellsize = fullHDF5.root._v_attrs.cellsize
    outHDF5.root._v_attrs.minx = long.min()
    outHDF5.root._v_attrs.maxx = long.max()
    outHDF5.root._v_attrs.miny = lat.min()
    outHDF5.root._v_attrs.maxy = lat.max()

    # Add longitude and latitude to archive, uncompressed. 
    outHDF5.createArray('/','long',long)
    outHDF5.createArray('/','lat',lat)

    # Add data to archive, heavily compressed, in a chunk array row-by-row (if a row won't fit in memory, the whole array won't fit on disk).
    outHDF5.createCArray('/', 'data', tb.Float64Atom(), (nrows, ncols), filters = tb.Filters(complevel=9, complib='zlib'),chunkshape = (1,ncols))    

    for i in xrange(nrows):
        outHDF5.root.data[i,:] = gridsubset[i,:]

    # close the files
    fullHDF5.close()
    outHDF5.close()
################################################################################################################################################
#
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "gr071km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "un_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "salblim1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "lims1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "ur1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "st_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "salb1km-e2_y-x+",resRatio=5)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "st_mask5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "gr075km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "pixarea5km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "pixarea1km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "salblim5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "salb5km-e2_y-x+",resRatio=1)
#subsetGlobalGrids(region="AM",lims = master_grid.AM_lims,gridname = "land5km_e2_y-x+",resRatio=1)

#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "gr071km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "un_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "salblim1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "lims1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "ur1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "st_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "salb1km-e2_y-x+",resRatio=5)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "st_mask5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "gr075km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "pixarea5km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "pixarea1km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "ad1_st_5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "ad1_5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "salblim5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "salb5km-e2_y-x+",resRatio=1)
#subsetGlobalGrids(region="AF",lims = master_grid.AF_lims,gridname = "land5km_e2_y-x+",resRatio=1)

#subsetGlobalGrids(region="AS",lims = master_grid.AS_lims,gridname = "gr071km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS",lims = master_grid.AS_lims,gridname = "un_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS",lims = master_grid.AS_lims,gridname = "salblim1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS",lims = master_grid.AS_lims,gridname = "lims1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS",lims = master_grid.AS_lims,gridname = "ur1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS",lims = master_grid.AS_lims,gridname = "st_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS",lims = master_grid.AS_lims,gridname = "salb1km-e2_y-x+",resRatio=5)

#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "gr071km_y-x+",resRatio=5)
#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "un_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "salblim1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "lims1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "ur1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "st_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "salb1km-e2_y-x+",resRatio=5)

#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "st_mask5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="KE",lims = master_grid.KE_lims,gridname = "gr075km_y-x+",resRatio=1)

#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "gr071km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "un_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "salblim1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "lims1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "ur1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "st_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "salb1km-e2_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "st_mask5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "gr075km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "pixarea5km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "pixarea1km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "salblim5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "salb5km-e2_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS1",lims = master_grid.AS1_lims,gridname = "land5km_e2_y-x+",resRatio=1)

#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "gr071km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "un_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "salblim1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "lims1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "ur1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "st_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "salb1km-e2_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "st_mask5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "gr075km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "pixarea5km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "pixarea1km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "land5km_e2_y-x+",resRatio=1)

#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "gr071km_y-x+",resRatio=5)
#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "un_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "salblim1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "lims1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "ur1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "st_mask1km-e_y-x+",resRatio=5)
#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "salb1km-e2_y-x+",resRatio=5)
#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "st_mask5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AMS1",lims = master_grid.AMS1_lims,gridname = "gr075km_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "salblim5km-e_y-x+",resRatio=1)
#subsetGlobalGrids(region="AS2",lims = master_grid.AS2_lims,gridname = "salb5km-e2_y-x+",resRatio=1)


subsetGlobalGrids(region="NBIA",lims = master_grid.NBIA_lims,gridname = "land5km_e2_y-x+",resRatio=1)
subsetGlobalGrids(region="NBIA",lims = master_grid.NBIA_lims,gridname = "urb5km-e_y-x+",resRatio=1)
subsetGlobalGrids(region="AFGH",lims = master_grid.AFGH_lims,gridname = "land5km_e2_y-x+",resRatio=1)
subsetGlobalGrids(region="AFGH",lims = master_grid.AFGH_lims,gridname = "urb5km-e_y-x+",resRatio=1)


