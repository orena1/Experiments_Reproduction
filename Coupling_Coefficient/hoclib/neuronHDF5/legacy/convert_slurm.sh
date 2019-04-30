#!/bin/bash
set -x
#echo "1: |$1|"
#echo "2: |$2|"

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
    mkdir -p $2
    #echo "Second argument must be a directory"
    #echo "Usage: $0 <Input ASC File> <Output Directory>"
    #exit 1
fi

# Get the cannonical path to the files in question
# This is necessary because we are going to explicitly change
# directories in this script, and we want this to still run
# correctly from any location.
#inputfile=`readlink -f $1`
#outputpath=`readlink -f $2`

## #outputpath=`readlink -f $2`
## inputfile=$1
## outputpath=$2

first=$1
if [ "${first:0:1}" = "/" ]
then
    inputfile=$first
else
    inputfile=`readlink -f $first`
fi

second=$2
if [ "${second:0:1}" = "/" ]
then
    outputpath=$second
else
    outputpath=`readlink -f $second`
fi

srun special -nogui -notatty -nobanner -NFRAME 350 << EOL
strdef cwd, inputfile, outputpath 
inputfile = "$inputfile"
outputpath= "$outputpath"
load_file("mk_hdf5_2.hoc")
quit()
EOL


