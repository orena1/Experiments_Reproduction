#!/bin/sh

if [ "$1" = "" -o "$2" = "" ]
then
    echo "Usage: $0 <Input ASC File> <Output Directory>"
    exit 1
fi

if [ ! -f "$1" ]
then
    echo "First argument must be a file"
    echo "Usage: $0 <Input ASC File> <Output Directory>"
    exit 1
fi

if [ ! -d "$2" ]
then
    echo "Second argument must be a directory"
    echo "Usage: $0 <Input ASC File> <Output Directory>"
    exit 1
fi

# Get the cannonical path to the files in question
# This is necessary because we are going to explicitly change
# directories in this script, and we want this to still run
# correctly from any location.
inputfile=`readlink -f $1`
outputpath=`readlink -f $2`


#export LD_LIBRARY_PATH=/home/bluebrain/shared/hdf5/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/simulators/pneuron/04.11.10/iv/x86_64/lib/
cd /opt/neuronHDF5
/opt/simulators/pneuron/nrnmpi/x86_64/bin/nrngui -nogui -notatty -nobanner -NFRAME 350 << EOL
strdef cwd, inputfile, outputpath 
inputfile = "$inputfile"
outputpath= "$outputpath"
//print "Argument is ", str
load_file("mk_hdf5_2_nr.hoc")
quit()
EOL

