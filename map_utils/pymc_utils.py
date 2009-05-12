import pymc as pm
import numpy as np
import time
import tables as tb
from st_cov_fun import my_st

__all__ = ['FieldStepper', 'combine_spatial_inputs','combine_st_inputs','basic_spatial_submodel', 'basic_st_submodel',
            'st_mean_comp','add_standard_metadata','covariate_trace', 'sample_covariates_from_chain','sample_covariates',
            'predictive_mean_and_std','trivial_means','cd_and_C_eval']

def spatial_mean(x, m_const):
    return m_const*np.ones(x.shape[0])
    
def zero_mean(x):
    return np.zeros(x.shape[:-1])

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

    # Make lon, lat, t triples.
    data_mesh = np.vstack((lon, lat, t)).T 
    return data_mesh
    
def add_standard_metadata(M, logp_mesh, covariate_dict, **others):
    """
    Adds the standard metadata to an hdf5 archive.
    """
    hf = M.db._h5file
    hf.createGroup('/','metadata')
    
    weird_attrs = ['ti','vars_to_writeout','scale_params','amp_params']
    
    hf.createArray(hf.root.metadata, 'logp_mesh', logp_mesh[:])
        
    hf.createVLArray(hf.root.metadata, 'covariates', tb.ObjectAtom())
    hf.root.metadata.covariates.append(covariate_dict)
        
    for name, val in others.iteritems():
        if name in weird_attrs:
            vla=hf.createVLArray(hf.root.metadata, name, tb.ObjectAtom())
            vla.append(val)
        else:
            hf.createArray(hf.root.metadata, name, val)    
    
def cd_and_C_eval(covariate_values, C, logp_mesh, fac=1e6):
    """
    Returns a {name: value, prior variance} dictionary
    and an evaluated covariance with covariates incorporated.
    """
    covariate_dict = {}
    # Set prior variances of covariate coefficients. They're huge, and scaled.
    means = []
        
    for cname, cval in covariate_values.iteritems():
        cov_var = np.var(cval)
        cov_mean = np.abs(np.mean(cval))+np.sqrt(cov_var)
        means.append(cov_mean)
        covariate_dict[cname] = (cval, cov_var*fac)
        
    # Constant term
    covariate_dict['m'] = (np.ones(logp_mesh.shape[0]), (np.sum(np.array(means)**2) + 1)*fac)
                    
    # The evaluation of the Covariance object, plus the nugget.
    @pm.deterministic(trace=False)
    def C_eval(C=C):
        out = C(logp_mesh, logp_mesh)
        for val,var in covariate_dict.itervalues():
            out += np.outer(val,val)*var
        return out
    
    return covariate_dict, C_eval
    
def trivial_means(lpm):
    """
    Returns a trivial mean function and an evaluating node.
    """
    # The mean of the field
    @pm.deterministic(trace=True)
    def M():
        return pm.gp.Mean(zero_mean)
    
    # The mean, evaluated  at the observation points, plus the covariates    
    @pm.deterministic(trace=False)
    def M_eval(M=M, lpm=lpm):
        return M(lpm)
    return M, M_eval

def basic_spatial_submodel(lon, lat, covariate_values):
    """
    A stem for building spatial models.
    """
    logp_mesh = combine_spatial_inputs(lon,lat)

    # =====================
    # = Create PyMC model =
    # =====================  

    inc = pm.CircVonMises('inc', 0,0)
    sqrt_ecc = pm.Uniform('sqrt_ecc',0,.95)
    ecc = pm.Lambda('ecc', lambda s=sqrt_ecc: s**2)
    amp = pm.Exponential('amp',.1,value=1.)
    scale_shift = pm.Exponential('scale_shift',1./.08,value=1./.08)
    scale = pm.Lambda('scale',lambda ss=scale_shift:ss+.01)
    diff_degree = pm.Uniform('diff_degree',.01,3)
    
    M, M_eval = trivial_means(logp_mesh)

    @pm.deterministic(trace=True)
    def C(amp=amp,scale=scale,inc=inc,ecc=ecc,diff_degree=diff_degree):
        return pm.gp.FullRankCovariance(pm.gp.cov_funs.matern.aniso_geo_rad, amp=amp, scale=scale, inc=inc, ecc=ecc, diff_degree=diff_degree)
    
    covariate_dict, C_eval = cd_and_C_eval(covariate_values, C, logp_mesh)
    
    return locals()


