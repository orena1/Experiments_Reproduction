import mpi4py
from mpi4py import MPI
import os

CW = MPI.COMM_WORLD


def test_mpi():
    print "bglib_pyutils: rank %d of %d" % (CW.rank, CW.size)

def write_all_spikes(spikevec, idvec, path, out="out.dat"):
    """ Serializes the writing of spikes """

    out_filename = os.path.join(path, out)
    
    for writing_rank in xrange(CW.size):
        if CW.rank==writing_rank:
            # this ranks turn to write the spikes
            if CW.rank==0:
                # rank=0 creates
                f = file(out_filename,'w')
            else:
                # other ranks append 
                f = file(out_filename,'a')

            # write spikes
            for i in xrange(len(spikevec)):
                print >> f, "%g\t%d" % (spikevec[i], idvec[i])

            f.close()
            #print "rank=%d wrote+wait" % CW.rank
            CW.Barrier()
        else:
            # this rank is waiting for another rank to write
            #print "rank=%d waiting" % CW.rank
            CW.Barrier()
    
    
    
