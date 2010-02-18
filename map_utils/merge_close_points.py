import numpy as np
import pymc as pm

__all__ = ['merge_close_points']

def merge_close_points(data_mesh,disttol,ttol):
    "data_mesh should have columns lon, lat, t"
    t = data_mesh[:,2]

    # Find near spatiotemporal duplicates.
    ui = []
    fi = []
    ti = []
    dx = np.empty(1)
    for i in xrange(len(data_mesh)):
        match=False
        for j in xrange(len(ui)):
            pm.gp.euclidean(dx, data_mesh[i,:2].reshape((1,2)), data_mesh[ui[j],:2].reshape((1,2)))
            dt = abs(t[ui[j]]-t[i])
            
            if dx[0]<disttol and dt<ttol:
                match=True
                fi.append(j)
                ti[j].append(i)
                break

        if not match:
            fi.append(len(ui))            
            ui.append(i)
            ti.append([i])
    ui=np.array(ui)
    ti = [np.array(tii) for tii in ti]
    fi = np.array(fi)
    
    # Number of unique points is len(ui)   
    # ui = 'unique indices'. data_mesh[ui] is uniquified
    # fi = 'from indices'. Element i, if a repeat, is set to element fi[i]
    # ti = 'to indices'. data_mesh[ui][ti] is full-length, but has repeats replaced
    
    print 'full set had '+str(len(t))+' points, collapsed set has '+str(len(ui))
    
    return ui, fi, ti
