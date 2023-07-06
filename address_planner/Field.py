import math
from .GlobalValues      import *
from .AddressLogicRoot  import *

#from uhdl import *




class Field(AddressLogicRoot):

    def __init__(self,name,bit,
        sw_access       = ExternalReadWrite ,
        hw_access       = InternalReadWrite ,
        sw_read_effect  = NoEffect  ,
        sw_write_effect = NoEffect  ,
        hw_read_effect  = NoEffect  ,
        hw_write_effect = NoEffect  ,
        hw_type         = InternalNull  ,
        init_value      = 0         ,
        description     = ''):
        super().__init__(name=name,description=description)
        self._name              = name
        self.bit                = bit
        self.sw_access          = sw_access
        self.hw_access          = hw_access
        self.sw_read_effect     = sw_read_effect
        self.sw_write_effect    = sw_write_effect
        self.hw_read_effect     = hw_read_effect
        self.hw_write_effect    = hw_write_effect
        self.hw_type            = hw_type
        self.bit_offset         = 0
        self.init_value         = init_value

    @property
    def name(self):
        return self._name

    @property
    def start_bit(self):
        return self.bit_offset

    @property
    def end_bit(self):
        return self.bit_offset + self.bit - 1

    @property
    def mask(self):
        bin_str = '0' * (self.father.bit - self.bit - self.bit_offset) + '1' * self.bit + '0' * self.bit_offset
        integer = int(bin_str,2)
        return hex(integer)



    @property
    def module_name_until_regbank(self):
        return self.father.module_name_until_regbank + '_' + self.module_name


    @property
    def sw_readable(self):
        return self.sw_access == ExternalReadOnly or self.sw_access == ExternalReadWrite

    @property
    def sw_writeable(self):
        return self.sw_access == ExternalWriteOnly or self.sw_access == ExternalReadWrite

    @property
    def hw_readable(self):
        return self.hw_access == InternalReadOnly or self.hw_access == InternalReadWrite

    @property
    def hw_writeable(self):
        return self.hw_access == InternalWriteOnly or self.hw_access == InternalReadWrite

    @property
    def sw_read_clean(self):
        return self.sw_readable and self.sw_read_effect == ReadClean
    
    @property 
    def sw_write_one_to_set(self):
        return self.sw_writeable and self.sw_write_effect == WriteOnce


    # @property
    # def global_offset(self):
    #     return 0 if self.father == None else self.father.global_offset + self.offset
# 
    # @property
    # def global_start_address(self):
    #     return self.global_offset
# 
    # @property
    # def global_end_address(self):
    #     return self.global_offset + self.size - 1
# 
    # @property
    # def start_address(self):
    #     return self.offset
# 
    # @property
    # def end_address(self):
    #     return self.offset + self.size - 1

    # @property
    # def offset(self):
    #     return math.floor(self.offset / self.father.bus_width)


class FilledField(Field):

    def __init__(self,bit):
        super().__init__(name='FilledField',bit=bit,sw_access=ExternalNull,hw_access=InternalNull)



################################################################################
# Field Type "ExternalReadOnly"
################################################################################

class FieldExternalReadOnly(Field):

    def __init__(self,name,bit,hw_access=InternalReadWrite,hw_read_effect=NoEffect,hw_write_effect=NoEffect,\
                 init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = ExternalReadOnly,
            hw_access       = hw_access,
            sw_read_effect  = NoEffect  ,
            sw_write_effect = NoEffect  ,
            hw_read_effect  = hw_read_effect  ,
            hw_write_effect = hw_write_effect  ,
            hw_type         = hw_access,
            init_value      = init_value,
            description     = description)

################################################################################
# Field Type "ExternalWriteOnly"
################################################################################

class FieldExternalWriteOnly(Field):

    def __init__(self,name,bit,hw_access=InternalReadWrite,hw_read_effect=NoEffect,hw_write_effect=NoEffect,\
                 init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = ExternalWriteOnly,
            hw_access       = hw_access,
            sw_read_effect  = NoEffect  ,
            sw_write_effect = NoEffect  ,
            hw_read_effect  = hw_read_effect  ,
            hw_write_effect = hw_write_effect  ,
            hw_type         = hw_access,
            init_value      = init_value,
            description     = description)

################################################################################
# Field Type "ExternalReadWrite"
################################################################################

class FieldExternalReadWrite(Field):

    def __init__(self,name,bit,hw_access=InternalReadWrite,hw_read_effect=NoEffect,hw_write_effect=NoEffect,\
                 init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = ExternalReadWrite,
            hw_access       = hw_access,
            sw_read_effect  = NoEffect  ,
            sw_write_effect = NoEffect  ,
            hw_read_effect  = hw_read_effect  ,
            hw_write_effect = hw_write_effect  ,
            hw_type         = hw_access,
            init_value      = init_value,
            description     = description)


