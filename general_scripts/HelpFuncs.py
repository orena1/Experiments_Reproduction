##Create Ca mg K values.
#Created by Oren Amsalem oren.a4@gamil.com
from __future__ import division
from Cheetah.Template import Template


def SetCaKThresh(ca, k, Mg):
    theshTemp.e_GABAB, theshTemp.k_inj = f_k_params(k)
    theshTemp.k_inj_dnac = theshTemp.k_inj*0.81
    return(str(theshTemp))

def SetCaK(ca, k, Mg):
    caKtemplate.K = k
    caKtemplate.Ca = ca
    caKtemplate.f_e2e, caKtemplate.f_e2pv, caKtemplate.f_i2i = [float(x) for x in f_ca_params(ca)]
    caKtemplate.e_GABAB, caKtemplate.k_inj = f_k_params(k)
    caKtemplate.k_inj_dnac = caKtemplate.k_inj*0.81
    caKtemplate.Mg = Mg
    return(str(caKtemplate))

#depolarize code 
import numpy

R = 8.135
T = 273.15 + 35 # temperature of 35 C
z = 1
F = 9.684e4
pre_factor = (R*T)/(z*F)

#0.0595864


def Erev(conc_ext, conc_int):
    return pre_factor*numpy.log(conc_ext/conc_int)*1000.0


# fractions of threshold approximation
f = lambda Vm: (Vm+85.)/30.
f = numpy.vectorize(f)

def K_Erev(conc_ext):
    return Erev(conc_ext, 93.6)

K_Erev = numpy.vectorize(K_Erev)

Em = lambda y: 1./(1.+0.2) * y + 0.2/(1.+0.2)*50
Em = numpy.vectorize(Em)

f_K = lambda k: f(Em(K_Erev(k)))




#### Ca hill 
def hill(ca_conc, y_max, K_half):
    return y_max*ca_conc**4/(K_half**4 + ca_conc**4)

def constrained_hill(K_half):
    from scipy.optimize import fsolve
    f = lambda x: hill(2.0, x, K_half)-1.0
    y_max = fsolve(f,1.0)
    f = lambda x: hill(x, y_max, K_half)
    return numpy.vectorize(f)
    

shallow_Ca = constrained_hill(1.09)
steep_Ca = constrained_hill(2.79)
intermediate_Ca = lambda x: (shallow_Ca(x) + steep_Ca(x))/2

f_ca_params = lambda ca: (steep_Ca(ca), shallow_Ca(ca), intermediate_Ca(ca))
f_k_params = lambda k: (K_Erev(k), f_K(k)*100)


Threshtemplate="""
Stimulus ThresholdExc
{

              Mode Current
           Pattern Noise
       MeanPercent $k_inj
          Variance 0.001
             Delay 0.000000
          Duration 1000000.000000
}

Stimulus ThresholdInh
{

              Mode Current
           Pattern Noise
       MeanPercent $k_inj
          Variance 0.001
             Delay 0.000000
          Duration 1000000.000000
}

Stimulus Threshold_dNAC_dSTUT
{

              Mode Current
           Pattern Noise
       MeanPercent $k_inj_dnac
          Variance 0.001
             Delay 200.000000
          Duration 1000000.000000
}"""
theshTemp = Template(Threshtemplate)



