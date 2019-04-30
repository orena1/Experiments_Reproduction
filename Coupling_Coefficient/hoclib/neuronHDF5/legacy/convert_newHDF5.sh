#!/bin/sh

export LD_LIBRARY_PATH=/opt/hdf5/lib
cd /opt/neuronHDF5
/opt/simulators/pneuron/nrnmpi/x86_64/bin/nrngui -NFRAME 350 << felix
strdef cwd, inputfile, outputpath 
inputfile = "$1"
outputpath= "$2"
//print "Argument is ", str
load_file("mk_newhdf5.hoc")
quit()
