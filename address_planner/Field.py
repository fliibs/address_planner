import math

from address_planner.GlobalValues import ReadWrite
from .GlobalValues      import *
from .AddressLogicRoot  import *



class Field(AddressLogicRoot):
    def __init__(self, name, bit, 
                 sw_access          = ReadWrite,
                 hw_access          = ReadWrite,
                 init_value         = 0,
                 description=''):
        super().__init__(name=name, description=description)
        
        self._name              = name
        self.bit                = bit
        self.sw_access          = sw_access
        self.hw_access          = hw_access
        self.is_external        = False
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
        return self.sw_access == ReadOnly or \
               self.sw_access == ReadWrite or \
               self.sw_access == ReadClean

    @property
    def sw_writeable(self):
        return self.sw_access == WriteOnly or \
               self.sw_access == ReadWrite

    @property
    def hw_readable(self):
        return self.hw_access == ReadOnly or \
               self.hw_access == ReadWrite

    @property
    def hw_writeable(self):
        return self.hw_access == WriteOnly or \
               self.hw_access == ReadWrite

    @property
    def sw_read_clean(self):
        return self.sw_access == ReadClean
    
    @property
    def sw_write_clean(self):
        pass

    @property 
    def sw_write_one_to_set(self):
        pass

    
    @property
    def hw_read_clean(self):
        return False


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
        super().__init__(name='FilledField',bit=bit,
                         sw_access     = Null, 
                         hw_access     = Null
                         )

class ExternalField(Field):
    def __init__(self, name, bit, sw_access=ReadWrite, hw_access=ReadWrite, init_value=0, description=''):
        super().__init__(name, bit, sw_access, hw_access, init_value, description)
        self.is_external = True