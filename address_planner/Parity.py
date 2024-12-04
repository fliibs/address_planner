from .uhdl.uhdl import *
from .GlobalValues import *

class ParityFieldRoot(object):
    def __init__(self, reg_name, field_name, is_external):
        self.reg_name   = reg_name
        self.field_name = field_name 
        self.is_external = is_external

    @property
    def full_field_name(self):
        if self.is_external:
            return f'{self.reg_name}_{self.field_name}_parity_field'
        else: # internal field
            return f'{self.reg_name}_{self.field_name}'
        
    @property
    def field_name_until_reg(self):
        return f'{self.reg_name}_{self.field_name}'
    
    def get_field_data(self, module):
        if hasattr(module, self.full_field_name):
            return getattr(module, self.full_field_name) 
        elif hasattr(module, f'{self.field_name_until_reg}_rdat'):
            return getattr(module, f'{self.field_name_until_reg}_rdat') 
        else:
            return UInt(1,0)
    
    def get_wdata(self, module):
        raise Exception('software/hardware access is not writeable.')
    
    def get_renable(self, module):
        return None

    def get_wenable(self, module):
        return None

    def get_wmux(self, module, sig_name='', sig=None):
        if not hasattr(module, f'{sig_name}_parity'):
            res_sig  = module.set(f'{sig_name}_parity', Wire(UInt(getattr(module, self.full_field_name).attribute.width)))
            sig_mux  = EmptyWhen()
            sig_val  = getattr(module, self.wsig_name) if sig==None else sig
            sig_mux.when(self.get_wenable(module)).then(sig_val).otherwise(self.get_field_data(module))
            res_sig += sig_mux
            return res_sig
        else:
            return getattr(module, f'{sig_name}_parity')
        

    def get_rmux(self, module, sig_name='', sig=None):
        if not hasattr(module, f'{sig_name}_parity'):
            res_sig  = module.set(f'{sig_name}_parity', Wire(UInt(getattr(module, self.full_field_name).attribute.width)))
            sig_mux  = EmptyWhen()
            sig_val  = getattr(module, self.rsig_name) if sig==None else sig
            sig_mux.when(self.get_renable(module)).then(sig_val).otherwise(self.get_field_data(module))
            res_sig += sig_mux
            return res_sig
        else:
            return getattr(module, f'{sig_name}_parity')


