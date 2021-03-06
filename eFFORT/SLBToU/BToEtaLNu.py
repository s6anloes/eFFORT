import numpy as np
from eFFORT.utility import BGL_form_factor, z_var, PDG, w
import abc
import scipy.integrate
import functools


class BToEtaLNu:

    def __init__(self, m_B: float, m_Eta: float, V_ub: float, eta_EW: float = 1.0066) -> None:
        # Some of the following can be inherited from a parent class / initialized from a super constructor in the
        # future.
        self.m_B = m_B
        self.m_Eta = m_Eta
        self.V_ub = V_ub
        self.eta_EW = eta_EW
        self.G_F = PDG.G_F

        self.w_min = 1
        self.w_max = (m_B ** 2 + m_Eta ** 2) / (2 * m_B * m_Eta)

        # Variables which are often used and can be computed once
        self.r = self.m_Eta / self.m_B
        #self.rprime = 2 * np.sqrt(self.m_B * self.m_D2S) / (self.m_B + self.m_D2S)

        self._gamma_int = self._Gamma()

    @abc.abstractmethod
    def G(self, w: float) -> float:
        pass

    def dGamma_dw(self, w):
        # For easier variable handling in the equations
        m_B = self.m_B
        m_Eta = self.m_Eta

        return self.G_F**2 * m_Eta**3 / 48 / np.pi**3 * (m_B + m_Eta) *2 * (w**2 - 1)**(3/2) * self.eta_EW ** 2 * self.V_ub ** 2 * self.G(w)**2

    def _Gamma(self):
        w_min = 1
        w_max = (self.m_B ** 2 + self.m_Eta ** 2) / (2 * self.m_B * self.m_Eta)
        return scipy.integrate.quad(self.dGamma_dw, w_min, w_max)[0]

        

class BToEtaLNuISGW2(BToEtaLNu):

    def __init__(self, m_B: float, m_Eta: float, V_ub: float, eta_EW: float = 1.0066):

        super(BToEtaLNuISGW2, self).__init__(m_B, m_Eta, V_ub, eta_EW)

        # ISGW2 specifics
        

    def G(self, w: float) -> float:

        #Probably quark masses b and d quark in GeV: See ISGW1 below equation (14), but b quark mass would be slightly off
        #Not actual masses but masses if only valence quarks contributed to hadron mass?
        msb=5.2
        msd=0.33
        
        # Beta_B^2
        bb2=0.431*0.431

        # Hyperfine-averaged physical mass of B-meson
        mbb=5.31

        # Number of flavours below b 
        nf = 4.0

        # Mass of decay meson b->qlv (from now on called daughter meson), in this case should be an up quark
        msq=0.33
        # 
        bx2=0.406*0.406
        # Probably Hyperfine-averaged physical mass of daughter meson
        mbx=0.75*0.770+0.25*0.14
        # N_f^' (N f prime): Number of flavours below daughter meson (probably)
        nfp = 0.0

        # Probably m_B(meson) = m_b(quark) + m_d(quark)    mtb for m tilde B: see ISGW1 page 804, second column, first line
        mtb = msb + msd
        # Probalby same here: m_X(daughter meson) = m_(daughter quark q: c or u quark) + m_d(quark)
        mtx = msq + msd

        # B-Meson mass in GeV, already defined in class variable m_B #############################################################################################
        mb=self.m_B
        # Mass of X in B->Xlv
        mx=self.m_Eta

        # ISGW1 Equation (B4): mu_+ and mu_-
        mup=1.0/(1.0/msq+1.0/msb)
        mum=1.0/(1.0/msq-1.0/msb)

        # ISGW1 Equation (B2): Beta_BX^2 meaning ???
        bbx2=0.5*(bb2+bx2)
        # ISGW1 Equation (B3): Maximum momentum transfer 
        tm=(mb-mx)*(mb-mx)
        t = mb ** 2 + mx ** 2 - 2 * w * mb * mx
        # t = self.q2(w)


        # If t=q2 above maximum, reduce it accordingly
        try:
            for i in t:
                if i > tm:
                    i=0.99*tm
        except TypeError:
            if t > tm:
                t = 0.99*tm
        # Equation (20): w~
        wt=1.0+(tm-t)/(2.0*mbb*mbx)

        # Quark model scale where running coupling has been assumed to saturate (see APPENDIX A)  from page 21, first paragraph
        mqm = 0.1

        # Strong coupling constant at scale mqm
        As0 = self.Getas(mqm, mqm)

        # Strong coupling constant at scale mqs
        As2 = self.Getas(msq, msq)

        #self.ratio = As0/As2

        # Equation (24) including (25): Convential charge radius r^2
        # As0 = alpha_s(mu_qm)     As2 = alpha_s(m_q)
        r2 = 3.0/(4.0*msb*msq) + 3*msd*msd/(2*mbb*mbx*bbx2) + (16.0/(mbb*mbx*(33.0-2.0*nfp)))*np.log(As0/As2)

        # ISGW1 Equation (B1) but not exactly. Some approximation?
        # See first sentence second paragraph of APPENDIX C: Leads to equation (27) which replaces exp(..) in (B1) with term in (27) where N=2 it seems.
        # N = 2 + n + n'       n and n' are the harmonicoscillator quantum numbers of the initial and final wavefunctions 
        # (i.e., N=2 for S-wave to S-wave, N=3 for S-wave to P-wave, N=4 for S-wave to S′-wave, etc.)
        N_f3 = 2.0
        f3 = np.sqrt(mtx/mtb) * (np.sqrt(bx2*bb2)/bbx2)**1.5 / (1.0+r2*(tm-t)/(6.0*N_f3))**N_f3


        # Equation (7)
        ai = -1.0 * (6.0 / (33.0 - 2.0*nf))
        # Strong coupling constants at different scales
        As_msb = self.Getas(msb,msb)
        As_msq = self.Getas(msq,msq)
        # Equation (6) without second term
        cji = (As_msb / As_msq)**ai
        # Equation (18)
        zji = msq / msb
        # Equation (16)
        gammaji = self.GetGammaji(zji)
        # Equation (17)
        chiji = -1.0 - gammaji/(1-zji)
        # Equations (10) & (11)
        betaji_fppfm = gammaji - (2.0/3.0)*chiji
        betaji_fpmfm = gammaji + (2.0/3.0)*chiji
        # appears in equation (101). Defintion in text above
        rfppfm = cji * (1.0 + betaji_fppfm * self.Getas(msq, np.sqrt(msb*msq)) / np.pi)
        rfpmfm = cji * (1.0 + betaji_fpmfm * self.Getas(msq, np.sqrt(msb*msq)) / np.pi)
        # Equation (?): F_3^(f_+ + f_-)      See first few sentences in second paragraph of APPENDIX C
        f3fppfm = f3 * (mbb/mtb)**(-0.5) * (mbx/mtx)**0.5
        # Equation (?): F_3^(f_+ - f_-)
        f3fpmfm = f3 * (mbb/mtb)**0.5 * (mbx/mtx)**(-0.5)

        
        # Equation (101): f_+ + f_-
        fppfm = f3fppfm * rfppfm * (2.0 - (mtx/msq) * (1 - msd*msq*bb2/(2.0*mup*mtx*bbx2)))
        # Equation (102): f_+ - f_- 
        fpmfm = f3fpmfm * rfpmfm * (mtb/msq) * (1 - msd*msq*bb2/(2.0*mup*mtx*bbx2))

        fppf = (fppfm + fpmfm) / 2.0
        fpmf = (fppfm - fpmfm) / 2.0

        return fppf



    def q2(self, w):
        q2 = (self.m_B ** 2 + self.m_Eta ** 2 - 2 * w * self.m_B * self.m_Eta)
        return q2

    def Getas(self, massq, massx):
        lqcd2 = 0.04
        nflav = 4
        temp = 0.6

        if massx > 0.6:
            if massq < 1.85:
                nflav = 3
            
            temp = 12.0*np.pi / ((33.0-2.0*nflav) * np.log(massx*massx/lqcd2))
        
        return temp

    def GetGammaji(self, z):
        temp = 2+((2.0*z)/(1-z))*np.log(z)
        temp = -1.0*temp

        return temp


