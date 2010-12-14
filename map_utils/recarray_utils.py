from csv import reader
from numpy import where, rec, arange

__all__ = ['add_field', 'filter_recarray', 'combine_by_field']

def add_field(A, field, array):
    if not len(array)==len(A):
        raise ValueError, 'Length of new field is not same as length of old array.'
    names = A.dtype.names + (field,)
    recs = []
    for i in xrange(len(A)):
        recs.append(list(A[i]) + [array[i]])
    return rec.fromrecords(recs, names=names)

def filter_recarray(A, field, values):
    good_indices = []
    
    for i in xrange(len(A)):
        if A[field][i] in values:
            good_indices.append(i)

    return A[good_indices]
    
    
def combine_by_field(A1, A2, fields):
    if not len(A1) == len(A2):
        print 'combine_by_field: Warning, arrays aren\'t same length.'
        
    # Find names that are unique and those that are shared.
    A1_names = set(A1.dtype.names)
    A2_names = set(A2.dtype.names)
    both_names = A1_names & A2_names
    A1_names -= both_names
    A2_names -= both_names

    names = list(A1_names | A2_names | both_names)
    A1_names = list(A1_names)
    A2_names = list(A2_names)
    both_names = list(both_names)
    
    # Iterate over records.
    out_recs = []
    for i1 in xrange(len(A1)):
        
        # Find all the records in A2 that match all the records in A1 at fields.
        out_recs.append([])
        val1 = []
        i2_remaining = arange(len(A2))
        for field in fields:
            i2_remaining = i2_remaining[where(A2[field][i2_remaining]==A1[i1][field])[0]]
        
        # Check for no matches or multiple matches and warn verbally if there are any.
        if len(i2_remaining)>1:
            print 'Warning, match underspecified ', i1,i2_remaining, len(i2_remaining)
        elif len(i2_remaining)==0:
            print 'Warning, no match ',i1
            
        # Take one of the records in A2 that matches (if any) and fuse it to the current
        # record in A1.            
        try:
            i2 = i2_remaining[0]
            
            for name in A1_names + both_names:
                out_recs[i1].append(A1[i1][name])
            for name in A2_names:
                out_recs[i1].append(A2[i2][name])
                
        except:
            pass
    A = rec.fromrecords(out_recs, names=A1_names + both_names + A2_names)
    return A