import pymc as pm
import numpy as np

__all__ = ['FieldStepper', 'combine_spatial_inputs','generic_spatial_submodel']

def combine_spatial_inputs(lon,lat):
    # Convert latitude and longitude from degrees to radians.
    lon = lon*np.pi/180.
    lat = lat*np.pi/180.
    
    # Make lon, lat tuples.
    data_mesh = np.vstack((lon, lat)).T 
    return data_mesh

def basic_spatial_submodel(lon, lat, covariate_values, cpus):
    logp_mesh = combine_spatial_inputs(lon,lat)

    # =====================
    # = Create PyMC model =
    # =====================    
    init_OK = False
    while not init_OK:
                
        # Make coefficients for the covariates.
        m_const = pm.Uninformative('m_const', value=0.)
        
        covariate_dict = {}
        for cname, cval in covariate_values.iteritems():
            this_coef = pm.Uninformative(cname + '_coef', value=0.)
            covariate_dict[cname] = (this_coef, cval)

        V = pm.Exponential('V',.1,value=1.)

        inc = pm.CircVonMises('inc', 0,0)

        @pm.stochastic(__class__ = pm.CircularStochastic, lo=0, hi=1)
        def sqrt_ecc(value=.1):
            return 0.
        ecc = pm.Lambda('ecc', lambda s=sqrt_ecc: s**2)

        amp = pm.Exponential('amp',.1,value=1.)

        scale = pm.Exponential('scale',.1,value=1.)
        
        dd = pm.Uniform('dd',.5,3)
            
        # The mean of the field
        @pm.deterministic(trace=True)
        def M(mc=m_const):
            return pm.gp.Mean(lambda x: mc*np.ones(x.shape[0]))
        
        # The mean, evaluated  at the observation points, plus the covariates    
        @pm.deterministic(trace=False)
        def M_eval(M=M, lpm=logp_mesh, cv=covariate_dict):
            out = M(lpm)
            for c in cv.itervalues():
                out += c[0]*c[1]
            return out

        # Create covariance and MV-normal F if model is spatial.   
        try:
            # A Deterministic valued as a Covariance object. Uses covariance my_st, defined above. 
            @pm.deterministic(trace=True)
            def C(amp=amp,scale=scale,inc=inc,ecc=ecc):
                return pm.gp.FullRankCovariance(pm.gp.cov_funs.matern.aniso_geo_rad, amp=amp, scale=scale, inc=inc, ecc=ecc, diff_degree=dd,n_threads=cpus)

            # The evaluation of the Covariance object, plus the nugget.
            @pm.deterministic(trace=False)
            def C_eval(C=C):
                return C(logp_mesh, logp_mesh)
                                            
            # The field evaluated at the uniquified data locations
            f = pm.MvNormalCov('f',M_eval,C_eval)            
            
            init_OK = True
        except pm.ZeroProbability, msg:
            print 'Trying again: %s'%msg
            init_OK = False
            gc.collect()

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