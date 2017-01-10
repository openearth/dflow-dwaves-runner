from bmi.wrapper import BMIWrapper
from bmi.api import IBmi
import xarray
import os
from glob import glob

class DFWR(IBmi):

    def __init__(self, configfile=''):
        
        self.configfile = configfile

        # TODO: make configfile 
            # Needed from configfile:
            # ARCH, D3D_HOME, dflowfmexedir, 
            # flow_dir, mdu, 
            # wave_dir, mdw
            
        ARCH=  r'win64'
        D3D_HOME= r'C:\vanArjen-Dflow_setup\fm_versions\3Nov'
        dflowfmexedir= r'c:\fm_versions\dflowfm-lib-x64-1.1.192.48947\dflowfm-lib-x64-1.1.192.48947'
        flow_dir = r'c:\Users\velhorst\Desktop\PythonScripts\BMI\models\SandEngine\DF'
        wave_dir = r'c:\Users\velhorst\Desktop\PythonScripts\BMI\models\SandEngine\WV'
        mdu = r'c:\Users\velhorst\Desktop\PythonScripts\BMI\models\SandEngine\DF\zm_dfm_used.mdu'
        mdw = r'c:\Users\velhorst\Desktop\PythonScripts\BMI\models\SandEngine\WV\zm_dfm_used.mdw'
        self.flow_dir = flow_dir
        self.wave_dir = wave_dir
        
        #==============================================================================
        # Set paths and environmental parameters
        #==============================================================================
        waveexedir=os.path.join(D3D_HOME,ARCH,r'wave\bin')
        swanexedir=os.path.join(D3D_HOME,ARCH,r'swan\bin')
        swanbatdir=os.path.join(D3D_HOME,ARCH,r'swan\scripts')
        esmfexedir=os.path.join(D3D_HOME,ARCH,r'esmf\bin')
        esmfbatdir=os.path.join(D3D_HOME,ARCH,r'esmf\scripts')
        
        pathlist = []
        for name in [dflowfmexedir,waveexedir,swanexedir,swanbatdir,esmfexedir,esmfbatdir]:
            pathlist.append(name)
        
        # append the paths to the bmiwrapper
        for path in pathlist:
            BMIWrapper.known_paths.append(path)
        
#        # store original environmental parameters, to be able to replace them back at the end of the script
#        original_ARCH = os.environ['ARCH']
#        original_D3D_HOME = os.environ['D3D_HOME']
#        original_PATH = os.environ['PATH']
        
        # Set environmental parameters    
        os.environ['ARCH'] = ARCH
        os.environ['D3D_HOME'] = D3D_HOME
        os.environ['swanexedir'] = swanexedir
        os.environ['swanbatdir'] = swanbatdir
        os.environ['PATH'] += os.pathsep + os.pathsep.join(pathlist)

        #load dflow
        os.chdir(self.flow_dir)
        self.dflow = BMIWrapper(engine="dflowfm", configfile=mdu)

        #load dwaves
        os.chdir(self.wave_dir)
        self.dwaves = BMIWrapper(engine="wave", configfile=mdw)
        
        
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
        
        if var in ['bl']: # DONE: fill this list with appropriate variable names
#            # DONE: do something with communication file
            com_var = ['FlowElem_zcc']
            com_file_update(com_var,-val)# minus because of different definition
        
        self.dflow.set_var(var, val)
    
        
    def set_var_index(self, var, idx):
        raise NotImplemented(
            'BMI extended function "get_var_index" is not implemented yet')
        
    
    def set_var_slice(self, var, slc):
        raise NotImplemented(
            'BMI extended function "get_var_slice" is not implemented yet')

    
    def initialize(self):

        # initialize dflow
        self.dflow.initialize()

        # initialize dwaves
        self.dwaves.initialize()
        
        # find _com.nc file
        output_DF = os.path.join(self.flow_dir,r'DFM_OUTPUT_{}'.format(os.path.split(mdu)[1][:-4]))
        com_nc_locater = os.path.join(output_DF.replace(' ',''),r'*_com.nc')# quick fix with replace (something because of an extra space)
        com_nc = glob(com_nc_locater)
        self.com_file = com_nc[0]
        
    def update(self, dt=-1):
        # for starters: use the exchange interval between dflow and 
        # dwaves as dt. E.g. 1200 seconds
        # com_file is the location of the communication file
        
        # update dwaves
        os.chdir(self.wave_dir)   
        if self.dflow.get_current_time() ==0.:
            self.dwaves.update(0)
            self.dflow.update(self.dflow.get_current_time()) # might be unnecessary
        else:
            self.dwaves.update(dt) # TODO: maybe we need some timestep differentiation here?
        # ANSWER: not necessarily. But to be sure the dflow user timestep could be used for dflow
                       
        # update dflow
        os.chdir(self.flow_dir)   
        self.dflow.update(dt)

        # get dflow bed level to set in com-file
        bl_dflow = self.dflow.get_var('bl')
        
        # update bed level in com-file
        com_file_update('FlowElem_zcc',-bl_dflow) # minus because of different definition
        
        
        
    def com_file_update(self, var, val):
#        update the bed in the com-file with 'val'
        
        fname = self.com_file
        with xarray.open_dataset(fname) as ds:
            data = ds.copy(deep=True)
        # Problem encountered: variable 'windyu' has a attribute called 'coordinates'
        # This is problematic because the "coordinates" (eg x and y)  cannot be serialized anymore
        # ugly solution: remove this attribute only
        # Fairly better solution: remove all attributes called 'coordinates'
        # Best solution (but I don't know how): do not create this attribute in the first place
            for var_name in data.variables.keys():
                data[var_name].attrs.pop('coordinates',None)    
            data[var].values = val 
            data.to_netcdf(fname,format="NETCDF3_CLASSIC")
    
    def finalize(self):

        # finalize dflow
        self.dflow.finalize()

        # finalize dwaves
        self.dwaves.finalize()
        