class ParityField(ParityFieldRoot):
    def __init__(self, reg_name, field_name, is_external=False, index=0, offset=0, init_value=0):
        super().__init__(reg_name, field_name, is_external)
        self.index = index
        self.offset = offset
        self.init_value = init_value

    def set_type(self, sw_type=Null, hw_type=Null):
        # for sw
        if      hw_type in [Write1Pulse,Write0Pulse]:  self.sw = ParitySwWritePulse(self.reg_name, self.field_name)
        elif    sw_type == Null:                self.sw = ParitySwNull(self.reg_name, self.field_name, self.init_value)
        elif    sw_type == ReadWrite:           self.sw = ParitySwWrite(self.reg_name, self.field_name)
        elif    sw_type == ReadOnly:            self.sw = ParitySwReadOnly(self.reg_name, self.field_name)
        elif    sw_type == ReadClean:           self.sw = ParitySwReadClean(self.reg_name, self.field_name)
        elif    sw_type == ReadSet:             self.sw = ParitySwReadSet(self.reg_name, self.field_name)
        elif    sw_type == WriteReadClean:      self.sw = ParitySwWriteReadClean(self.reg_name, self.field_name)
        elif    sw_type == WriteReadSet:        self.sw = ParitySwWriteReadSet(self.reg_name, self.field_name)
        elif    sw_type == WriteOnly:           self.sw = ParitySwWrite(self.reg_name, self.field_name)
        elif    sw_type == WriteOnlyClean:      self.sw = ParitySwWriteClean(self.reg_name, self.field_name)
        elif    sw_type == WriteOnlySet:        self.sw = ParitySwWriteSet(self.reg_name, self.field_name)
        elif    sw_type == WriteClean:          self.sw = ParitySwWriteClean(self.reg_name, self.field_name)
        elif    sw_type == WriteSet:            self.sw = ParitySwWriteSet(self.reg_name, self.field_name)
        elif    sw_type == WriteSetReadClean:   self.sw = ParitySwWriteSetReadClean(self.reg_name, self.field_name)
        elif    sw_type == WriteCleanReadSet:   self.sw = ParitySwWriteCleanReadSet(self.reg_name, self.field_name)
        elif    sw_type == Write1Clean:         self.sw = ParitySwWrite1Clean(self.reg_name, self.field_name)
        elif    sw_type == Write1CleanReadSet:  self.sw = ParitySwWrite1CleanReadSet(self.reg_name, self.field_name)
        elif    sw_type == Write0Clean:         self.sw = ParitySwWrite0Clean(self.reg_name, self.field_name)
        elif    sw_type == Write0CleanReadSet:  self.sw = ParitySwWrite0CleanReadSet(self.reg_name, self.field_name)
        elif    sw_type == Write1Set:           self.sw = ParitySwWrite1Set(self.reg_name, self.field_name)
        elif    sw_type == Write1SetReadClean:  self.sw = ParitySwWrite1SetReadClean(self.reg_name, self.field_name)
        elif    sw_type == Write0Set:           self.sw = ParitySwWrite0Set(self.reg_name, self.field_name)
        elif    sw_type == Write0SetReadClean:  self.sw = ParitySwWrite0SetReadClean(self.reg_name, self.field_name)
        elif    sw_type == Write0Toggle:        self.sw = ParitySwWrite0Toggle(self.reg_name, self.field_name)
        elif    sw_type == Write1Toggle:        self.sw = ParitySwWrite1Toggle(self.reg_name, self.field_name)
        elif    sw_type == WriteOnce:           self.sw = ParitySwWriteOnce(self.reg_name, self.field_name)
        elif    sw_type == WriteOnlyOnce:       self.sw = ParitySwWriteOnce(self.reg_name, self.field_name)
        elif    sw_type == Write1Pulse:         self.sw = ParitySwWritePulse(self.reg_name, self.field_name)
        elif    sw_type == Write0Pulse:         self.sw = ParitySwWritePulse(self.reg_name, self.field_name)
        else:   raise Exception(f'not support software type: {sw_type}.')
        # for hw
        if      sw_type in [Write1Pulse,Write0Pulse]:  self.hw = ParityHwWritePulse(self.reg_name, self.field_name)
        elif    hw_type == Null:                self.hw = ParityHwNull(self.reg_name, self.field_name, self.init_value)
        elif    hw_type == ReadWrite:           self.hw = ParityHwWrite(self.reg_name, self.field_name)
        elif    hw_type == ReadOnly:            self.hw = ParityHwReadOnly(self.reg_name, self.field_name)
        elif    hw_type == ReadClean:           self.hw = ParityHwReadClean(self.reg_name, self.field_name)
        elif    hw_type == ReadSet:             self.hw = ParityHwReadSet(self.reg_name, self.field_name)
        elif    hw_type == WriteReadClean:      self.hw = ParityHwWriteReadClean(self.reg_name, self.field_name)
        elif    hw_type == WriteReadSet:        self.hw = ParityHwWriteReadSet(self.reg_name, self.field_name)
        elif    hw_type == WriteOnly:           self.hw = ParityHwWrite(self.reg_name, self.field_name)
        elif    hw_type == WriteOnlyClean:      self.hw = ParityHwWriteClean(self.reg_name, self.field_name)
        elif    hw_type == WriteOnlySet:        self.hw = ParityHwWriteSet(self.reg_name, self.field_name)
        elif    hw_type == WriteClean:          self.hw = ParityHwWriteClean(self.reg_name, self.field_name)
        elif    hw_type == WriteSet:            self.hw = ParityHwWriteSet(self.reg_name, self.field_name)
        elif    hw_type == WriteSetReadClean:   self.hw = ParityHwWriteSetReadClean(self.reg_name, self.field_name)
        elif    hw_type == WriteCleanReadSet:   self.hw = ParityHwWriteCleanReadSet(self.reg_name, self.field_name)
        elif    hw_type == Write1Clean:         self.hw = ParityHwWrite1Clean(self.reg_name, self.field_name)
        elif    hw_type == Write1CleanReadSet:  self.hw = ParityHwWrite1CleanReadSet(self.reg_name, self.field_name)
        elif    hw_type == Write0Clean:         self.hw = ParityHwWrite0Clean(self.reg_name, self.field_name)
        elif    hw_type == Write0CleanReadSet:  self.hw = ParityHwWrite0CleanReadSet(self.reg_name, self.field_name)
        elif    hw_type == Write1Set:           self.hw = ParityHwWrite1Set(self.reg_name, self.field_name)
        elif    hw_type == Write1SetReadClean:  self.hw = ParityHwWrite1SetReadClean(self.reg_name, self.field_name)
        elif    hw_type == Write0Set:           self.hw = ParityHwWrite0Set(self.reg_name, self.field_name)
        elif    hw_type == Write0SetReadClean:  self.hw = ParityHwWrite0SetReadClean(self.reg_name, self.field_name)
        elif    hw_type == Write0Toggle:        self.hw = ParityHwWrite0Toggle(self.reg_name, self.field_name)
        elif    hw_type == Write1Toggle:        self.hw = ParityHwWrite1Toggle(self.reg_name, self.field_name)
        elif    hw_type == WriteOnce:           self.hw = ParityHwWriteOnce(self.reg_name, self.field_name)
        elif    hw_type == WriteOnlyOnce:       self.hw = ParityHwWriteOnce(self.reg_name, self.field_name)
        elif    hw_type == Write1Pulse:         self.hw = ParityHwWritePulse(self.reg_name, self.field_name)
        elif    hw_type == Write0Pulse:         self.hw = ParityHwWritePulse(self.reg_name, self.field_name)
        else:   raise Exception(f'not support hardware type: {hw_type}.')

        self.sw.is_external = self.is_external
        self.hw.is_external = self.is_external


    def get_hw_wena_wdata(self, module):
        if not isinstance(self.hw.get_wena_wdata(module), UInt):
            return self.hw.get_wena_wdata(module)[self.index]
        else:
            return self.hw.get_wena_wdata(module)

    def get_hw_rena_wdata(self, module):
        if not isinstance(self.hw.get_rena_wdata(module), UInt):
            return self.hw.get_rena_wdata(module)[self.index]
        else:
            return self.hw.get_rena_wdata(module)
    
    def get_sw_wena_wdata(self, module):
        if not isinstance(self.sw.get_wena_wdata(module), UInt):
            return self.sw.get_wena_wdata(module)[self.index]
        else:
            return self.sw.get_wena_wdata(module)

    def get_sw_rena_wdata(self, module):
        if not isinstance(self.sw.get_rena_wdata(module), UInt):
            return self.sw.get_rena_wdata(module)[self.index]
        else:
            return self.sw.get_rena_wdata(module)


