#!/bin/bash
PATH=$PATH:/opt/simulators/pneuron/nrnmpi/x86_64/bin:./
export PATH
export LD_LIBRARY_PATH=/opt/hdf5/lib
if [ ! -d "$1" ]; then
  echo "give source dir! \nusage: batchconvert SOURCEDIR"
  exit 1
fi


rm -f /opt/neuronHDF5/output/*

  for file in $(ls $1/*.asc)
  do 
 #   echo $file
    /opt/neuronHDF5/convert.sh $file /opt/neuronHDF5/output
    if [ $? -ne 0 ]; then
      echo $file >> failed.txt
    fi
  done
  for file in $(ls $1/*.ASC)
  do 
#    echo $file
    /opt/neuronHDF5/convert.sh $file /opt/neuronHDF5/output
    if [ $? -ne 0 ]; then
      echo $file >> failed.txt
    fi
  done

echo "The converted files you find in /opt/neuronHDF5/output."