def basic_st_submodel(lon, lat, t, covariate_values, cpus):
    """
    A stem for building spatiotemporal models.
    """
        
    logp_mesh = combine_st_inputs(lon,lat,t)

    inc = pm.CircVonMises('inc', 0,0)
    sqrt_ecc = pm.Uniform('sqrt_ecc',0,.95)
    ecc = pm.Lambda('ecc', lambda s=sqrt_ecc: s**2)
    amp = pm.Exponential('amp',.1,value=1.)
    scale = pm.Exponential('scale',1.,value=1.)
    scale_t = pm.Exponential('scale_t',.1,value=.1)
    t_lim_corr = pm.Uniform('t_lim_corr',0,.95)

    @pm.stochastic(__class__ = pm.CircularStochastic, lo=0, hi=1)
    def sin_frac(value=.1):
        return 0.

    M, M_eval = trivial_means(logp_mesh)
        
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

    covariate_dict, C_eval = cd_and_C_eval(covariate_values, C, logp_mesh)
        
    return locals()

def sample_covariates(covariate_dict, S_eval, d):
    """
    Samples covariates back in when they have been marginalized away.
        - covariate_dict : {name : value-on-input, prior-variance}
        - M_eval : array. Probably zeros, unless you did something fancy in the mean.
        - S_eval : Cholesky decomposition of covariance of d | covariates, m
        - d : current deviation from mean of covariates' immediate child.
    """
    # Extract keys to list to preserve order.
    n = covariate_dict.keys()
    
    cvv = [covariate_dict[k] for k in n]
    x = np.vstack((np.asarray([v[0] for v in cvv])))
    prior_val = [v[1] for v in cvv]
    
    pri_S_eval = np.asarray(S_eval)
    lo = pm.gp.trisolve(S_eval, x.T, uplo='L').T
    post_tau = np.dot(lo,lo.T)
    l = np.linalg.cholesky(post_tau)

    post_C = pm.gp.trisolve(l, np.eye(l.shape[0]),uplo='L')
    post_C = pm.gp.trisolve(l.T, post_C, uplo='U')

    post_mean = np.dot(lo, pm.gp.trisolve(pri_S_eval, d, uplo='L'))
    post_mean = pm.gp.trisolve(l, post_mean, uplo='L')
    post_mean = pm.gp.trisolve(l.T, post_mean, uplo='U')

    new_val = pm.rmv_normal_cov(post_mean, post_C).squeeze()

    return dict(zip(n, new_val))

def get_d_S_eval(chain, f_label, nugget_label, i, M_eval, logp_mesh):
    """Utility fn"""
    if type(f_label) == type('str'):
        f = chain.PyMCsamples.col(f_label)[i]
    else:
        f = f_label
    d = f - M_eval

    C = chain.group0.C[i]
    if nugget_label is not None:
        nug = chain.PyMCsamples.cols.V[i]
    C_eval = C(logp_mesh, logp_mesh) + nug*np.eye(np.sum(logp_mesh.shape[:-1]))
    S_eval = np.linalg.cholesky(C_eval)
    return d, S_eval

def sample_covariates_from_chain(chain, meta, i, f_label, nugget_label=None):
    """
    Wrapper for sample_covariates.
        - chain : hdf5 group.
        - meta : hdf5 group.
        - i : integer.
        - f_label : string or array.
        - nugget_label : string
    """
    covariate_dict = meta.covariates[0]
    logp_mesh = meta.logp_mesh[:]    
    M_eval = np.zeros(logp_mesh.shape[:-1])

    d, S_eval = get_d_S_eval(chain, f_label, nugget_label, i, M_eval, logp_mesh)
    return sample_covariates(covariate_dict, S_eval, d)

def covariate_trace(chain, meta, f_label, nugget_label=None):
    """
    Produces a covariate trace from an existing hdf5 chain.
        - chain : hdf5 group
        - meta : hdf5 group
        - f_label : string or array
        - nugget_label : string
    """
    covariate_dict = meta.covariates[0]
    logp_mesh = meta.logp_mesh[:]
    M_eval = np.zeros(logp_mesh.shape[:-1])

    out = dict.fromkeys(covariate_dict)
    for k in out.keys():
        out[k] = []

    n = len(chain.PyMCsamples)
    for i in xrange(n):
        d, S_eval = get_d_S_eval(chain, f_label, nugget_label, i, M_eval, logp_mesh)
        cur_vals = sample_covariates(covariate_dict, S_eval, d)

        for k, v in cur_vals.iteritems():
            out[k].append(v)

    return dict([(k,np.array(v)) for k,v in out.iteritems()])