class ParitySwFieldRoot(ParityFieldRoot):
    def __init__(self, reg_name, field_name, sel_read, sel_write):
        super().__init__(reg_name, field_name, False)
        self.sel_read  = sel_read
        self.sel_write = sel_write

    @property
    def wsig_name(self):
        if self.is_external:
            return f'{self.field_name_until_reg}_parity_sw_wdat'
        else: # internal field
            return f'{self.field_name_until_reg}_field_wdat'
    
    @property
    def rsig_name(self):
        if self.is_external:
            return f'{self.field_name_until_reg}_parity_sw_rdat' # no use but get name
        else:
            return f'{self.field_name_until_reg}_field_rdat'

    @property
    def rsig_ena_name(self):
        if self.is_external:
            return f'{self.field_name_until_reg}_parity_sw_rena'
        else:
            return f'{self.reg_name}_rvld'
    
    @property
    def wsig_ena_name(self):
        if self.is_external:
            return f'{self.field_name_until_reg}_parity_sw_wena'
        else:
            return f'{self.field_name_until_reg}_sw_wren'

    def get_renable(self, module):
        if self.sel_read:
            return getattr(module, self.rsig_ena_name)
        else:
            return None

    def get_wenable(self, module):
        if self.sel_write:
            return getattr(module, self.wsig_ena_name)
        else:
            return None

    def get_wena_wdata(self, module):
        return self.get_field_data(module)

    def get_rena_wdata(self, module):
        return self.get_field_data(module)
    

