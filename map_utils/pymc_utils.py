import pymc as pm
import numpy as np
import time

__all__ = ['FieldStepper', 'combine_spatial_inputs','combine_st_inputs','basic_spatial_submodel', 'basic_st_submodel','st_mean_comp']

def spatial_mean(x, m_const):
    return m_const*np.ones(x.shape[0])

def st_mean_comp(x, m_const, t_coef):
    lon = x[:,0]
    lat = x[:,1]
    t = x[:,2]
    return m_const + t_coef * t

def combine_spatial_inputs(lon,lat):
    # Convert latitude and longitude from degrees to radians.
    lon = lon*np.pi/180.
    lat = lat*np.pi/180.
    
    # Make lon, lat tuples.
    data_mesh = np.vstack((lon, lat)).T 
    return data_mesh
    
def combine_st_inputs(lon,lat,t):
    # Convert latitude and longitude from degrees to radians.
    lon = lon*np.pi/180.
    lat = lat*np.pi/180.

    # Convert time to end year - 2009 (no sense forcing mu to adjust by too much).
    t = t - 2009

    # Make lon, lat, t triples.
    data_mesh = np.vstack((lon, lat, t)).T 
    return data_mesh
    
def basic_spatial_submodel(lon, lat, covariate_values, prior_params = {}):
    """
    A stem for building spatial models.
    """
    logp_mesh = combine_spatial_inputs(lon,lat)

    # =====================
    # = Create PyMC model =
    # =====================    
                
    # Make coefficients for the covariates.
    m_const = pm.Uninformative('m_const', value=0.)
    
    covariate_dict = {}
    for cname, cval in covariate_values.iteritems():
        this_coef = pm.Uninformative(cname + '_coef', value=0.)
        covariate_dict[cname] = (this_coef, cval)

    inc = pm.CircVonMises('inc', 0,0)

    @pm.stochastic(__class__ = pm.CircularStochastic, lo=0, hi=1)
    def sqrt_ecc(value=.1):
        return 0.
    ecc = pm.Lambda('ecc', lambda s=sqrt_ecc: s**2)

    amp = pm.Exponential('amp',.1,value=1.)

    scale_shift = pm.Exponential('scale_shift',.1,value=1.)
    scale = pm.Lambda('scale',lambda ss=scale_shift:ss+.1)
    
    
    for s in [sqrt_ecc, amp, scale]:
        if prior_params.has_key(s.__name__):
            s.parents.update(prior_params[s.__name__])
        
    # The mean of the field
    @pm.deterministic(trace=True)
    def M(mc=m_const):
        return pm.gp.Mean(spatial_mean, m_const=mc)
    
    # The mean, evaluated  at the observation points, plus the covariates    
    @pm.deterministic(trace=False)
    def M_eval(M=M, lpm=logp_mesh, cv=covariate_dict):
        out = M(lpm)
        for c in cv.itervalues():
            out += c[0]*c[1]
        return out

    # A Deterministic valued as a Covariance object. Uses covariance my_st, defined above. 
    @pm.deterministic(trace=True)
    def C(amp=amp,scale=scale,inc=inc,ecc=ecc):
        return pm.gp.FullRankCovariance(pm.gp.cov_funs.exponential.aniso_geo_rad, amp=amp, scale=scale, inc=inc, ecc=ecc)
    
    # @pm.deterministic(trace=True)
    # def C(amp=amp,scale=scale):
    #     return pm.gp.FullRankCovariance(pm.gp.cov_funs.exponential.geo_rad, amp=amp, scale=scale)
    
    # The evaluation of the Covariance object, plus the nugget.
    @pm.deterministic(trace=False)
    def C_eval(C=C):
        out = C(logp_mesh, logp_mesh)
        return out
    
    return locals()