def predictive_mean_and_std(chain, meta, i, f_label, x_label, x, f_has_nugget=False, pred_cv_dict=None, nugget_label=None):
    """
    Computes marginal (pointwise) predictive mean and variance for f(x).
    Expects input from an hdf5 datafile.
        - chain : hdf5 group.
        - meta : hdf5 group.
        - i : integer.
        - f_label : string or array.
        - x : numpy array
        - pred_cv_dict : {name : value-on-predmesh}
        - nugget_label : string
    """
    
    if pred_cv_dict is not None:
        n = pred_cv_dict.keys()
        
        covariate_dict = meta.covariates[0]
        prior_covariate_variance = np.diag([covariate_dict[key][1] for key in n])
    
        pred_covariate_values = np.array([pred_cv_dict[key] for key in n])
        input_covariate_values = np.array([covariate_dict[key][0] for key in n])
    
    # How many times must a man condition a multivariate normal
    
    M = chain.group0.M[i]
    C = chain.group0.C[i]

    logp_mesh = getattr(meta,x_label)[:]    
    M_input = M(logp_mesh)
    M_pred = M(x)

    C_input = C(logp_mesh, logp_mesh)
    if pred_cv_dict is not None:
        C_input += np.dot(np.dot(input_covariate_values.T, prior_covariate_variance), input_covariate_values)
    if nugget_label is not None and f_has_nugget:
        nug = chain.PyMCsamples.cols.V[i]
        C_input += nug*np.eye(np.sum(logp_mesh.shape[:-1]))
    S_input = np.linalg.cholesky(C_input)
    
    C_cross = C(logp_mesh, x) 
    V_pred = C(x)
    if pred_cv_dict is not None:
        C_cross += np.dot(np.dot(input_covariate_values.T, prior_covariate_variance), pred_covariate_values)
        V_pred += np.sum(np.dot(np.sqrt(prior_covariate_variance), pred_covariate_values)**2, axis=0)
    if np.any(np.isnan(V_pred)):
        raise ValueError

    SC_cross = pm.gp.trisolve(S_input,C_cross,uplo='L')
    V_out = V_pred - np.sum(np.asarray(SC_cross)**2,axis=0)
    
    try:
        f = chain.PyMCsamples.col(f_label)[i]
    except:
        f = getattr(meta,f_label)[:]

    M_out = M_pred + np.asarray(np.dot(SC_cross.T,pm.gp.trisolve(S_input, (f-M_input), uplo='L'))).squeeze()
    
    # from IPython.Debugger import Pdb
    # Pdb(color_scheme='Linux').set_trace()   
    if np.any(np.isnan(np.sqrt(V_out))) or np.any(np.isnan(M_out)):
        raise ValueError, 'Some predictive samples were NaN. Keep all your input files and tell Anand.'
    
    return M_out, np.sqrt(V_out)        
    
                                    
class FieldStepper(pm.StepMethod):
    """
    A special Gibbs stepper that updates tau and f together give eps_p_f
    and the mean and covariance parameters. Why did I update tau and f together?
    I don't remember. Probably grasping at straws trying to improve mixing
    at some point. This doesn't save any Cholesky decompositions or covariance 
    evaluations.
    """
    # def __init__(self, f, tau, V, C_eval, M_eval, logp_mesh, eps_p_f, ti, incomp_jump=False, jump_tau = True):
    def __init__(self, f, V, C_eval, M_eval, logp_mesh, eps_p_f, ti, incomp_jump=False):    
        self.f = f
        # self.tau = tau
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

        pm.StepMethod.__init__(self,[f])

        # self.jump_tau = jump_tau
        # if self.jump_tau:
        #     pm.StepMethod.__init__(self,[f,tau])
        # else:
        #     pm.StepMethod.__init__(self,[f])
            
        self.time = 0.
        self.incomp_time = 0.
    
    def step(self):
        
        fc = pm.gp.fast_matrix_copy
        
        t1 = time.time()
    
        eps_p_f = self.eps_p_f.value
        f = self.f.value
        for i in xrange(len(self.scratch3)):
            self.scratch3[i] = np.sum(eps_p_f[self.ti[i]] - f[i])
    
        # if self.jump_tau:
        #     # tau's full conditional is Gamma.
        #     amp_alph = eps_p_f.shape[0]/2.+1.
        #     tau_alph = amp_alph + self.tau.parents['alpha']
        #     tau_vec = self.scratch3 - self.f.value
        #     tau_bet = np.dot(tau_vec, tau_vec)/2. + self.tau.parents['beta']
        #     self.tau.value = pm.rgamma(tau_alph,tau_bet)

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