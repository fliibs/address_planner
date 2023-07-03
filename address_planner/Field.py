import math
from .GlobalValues      import *
from .AddressLogicRoot  import *

from uhdl import *




class Field(AddressLogicRoot):

    def __init__(self,name,bit,
        sw_access       = ReadWrite ,
        hw_access       = ReadWrite ,
        sw_read_effect  = NoEffect  ,
        sw_write_effect = NoEffect  ,
        hw_type         = Unknown   ,
        init_value      = 0         ,
        description     = ''):
        super().__init__(name=name,description=description)
        self._name              = name
        self.bit                = bit
        self.sw_access          = sw_access
        self.hw_access          = hw_access
        self.sw_read_effect     = sw_read_effect
        self.sw_write_effect    = sw_write_effect
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
        return self.sw_access == ReadOnly or self.sw_access == ReadWrite

    @property
    def sw_writeable(self):
        return self.sw_access == WriteOnly or self.sw_access == ReadWrite

    @property
    def hw_readable(self):
        return self.hw_access == ReadOnly or self.hw_access == ReadWrite

    @property
    def hw_writeable(self):
        return self.hw_access == WriteOnly or self.hw_access == ReadWrite




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
        super().__init__(name='FilledField',bit=bit,sw_access=Null,hw_access=Null)



################################################################################
# Field Type "ExternalReadOnly"
################################################################################

FieldHardwareType.ExternalReadOnly = 'External Read Only'
ADD_TO_GLOBAL_VALUES(ExternalReadOnly=FieldHardwareType.ExternalReadOnly)

class FieldExternalReadOnly(Field):

    def __init__(self,name,bit,init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = ReadOnly,
            sw_read_effect  = NoEffect,
            sw_write_effect = NoEffect,
            hw_type         = FieldHardwareType.ExternalReadOnly,
            init_value      = init_value,
            description     = description)

################################################################################
# Field Type "ExternalWriteOnly"
################################################################################

FieldHardwareType.ExternalWriteOnly = 'External Write Only'
ADD_TO_GLOBAL_VALUES(ExternalWriteOnly=FieldHardwareType.ExternalWriteOnly)

class FieldExternalWriteOnly(Field):

    def __init__(self,name,bit,init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = WriteOnly,
            sw_read_effect  = NoEffect,
            sw_write_effect = NoEffect,
            hw_type         = FieldHardwareType.ExternalWriteOnly, 
            init_value      = init_value,
            description     = description)

################################################################################
# Field Type "ExternalReadWrite"
################################################################################

FieldHardwareType.ExternalReadWrite = 'External Read Write'
ADD_TO_GLOBAL_VALUES(ExternalReadWrite=FieldHardwareType.ExternalReadWrite)

class FieldExternalReadWrite(Field):

    def __init__(self,name,bit,init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = ReadWrite,
            sw_read_effect  = NoEffect,
            sw_write_effect = NoEffect,
            hw_type         = FieldHardwareType.ExternalReadWrite,
            init_value      = init_value,
            description     = description)

################################################################################
# Field Type "InternalReadOnly"
################################################################################

FieldHardwareType.InternalReadOnly = 'Internal Read Only'
ADD_TO_GLOBAL_VALUES(InternalReadOnly=FieldHardwareType.InternalReadOnly)

class FieldReadOnly(Field):

    def __init__(self,name,bit,init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = ReadOnly,
            sw_read_effect  = NoEffect,
            sw_write_effect = NoEffect,
            hw_type         = FieldHardwareType.InternalReadOnly,
            init_value      = init_value,
            description     = description)

################################################################################
# Field Type "InternalWriteOnly"
################################################################################

FieldHardwareType.InternalWriteOnly = 'Internal Write Only'
ADD_TO_GLOBAL_VALUES(InternalWriteOnly=FieldHardwareType.InternalReadOnly)

class FieldWriteOnly(Field):

    def __init__(self,name,bit,init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = WriteOnly,
            sw_read_effect  = NoEffect,
            sw_write_effect = NoEffect,
            hw_type         = FieldHardwareType.InternalWriteOnly,
            init_value      = init_value,
            description     = description)

################################################################################
# Field Type "InternalReadWrite"
################################################################################

FieldHardwareType.InternalReadWrite = 'Internal Read Write'
ADD_TO_GLOBAL_VALUES(InternalReadWrite=FieldHardwareType.InternalReadWrite)

class FieldReadWrite(Field):

    def __init__(self,name,bit,init_value=0,description=''):
        super().__init__(name=name,bit=bit,
            sw_access       = ReadWrite,
            sw_read_effect  = NoEffect,
            sw_write_effect = NoEffect,
            hw_type         = FieldHardwareType.InternalReadWrite,
            init_value      = init_value,
            description     = description)