CaKtemplate = """

# Adjust global synapse parameters, e.g. reversals

Connection GABAB_erev
{
        Source Inhibitory
        Destination Mosaic
        Weight 1.0
# K= 2.5mM
#       SynapseConfigure %s.e_GABAA = -80.0 %s.e_GABAB = -93.6
# K = $K mM
        SynapseConfigure %s.e_GABAA = -80.0 %s.e_GABAB = $e_GABAB
}

Connection MGGate
{
        Source Excitatory
        Destination Mosaic
        Weight 1.0
        SynapseConfigure %s.mg = $Mg
}

# Use adjustments due to Calcium $Ca mM compared to normal 2.0 mM

Connection scheme_CaUse_ee
{       
              Source Excitatory 
         Destination Excitatory
              Weight 1.0
    SynapseConfigure %s.Use *= $f_e2e
}

Connection scheme_CaUse_e_2_PV_FS
{       
              Source Excitatory 
         Destination PV_FS
              Weight 1.0
    SynapseConfigure %s.Use *= $f_e2pv
}

Connection scheme_CaUse_PV_FS_2_e
{       
              Source PV_FS
         Destination Excitatory
              Weight 1.0
    SynapseConfigure %s.Use *= $f_e2pv
}

Connection scheme_CaUse_e_2_DISTAR_INH
{       
              Source Excitatory 
         Destination DISTAR_INH
              Weight 1.0
    SynapseConfigure %s.Use *= $f_e2e
}

Connection scheme_CaUse_DISTAR_INH_2_e
{       
              Source DISTAR_INH
         Destination Excitatory
              Weight 1.0
    SynapseConfigure %s.Use *= $f_e2e
}

Connection scheme_CaUse_e_2_Other_Inh
{       
              Source Excitatory 
         Destination Other_Inh
              Weight 1.0
    SynapseConfigure %s.Use *= $f_i2i
}

Connection scheme_CaUse_Other_Inh_2_e
{       
              Source Other_Inh
         Destination Excitatory
              Weight 1.0
    SynapseConfigure %s.Use *= $f_i2i
}

Connection scheme_CaUse_Inh_Inh
{       
              Source Inhibitory
         Destination Inhibitory
              Weight 1.0
    SynapseConfigure %s.Use *= $f_i2i
}


# Adjust AMPA_NMDA and GABAA_B ratios
Connection scheme_minus2
{       
              Source Excitatory 
         Destination Excitatory
              Weight 1.0
    SynapseConfigure %s.NMDA_ratio = 0.4
}

Connection scheme_minus1
{       
              Source Excitatory
         Destination Inhibitory
              Weight 1.0
    SynapseConfigure %s.NMDA_ratio = 0.8
}

Connection scheme5
{       
              Source L5_TTPC1
         Destination L5_TTPC1
              Weight 1.0
    SynapseConfigure %s.NMDA_ratio = 0.71
}

Connection scheme6
{       
              Source L5_TTPC2
         Destination L5_TTPC2
              Weight 1.0
    SynapseConfigure %s.NMDA_ratio = 0.71
}

Connection scheme7
{       
              Source L5_TTPC1
         Destination L5_TTPC2
              Weight 1.0
    SynapseConfigure %s.NMDA_ratio = 0.71
}

Connection scheme8
{       
              Source L5_TTPC2
         Destination L5_TTPC1
              Weight 1.0
    SynapseConfigure %s.NMDA_ratio = 0.71
}

Connection NMDA_Override_L4-L4
{
        Source Layer4Excitatory
        Destination Layer4Excitatory
        Weight 1.0
        SynapseConfigure %s.NMDA_ratio = 0.86

}

Connection NMDA_Override_L4-L23
{
        Source L4_SS
        Destination L23_PC
        Weight 1.0
        SynapseConfigure %s.NMDA_ratio = 0.5

}

Connection scheme1b
{       
              Source Layer1
         Destination Excitatory
              Weight 1.0
    SynapseConfigure %s.GABAB_ratio = 0.75
}

Connection scheme2b
{       
              Source L23_NGC
         Destination Excitatory
              Weight 1.0
    SynapseConfigure %s.GABAB_ratio = 0.75
}

Connection schemeExternal
{
          Source proj_Thalamocortical_VPM_Source
     Destination Mosaic
SynapseConfigure %s.Use = 0.86
          Weight 1.0
}


Connection scheme_CaUse_ee_tc2c
{
              Source proj_Thalamocortical_VPM_Source
         Destination Mosaic
              Weight 1.0
    SynapseConfigure %s.Use *= $f_e2e
}"""

caKtemplate = Template(CaKtemplate)



def SetFacDep(DisableUseDep):
    strChunk = ''
    for From,To in DisableUseDep:
        DisableUseDepTemplate.Name = From + '_' + To
        DisableUseDepTemplate.From = From
        DisableUseDepTemplate.To   = To
        strChunk += str(DisableUseDepTemplate)
    return(strChunk)



DisableUseDepTemp = """
Connection scheme_DisableFac_$Name
{
              Source $From
         Destination $To
              Weight 1.0
    SynapseConfigure %s.Fac = 0.0
}


Connection scheme_DisableDep_$Name
{
              Source $From
         Destination $To
              Weight 1.0
    SynapseConfigure %s.Dep = 0.0
}"""
DisableUseDepTemplate = Template(DisableUseDepTemp)




