#!/bin/bash
PATH=$PATH:/opt/neuron_latest/nrn/i686/bin:./
export PATH
export LD_LIBRARY_PATH=/home/bluebrain/shared/hdf5/lib
if [ ! -d "$1" ]; then
  echo "give source dir! \nusage: batchconvert SOURCEDIR"
  exit 1
fi


rm -f /opt/neuronHDF5/output/*
#rm -f /opt/neuronHDF5/to_convert.tmp
echo "" > /opt/neuronHDF5/to_convert.tmp
echo "" > /opt/neuronHDF5/failed.txt

#if [ -e "to_convert.tmp" ];then
#  echo "using existing file 'to_convert.tmp'"
#  echo "remove the file if you want to start from scratch..."
##  rm to_validate.tmp
#else
  for file in $(ls $1/*.asc)
  do 
    echo $file > /opt/neuronHDF5/to_convert.tmp
    /opt/neuronHDF5/i686/special -NFRAME 250 /opt/neuronHDF5/mk_hdf5_nr.hoc
    if [ $? -ne 0 ]; then
      echo $file >> failed.txt
    fi
  done
  for file in $(ls $1/*.ASC)
  do 
    echo $file > /opt/neuronHDF5/to_convert.tmp
    /opt/neuronHDF5/i686/special -NFRAME 250 /opt/neuronHDF5/mk_hdf5_nr.hoc
    if [ $? -ne 0 ]; then
      echo $file >> failed.txt
    fi
  done
#fi


#valid

#if [ $? -eq 0 ]; then
#  echo "exit status 0...everything is fine, deleting 'to_validate.tmp'..."
#  if [ -e "to_validate.tmp" ];then
#    rm to_validate.tmp
#  fi
#fi

echo "The converted files you find in /opt/neuronHDF5/output."