def basic_st_submodel(lon, lat, t, covariate_values, cpus, prior_params={}):
    
    logp_mesh = combine_st_inputs(lon,lat,t)
                
    # Make coefficients for the covariates.
    m_const = pm.Uninformative('m_const', value=0.)
    t_coef = pm.Uninformative('t_coef',value=.1)        
    covariate_dict = {}
    for cname, cval in covariate_values.iteritems():
        this_coef = pm.Uninformative(cname + '_coef', value=0.)
        covariate_dict[cname] = (this_coef, cval)

    inc = pm.CircVonMises('inc', 0,0)

    @pm.stochastic(__class__ = pm.CircularStochastic, lo=0, hi=1)
    def sqrt_ecc(value=.1):
        return 0.
    ecc = pm.Lambda('ecc', lambda s=sqrt_ecc: s**2)

    # log_amp = pm.Uninformative('log_amp', value=0)
    # amp = pm.Lambda('amp', lambda la = log_amp: np.exp(la))
    amp = pm.Exponential('amp',.1,value=1.)

    # log_scale = pm.Uninformative('log_scale', value=0)
    # scale = pm.Lambda('scale', lambda ls = log_scale: np.exp(ls))
    scale = pm.Exponential('scale',.1,value=1.)

    # log_scale_t = pm.Uninformative('log_scale_t', value=0)
    # scale_t = pm.Lambda('scale_t', lambda ls = log_scale_t: np.exp(ls))
    scale_t = pm.Exponential('scale_t',.1,value=.1)
    
    @pm.stochastic(__class__ = pm.CircularStochastic, lo=0, hi=1)
    def t_lim_corr(value=.2):
        return 0.
    ecc = pm.Lambda('ecc', lambda s=sqrt_ecc: s**2)

    @pm.stochastic(__class__ = pm.CircularStochastic, lo=0, hi=1)
    def sin_frac(value=.1):
        return 0.
    
    for s in [inc, sqrt_ecc, amp, scale, scale_t, t_lim_corr, sin_frac]:
        if prior_params.has_key(s.__name__):
            s.parents.update(prior_params[s.__name__])

    # The mean of the field
    @pm.deterministic
    def M(mc=m_const, tc=t_coef):
        return pm.gp.Mean(st_mean_comp, m_const = mc, t_coef = tc)
    
    # The mean, evaluated  at the observation points, plus the covariates    
    @pm.deterministic(trace=False)
    def M_eval(M=M, lpm=logp_mesh, cv=covariate_dict):
        out = M(lpm)
        for c in cv.itervalues():
            out += c[0]*c[1]
        return out
        
    # A constraint on the space-time covariance parameters that ensures temporal correlations are 
    # always between -1 and 1.
    @pm.potential
    def st_constraint(sd=.5, sf=sin_frac, tlc=t_lim_corr):    
        if -sd >= 1./(-sf*(1-tlc)+tlc):
            return -np.Inf
        else:
            return 0.

    # A Deterministic valued as a Covariance object. Uses covariance my_st, defined above. 
    @pm.deterministic
    def C(amp=amp,scale=scale,inc=inc,ecc=ecc,scale_t=scale_t, t_lim_corr=t_lim_corr, sin_frac=sin_frac):
        return pm.gp.FullRankCovariance(my_st, amp=amp, scale=scale, inc=inc, ecc=ecc,st=scale_t, sd=.5,
                                        tlc=t_lim_corr, sf = sin_frac, n_threads=cpus)

    # The evaluation of the Covariance object, plus the nugget.
    @pm.deterministic(trace=False)
    def C_eval(C=C):
        return C(logp_mesh, logp_mesh)
                                   

class CovariateStepper(pm.StepMethod):

    def __init__(self, covariate_dict, m_const, t, t_coef, M_eval, sig, d):
        self.m_const = m_const
        self.t_coef=t_coef
        self.M = M_eval
        self.sig = sig
        self.d = d.value

        cvv = covariate_dict.values()
        self.beta = pm.Container([self.m_const, self.t_coef]+[v[0] for v in cvv])
        self.x = np.vstack((np.ones((1,len(t))), np.atleast_2d(t), np.asarray([v[1] for v in cvv])))

        pm.StepMethod.__init__(self, self.beta)

    def step(self):

        pri_sig = np.asarray(self.sig.value)
        lo = pm.gp.trisolve(pri_sig, self.x.T, uplo='L').T
        post_tau = np.dot(lo,lo.T)
        l = np.linalg.cholesky(post_tau)

        post_C = pm.gp.trisolve(l, np.eye(l.shape[0]),uplo='L')
        post_C = pm.gp.trisolve(l.T, post_C, uplo='U')

        post_mean = np.dot(lo, pm.gp.trisolve(pri_sig, self.d, uplo='L'))
        post_mean = pm.gp.trisolve(l, post_mean, uplo='L')
        post_mean = pm.gp.trisolve(l.T, post_mean, uplo='U')

        new_val = pm.rmv_normal_cov(post_mean, post_C).squeeze()

        [b.set_value(nv) for (b,nv) in zip(self.beta, new_val)]

                                    
