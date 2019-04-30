#!/bin/sh

f="balinfo"	# prefix for $f.dat and $f.$n.dat
n=1024		# want a balance file for this number of cpus.
cx=360		# maximum complexity on a single cpu.

p=R1001		# partition for constructing bal.* files
np=256		# number of cpus used to construct bal.* files

if test "$1" != "" ; then f="$1"; fi
if test "$2" != "" ; then n="$2"; fi
if test "$3" != "" ; then cx="$3"; fi
if test "$4" != "" ; then p="$4"; fi
if test "$5" != "" ; then np="$5"; fi


rm -f bal.[0-9][0-9][0-9][0-9]

# transform the init.hoc file into _init.hoc
sed '
s/^multisplit_=.*/multisplit_=2/
s/^makebal=0/makebal=1/
s/^print_load_balance_info(3.*/print_load_balance_info('"3, $cx"')/
' init.hoc > _init.hoc

# construct bal.* files from an entire network spec (includes synapses)
if which bgrun ; then
	bgrun VN $p $np _init.hoc
else
	np=4
	mpiexec -np $np ~/neuron/nrnmpi/x86_64/bin/nrniv -mpi _init.hoc
fi

# construct $f.dat from bal.* files
echo $np > $f.dat
cat bal.[0-9][0-9][0-9][0-9] >> $f.dat
rm bal.[0-9][0-9][0-9][0-9]

# construct $f.$n.dat from $f.dat and $n
# requires that pmetis be in the PATH
/home/hines/neuron/nrnobj/powerpc64/bin/nrniv << here
{load_file("binfo.hoc")}
mkbalinfo("$f", $n)
quit()
here


