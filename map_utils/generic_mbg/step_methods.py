import pymc as pm
import numpy as np
import time

class CovariateStepper(pm.StepMethod):
    """
    A step method for a dictionary of covariate coefficients.
    """
 
    def __init__(self, covariate_dict, M_eval, sig, d):
        self.M = M_eval
        self.sig = sig
        self.d = d.value
 
        cvv = covariate_dict.values()
        self.beta = pm.Container([v[0] for v in cvv])
        self.x = np.asarray([v[1] for v in cvv])
 
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
        
        # Update value of f.
        self.f.value = m_step+np.dot(sig_step,np.random.normal(size=sig_step.shape[1])).view(np.ndarray).ravel()
        
        t2 = time.time()
        self.time += t2-t1