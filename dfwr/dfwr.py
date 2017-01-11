import os
import json
import xarray
from glob import glob
from bmi.wrapper import BMIWrapper
from bmi.api import IBmi


class DFWR(IBmi):

    def __init__(self, configfile=''):
        
        self.configfile = configfile

        # read json file
        if os.path.exists(self.configfile):
            with open(self.configfile, 'r') as fp:
                self.cfg = json.load(fp)
        else:
            raise IOError('File not found: %s', self.configfile)

        # set run directories
        self.flow_dir = self.cfg['flow_dir']
        self.wave_dir = self.cfg['wave_dir']

        # set exe directories
        waveexedir = os.path.join(self.cfg['D3D_HOME'], self.cfg['ARCH'], r'wave\bin')
        swanexedir = os.path.join(self.cfg['D3D_HOME'], self.cfg['ARCH'], r'swan\bin')
        swanbatdir = os.path.join(self.cfg['D3D_HOME'], self.cfg['ARCH'], r'swan\scripts')
        esmfexedir = os.path.join(self.cfg['D3D_HOME'], self.cfg['ARCH'], r'esmf\bin')
        esmfbatdir = os.path.join(self.cfg['D3D_HOME'], self.cfg['ARCH'], r'esmf\scripts')

        # store path list
        pathlist = []
        for name in [self.cfg['exe_dir'], waveexedir, swanexedir, swanbatdir, esmfexedir, esmfbatdir]:
            pathlist.append(name)
        
        for path in pathlist:
            BMIWrapper.known_paths.append(path)

        # set environment variables
        os.environ['ARCH'] = self.cfg['ARCH']
        os.environ['D3D_HOME'] = self.cfg['D3D_HOME']
        os.environ['swanexedir'] = swanexedir
        os.environ['swanbatdir'] = swanbatdir
        os.environ['PATH'] += os.pathsep + os.pathsep.join(pathlist)

        # load dflow
        os.chdir(self.flow_dir)
        self.dflow = BMIWrapper(engine="dflowfm", configfile=os.path.join(self.cfg['flow_dir'],
                                                                          self.cfg['mdu_file']))

        # load dwaves
        os.chdir(self.wave_dir)
        self.dwaves = BMIWrapper(engine="wave", configfile=os.path.join(self.cfg['wave_dir'],
                                                                        self.cfg['mdw_file']))
        
        
    def __enter__(self):
        self.initialize()
        return self
    
    
    def __exit__(self, errtype, errobj, traceback):
        self.finalize()
        if errobj:
            raise errobj
        
        
    def get_current_time(self):
        return self.dflow.get_current_time()

    
    def get_time_step(self):
        return self.dflow.get_time_step()

    
    def get_start_time(self):
        return self.dflow.get_start_time()
    
    
    def get_end_time(self):
        return self.dflow.get_end_time()
    
    
    def get_var(self, var):
        return self.dflow.get_var(var)
    
    
    def get_var_name(self, i):
        raise NotImplemented(
            'BMI extended function "get_var_name" is not implemented yet')
    
    
    def get_var_count(self, var):
        return self.dflow.get_var_count(var)
    

    def get_var_rank(self, var):
        return self.dflow.get_var_rank(var)
    
    
    def get_var_shape(self, var):
        return self.dflow.get_var_shape(var)

    
    def get_var_type(self, var):
        return self.dflow.get_var_type(var)
    
    
    def inq_compound(self, var):
        raise NotImplemented(
            'BMI extended function "inq_compound" is not implemented yet')
    
    
    def inq_compound_field(self, var, field):
        raise NotImplemented(
            'BMI extended function "inq_compound_field" is not implemented yet')

    
    def set_var(self, var, val):
        # TODO: 
        # there is now a difference between the dflow variable and the dwaves 
        # Dflow is correctly updated for the next timestep, but the updating of
        # the dwaves variable is only after dflow writes to the com-file. 
        # Only the bed level is updated immediately in the com-file and is 
        # correctly set in dwaves.
        # To fix this the updating of the com-file should be done manually for 
        # all variables used by dwaves.
        
        if var in self.cfg['com_structure'].keys():
            com_var = self.cfg['com_structure'][var]
            self._update_com_file(com_var, val)
        
        self.dflow.set_var(var, val)
    
        
    def set_var_index(self, var, idx):
        raise NotImplemented(
            'BMI extended function "get_var_index" is not implemented yet')
        
    
    def set_var_slice(self, var, slc):
        raise NotImplemented(
            'BMI extended function "get_var_slice" is not implemented yet')

    
    def initialize(self):
        # initialize dflow
        os.chdir(self.flow_dir)
        self.dflow.initialize()

        # initialize dwaves
        os.chdir(self.wave_dir)
        self.dwaves.initialize()
        
        # find _com.nc file
        os.chdir(self.flow_dir)
        output_DF = os.path.join(self.flow_dir, r'DFM_OUTPUT_{}'.format(os.path.splitext(self.cfg['mdu_file'])[0]))
        com_nc_locater = os.path.join(output_DF, r'*_com.nc') # Original 

        com_nc = glob(com_nc_locater)
        self.com_file = com_nc[0]
        
    def update(self, dt=1200):
        # for starters: use the exchange interval between dflow and 
        # dwaves as dt. E.g. 1200 seconds
        # com_file is the location of the communication file
        
        # update dwaves
        os.chdir(self.wave_dir)   
        if self.dflow.get_current_time() == 0.:
            self.dwaves.update(0)
            self.dflow.update(self.dflow.get_current_time()) # might be unnecessary
        else:
            self.dwaves.update(dt)
                       
        # update dflow
        os.chdir(self.flow_dir)
        self.dflow.update(dt)
        
        # get dflow bed level to set in com-file, update bed level in com-file
        for vf, vc in self.cfg['com_structure'].iteritems():
            val = self.dflow.get_var(vf)
            self._update_com_file(vc, val)
        
        
    def finalize(self):

        # finalize dflow
        self.dflow.finalize()

        # finalize dwaves
        self.dwaves.finalize()
        

    def _update_com_file(self, var, val):
        '''update the bed in the com-file with `val`'''

        # com_var can start with "-" to negate value
        if var.startswith('-'):
            var = var[1:]
            val = -val
        
        fname = self.com_file
        
        with xarray.open_dataset(fname) as ds:
            data = ds.copy(deep=True)
            # Problem encountered: variable 'windyu' has an attribute called 'coordinates'
            # This is problematic because the "coordinates" (eg x and y)  cannot be serialized anymore
            # ugly solution: remove this attribute only
            # Fairly better solution: remove all attributes called 'coordinates'
            # Best solution (but I don't know how): do not create this attribute in the first place
        for var_name in data.variables.keys():
            data[var_name].attrs.pop('coordinates',None)    
        data[var].values = val
        data.to_netcdf(fname,mode='w',format="NETCDF3_CLASSIC")  #    <---- BUG, SHOULD BE FIXED. ASK RUFUS; He says it works for him.


            