class ParityHwFieldRoot(ParityFieldRoot):
    def __init__(self, reg_name, field_name, sel_read, sel_write):
        super().__init__(reg_name, field_name, False)
        self.sel_read  = sel_read
        self.sel_write = sel_write

    @property
    def wsig_name(self):
        if self.is_external:
            return f'{self.field_name_until_reg}_parity_hw_wdat'
        else: # internal field
            return f'{self.field_name_until_reg}_wdat'
    
    @property
    def rsig_name(self):
        if self.is_external:
            return f'{self.field_name_until_reg}_parity_hw_rdat' # no use but get name
        else: # internal field
            return f'{self.field_name_until_reg}_rdat'
    
    @property
    def rsig_ena_name(self):
        if self.is_external:
            return f'{self.field_name_until_reg}_parity_hw_rena'
        else: # internal field
            return f'{self.field_name_until_reg}_rena'
    
    @property
    def wsig_ena_name(self):
        if self.is_external:
            return f'{self.field_name_until_reg}_parity_hw_wena'
        else: # internal field
            return f'{self.field_name_until_reg}_wena'

    def get_renable(self, module):
        if self.sel_read:
            return getattr(module, self.rsig_ena_name)
        else:
            return None

    def get_wenable(self, module):
        if self.sel_write:
            return getattr(module, self.wsig_ena_name)
        else:
            return None

    def get_wena_wdata(self, module):
        return self.get_field_data(module)
    
    def get_rena_wdata(self, module):
        return self.get_field_data(module)
    

###############################################################
# reserve field
###############################################################
class ParitySwNull(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name, init_value=0):
        super().__init__(reg_name, field_name, False, False)
        self.init_value = init_value 

    def get_wena_wdata(self, module):
        return UInt(1,self.init_value) 
    
    def get_rena_wdata(self, module):
        return UInt(1,self.init_value) 

class ParityHwNull(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name, init_value=0):
        super().__init__(reg_name, field_name, False, False)
        self.init_value = init_value 

    def get_wena_wdata(self, module):
        return UInt(1,self.init_value) 
    
    def get_rena_wdata(self, module):
        return UInt(1,self.init_value) 

###############################################################
# readwrite/writeonly
###############################################################
class ParitySwWrite(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        return self.get_wmux(module, self.wsig_name)


class ParityHwWrite(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        return self.get_wmux(module, self.wsig_name)
    
###############################################################
# readonly
###############################################################
class ParitySwReadOnly(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, False)

    
class ParityHwReadOnly(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, False)

###############################################################
# read clean
###############################################################
class ParitySwReadClean(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, False)

    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width,0))

class ParityHwReadClean(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, False)

    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width,0))

###############################################################
# read set
###############################################################
class ParitySwReadSet(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, False)

    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width,2**width - 1))

class ParityHwReadSet(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, False)

    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width,2**width - 1))

###############################################################
# write read set
###############################################################
class ParitySwWriteReadSet(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        return self.get_wmux(module, self.wsig_name)

    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width,2**width - 1))

class ParityHwWriteReadSet(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        return self.get_wmux(module, self.wsig_name)

    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width,2**width - 1))

###############################################################
# write read clean
###############################################################
class ParitySwWriteReadClean(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        return self.get_wmux(module, self.wsig_name)

    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width,0))

class ParityHwWriteReadClean(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        return self.get_wmux(module, self.wsig_name)

    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width,0))

###############################################################
# writeonly clean / write clean
###############################################################
class ParitySwWriteClean(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.wsig_name, UInt(width,0))

class ParityHwWriteClean(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.wsig_name, UInt(width,0))

###############################################################
# writeonly set / write set
###############################################################
class ParitySwWriteSet(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.wsig_name, UInt(width, 2**width-1))

class ParityHwWriteSet(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.wsig_name, UInt(width, 2**width-1))

###############################################################
# write set read clean
###############################################################
class ParitySwWriteSetReadClean(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.wsig_name, UInt(width, 2**width-1))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 0))

class ParityHwWriteSetReadClean(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.wsig_name, UInt(width, 2**width-1))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 0))

###############################################################
# write clean read set
###############################################################
class ParitySwWriteCleanReadSet(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.wsig_name, UInt(width, 0))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 2**width-1))

