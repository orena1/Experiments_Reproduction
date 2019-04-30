#!/usr/bin/env bash
set -e

USAGE="Usage: $0 [-h] [-n] <Input ASC File> <Output Directory>
where:
    -h: show usage
    -n: norecenter - don't recenter the neuron based on the soma center
"

if [[ -z $1 ]]; then
    echo "$USAGE"
    exit 1
fi

if [[ -z $HOC_LIBRARY_PATH ]]; then
    HOC_LIBRARY_PATH=$(dirname "$(dirname "$(readlink -f "$0")")")/hoclib
fi

# ensure that neuronHDF5 is included in HOC_LIBRARY_PATH
export HOC_LIBRARY_PATH=$HOC_LIBRARY_PATH:$HOC_LIBRARY_PATH/neuronHDF5

NORECENTER=0
NFRAME=1500

while getopts "hnf:" FLAG; do
case "$FLAG" in
    f) NFRAME=$OPTARG;;
    h) echo "$USAGE";;
    n) NORECENTER=1;;
esac
done

INPUTFILE=${*:$OPTIND:1}
OUTPUTPATH=${*:$OPTIND+1:1}

# Get the cannonical path to the files in question
INPUTFILE=$(readlink -f "$INPUTFILE")
OUTPUTPATH=$(readlink -f "$OUTPUTPATH")

if [[ ! -f $INPUTFILE ]]; then
    printf "First argument must be a file\n\n"
    echo "$USAGE"
    exit 1
fi

if [[ ! -d $OUTPUTPATH ]]; then
    echo "Making output directory: $OUTPUTPATH"
    mkdir -p "$OUTPUTPATH"
fi

# user PATH and HOC_LIBRARY_PATH environmental variables are expected to be set
# when this script is invoked
special -nogui -notatty -nobanner -NFRAME "$NFRAME" << EOL
strdef cwd, inputfile, outputpath
inputfile="$INPUTFILE"
outputpath="$OUTPUTPATH"
norecenter=$NORECENTER
//print "Argument is ", str
{load_file("mk_hdf5_2.hoc")}
quit()
EOL