class FieldStepper(pm.StepMethod):
    """
    A special Gibbs stepper that updates tau and f together give eps_p_f
    and the mean and covariance parameters. Why did I update tau and f together?
    I don't remember. Probably grasping at straws trying to improve mixing
    at some point. This doesn't save any Cholesky decompositions or covariance 
    evaluations.
    """
    def __init__(self, f, tau, V, C_eval, M_eval, logp_mesh, eps_p_f, ti, incomp_jump=False, jump_tau = True):
        self.f = f
        self.tau = tau
        self.V = V
        self.C_eval = C_eval
        self.M_eval = M_eval
        self.logp_mesh = logp_mesh
        self.eps_p_f = eps_p_f
        self.incomp_jump = incomp_jump
        self.ti = ti
        
        self.scratch1 = np.asmatrix(np.empty(self.C_eval.value.shape, order='F'))
        self.scratch2 = np.asmatrix(np.empty(self.C_eval.value.shape, order='F'))
        self.scratch3 = np.empty(self.M_eval.value.shape)     

        self.jump_tau = jump_tau
        if self.jump_tau:
            pm.StepMethod.__init__(self,[f,tau])
        else:
            pm.StepMethod.__init__(self,[f])
            
        self.time = 0.
        self.incomp_time = 0.
    
    def step(self):
        
        fc = pm.gp.fast_matrix_copy
        
        t1 = time.time()
    
        eps_p_f = self.eps_p_f.value
        f = self.f.value
        for i in xrange(len(self.scratch3)):
            self.scratch3[i] = np.sum(eps_p_f[self.ti[i]] - f[i])
    
        if self.jump_tau:
            # tau's full conditional is Gamma.
            amp_alph = eps_p_f.shape[0]/2.+1.
            tau_alph = amp_alph + self.tau.parents['alpha']
            tau_vec = self.scratch3 - self.f.value
            tau_bet = np.dot(tau_vec, tau_vec)/2. + self.tau.parents['beta']
            self.tau.value = pm.rgamma(tau_alph,tau_bet)

        # Compute Cholesky factor of covariance of eps_p_f, C(x,x) + V
        in_chol = fc(self.C_eval.value, self.scratch1)
        for i in xrange(self.logp_mesh.shape[0]):
            in_chol[i,i] += self.V.value / len(self.ti[i])
        info = pm.gp.linalg_utils.dpotrf_wrap(in_chol)
        if info > 0:
            raise np.linalg.LinAlgError

        # Compute covariance of f conditional on eps_p_f.
        offdiag = fc(self.C_eval.value, self.scratch2)
        offdiag = pm.gp.trisolve(in_chol, offdiag, uplo='U', transa='T', inplace=True)

        C_step = offdiag.T * offdiag
        C_step *= -1
        C_step += self.C_eval.value
        
        # Compute mean of f conditional on eps_p_f.
        for i in xrange(len(self.scratch3)):
            self.scratch3[i] = np.mean(eps_p_f[self.ti[i]])
        m_step = self.M_eval.value + np.dot(offdiag.T, pm.gp.trisolve(in_chol,(self.scratch3 - self.M_eval.value),uplo='U',transa='T')).view(np.ndarray).ravel()
        
        sig_step = C_step
        info = pm.gp.linalg_utils.dpotrf_wrap(C_step.T)
        if info > 0:
            print 'WARNING: Cholesky decomposition of full conditional covariance not positive definite.'
            return
            raise np.linalg.LinAlgError
        
        # Update value of f.
        self.f.value = m_step+np.dot(sig_step,np.random.normal(size=sig_step.shape[1])).view(np.ndarray).ravel()
        
        t2 = time.time()
        self.time += t2-t1