class ParityHwWriteCleanReadSet(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.wsig_name, UInt(width, 0))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 2**width-1))


###############################################################
# write 1 clean
###############################################################
class ParitySwWrite1Clean(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitAnd(Inverse(sig_wdat), sig_field))

class ParityHwWrite1Clean(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitAnd(Inverse(sig_wdat), sig_field))

###############################################################
# write 1 clean read set
###############################################################
class ParitySwWrite1CleanReadSet(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitAnd(Inverse(sig_wdat), sig_field))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 2**width-1))

class ParityHwWrite1CleanReadSet(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitAnd(Inverse(sig_wdat), sig_field))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 2**width-1))

###############################################################
# write 0 clean
###############################################################
class ParitySwWrite0Clean(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitAnd(sig_wdat, sig_field))

class ParityHwWrite0Clean(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitAnd(sig_wdat, sig_field))

###############################################################
# write 0 clean read set
###############################################################
class ParitySwWrite0CleanReadSet(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitAnd(sig_wdat, sig_field))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.rsig_name, UInt(width, 2**width-1))

class ParityHwWrite0CleanReadSet(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitAnd(sig_wdat, sig_field))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_wmux(module, self.rsig_name, UInt(width, 2**width-1))

###############################################################
# write 1 set
###############################################################
class ParitySwWrite1Set(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitOr(sig_wdat, sig_field))

class ParityHwWrite1Set(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitOr(sig_wdat, sig_field))
    
###############################################################
# write 1 set read clean
###############################################################
class ParitySwWrite1SetReadClean(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitOr(sig_wdat, sig_field))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 0))

class ParityHwWrite1SetReadClean(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitOr(sig_wdat, sig_field))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 0))

###############################################################
# write 0 set
###############################################################
class ParitySwWrite0Set(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitOr(Inverse(sig_wdat), sig_field))

class ParityHwWrite0Set(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitOr(Inverse(sig_wdat), sig_field))

###############################################################
# write 0 set read clean
###############################################################
class ParitySwWrite0SetReadClean(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitOr(Inverse(sig_wdat), sig_field))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 0))

class ParityHwWrite0SetReadClean(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, True, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitOr(Inverse(sig_wdat), sig_field))
    
    def get_rena_wdata(self, module):
        width    = getattr(module, self.full_field_name).attribute.width
        return self.get_rmux(module, self.rsig_name, UInt(width, 0))

###############################################################
# write 1 toggle
###############################################################
class ParitySwWrite1Toggle(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitXor(sig_wdat, sig_field))
    
class ParityHwWrite1Toggle(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitXor(sig_wdat, sig_field))
    

###############################################################
# write 0 toggle
###############################################################
class ParitySwWrite0Toggle(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitXnor(sig_wdat, sig_field))
    
class ParityHwWrite0Toggle(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        sig_wdat  = getattr(module, self.wsig_name)
        sig_field = self.get_field_data(module)
        return self.get_wmux(module, self.wsig_name, BitXnor(sig_wdat, sig_field))


###############################################################
# write once/ write once only
###############################################################
class ParitySwWriteOnce(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        return self.get_wmux(module, self.wsig_name)
    
    def get_wenable(self, module):
        if self.is_external:
            return super().get_wenable(module)
        else:
            flag_name = f'{self.field_name_until_reg}_sw_flag'
            return BitAnd(getattr(module, self.wsig_ena_name), Inverse(getattr(module, flag_name)))
    
class ParityHwWriteOnce(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, True)

    def get_wena_wdata(self, module):
        return self.get_wmux(module, self.wsig_name)

    def get_wenable(self, module):
        if self.is_external:
            return super().get_wenable(module)
        else:
            flag_name = f'{self.field_name_until_reg}_hw_flag'
            return BitAnd(getattr(module, self.wsig_ena_name), Inverse(getattr(module, flag_name)))
     

###############################################################
# write once/ write once only
###############################################################
class ParitySwWritePulse(ParitySwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, False)

    def get_field_data(self, module):
        return UInt(1,0)

    
class ParityHwWritePulse(ParityHwFieldRoot):
    def __init__(self, reg_name, field_name):
        super().__init__(reg_name, field_name, False, False)

    def get_field_data(self, module):
        return UInt(1,0)

  