class BToEtaLNuLCSR_BZ(BToEtaLNu):

    def __init__(self, m_B: float, m_Eta: float, V_ub: float, eta_EW: float = 1.0066, param=[0.231, 0.851, 0.411, 5.33]):
        self.parameters = param#[
        # Ball-Zwicky calculation 2007  JHEP. 0708:025
        #    0.231, # fzero
        #    0.851, # alpha
        #    0.411,  # r
        #    5.33   # mB*
            #]
        super(BToEtaLNuLCSR_BZ, self).__init__(m_B, m_Eta, V_ub, eta_EW)

    def G(self, w):
        q2 = self.q2(w)
        pars = self.parameters[0:4]
        return pars[0] * ( 1./(1.- (q2/pars[3]**2)) + (pars[2] * q2 / pars[3]** 2)/((1.- q2/pars[3] ** 2)*(1.- (pars[1] *q2)/self.m_B ** 2)))

    def q2(self, w):
        q2 = (self.m_B ** 2 + self.m_Eta ** 2 - 2 * w * self.m_B * self.m_Eta)
        return q2
    
    
    
class BToEtaLNuLCSR_DM(BToEtaLNu):

    def __init__(self, m_B: float, m_Eta: float, V_ub: float, eta_EW: float = 1.0066, param=[0.168, 0.462, 5.3252]):
        self.parameters = param#[
        # G. Duplancic, B. Melic calculation 2015 https://arxiv.org/abs/1508.05287  JHEP 1511 (2015) 138
        #    0.168, # fzero
        #    0.462, # alpha
        #    5.3252   # mB*
            #]
        super(BToEtaLNuLCSR_DM, self).__init__(m_B, m_Eta, V_ub, eta_EW)

    def G(self, w):
        q2 = self.q2(w)
        pars = self.parameters[0:3]
        return pars[0] / ((1 - q2/pars[2] **2)*(1- pars[1] * q2 /pars[2] ** 2))
    
    def q2(self, w):
        q2 = (self.m_B ** 2 + self.m_Eta ** 2 - 2 * w * self.m_B * self.m_Eta)
        return q2
