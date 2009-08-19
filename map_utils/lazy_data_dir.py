import tables as tb
import os

__all__ = ['LazyDataDirectory']

class LazyDataDirectory(object):
    """
    Exposes all the hdf5 files in a directory as attributes. Only opens them
    on-demand.
    """
    
    def __init__(self, path):
        self.path = path
        
    def __getattr__(self, name):
        if self.__dict__.has_key(name):
            return self.__dict__[name]
        else:
            hf_names = filter(lambda n: tb.isHDF5File(os.path.join(self.path, n)), os.listdir(self.path))
            for fname in hf_names:
                if name == os.path.splitext(fname)[0]:
                    hf = tb.openFile(os.path.join(self.path, name+'.hdf5')).root
                    setattr(self, name, hf)
                    return hf
            raise IOError, 'File with base %s not found in directory %s'%(name, self.path)
            
    def close(self, name):
        if self.__dict__.has_key(name):
            getattr(self,name)._v_file.close()
            delattr(self, name)
        
    def list(self):
        hf_names = filter(lambda n: tb.isHDF5File(os.path.join(self.path, n)), os.listdir(self.path))
        return [os.path.splitext(fname)[0] for fname in hf_names]