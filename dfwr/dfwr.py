from bmi.wrapper import BMIWrapper
from bmi.api import IBmi


class DFWR(IBmi):

    def __init__(self, configfile=''):
        
        self.configfile = configfile

        # load dflow
        self.dflow = BMIWrapper(self.configfile)

        # load dwaves
        self.dwaves = BMIWrapper(self.configfile) # TODO: we might need to use a different configfile here, but be aware that the __init__ method can only take one parameter!

        
    def __enter__(self):
        self.initialize()
        return self
    
    
    def __exit__(self, errtype, errobj, traceback):
        self.finalize()
        if errobj:
            raise errobj
        
        
    def get_current_time(self):
        return self.dflow.get_current_time()
    
    
    def get_start_time(self):
        return self.dflow.get_start_time()
    
    
    def get_end_time(self):
        return self.dflow.get_end_time()
    
    
    def get_var(self, var):
        
        if var in []: # TODO: fill this list with appropriate variable names
            pass # TODO: do something with communication file
        else:
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

        if var in []: # TODO: fill this list with appropriate variable names
            pass # TODO: do something with communication file
        else:
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

            
    def update(self, dt=-1):

        # update dflow
        self.dflow.update(dt)

        # update dwaves
        self.dwaves.update(dt) # TODO: maybe we need some timestep differentiation here?

        
    def finalize(self):

        # finalize dflow
        self.dflow.finalize()

        # finalize dwaves
        self.dwaves.finalize()
        
