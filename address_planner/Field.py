import math

# from address_planner.GlobalValues import ReadWrite
from .GlobalValues      import *
from .AddressLogicRoot  import *

class FieldRoot(AddressLogicRoot):
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
        self.lock_list          = []


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
    def hex_value(self):
        hex_value = hex(self.init_value)
        if hex_value == '0x0':
            return '%d\'h0'%(self.bit)
        else:
            return '%d\'h'%(self.bit)+hex_value.lstrip('0x')

    @property
    def module_name_until_regbank(self):
        return self.father.module_name_until_regbank + '_' + self.module_name
    
    @property
    def get_lock_list(self):
        lock_list = self.lock_list.copy()
        for lock in self.father.lock_list:
            if lock not in self.lock_list:
                lock_list.append(lock)

        if lock_list == []: return []

        reg_space = self.father.father
        real_lock_list = [reg_space.search_field(lock.split('.')[0], lock.split('.')[1]) for lock in lock_list]
        return real_lock_list


    def detect_pulse(self):
        if (self.sw_access==Write1Pulse or self.sw_access==Write0Pulse) and self.hw_access!=ReadOnly:
            raise Exception("detect write pulse field: %s, but hardware access should be readonly"% self._name)
        if (self.sw_access==Write1Pulse or self.sw_access==Write0Pulse) and self.is_external==True:
            raise Exception("detect write pulse field: %s, but it must be internal field"% self._name)
        if self.hw_access==Write1Pulse or self.hw_access==Write0Pulse:
            raise Exception("detect pulse on hardware access of field: %s, hardware has no pulse type"% self._name)
        
    def lock_self_detect(self):
        pass


    ############## Software Type ###############
    @property
    def sw_readable(self):
        return self.sw_access == ReadOnly or \
               self.sw_access == ReadWrite or \
               self.sw_access == ReadClean or \
               self.sw_access == WriteReadClean or \
               self.sw_access == ReadSet or \
               self.sw_access == WriteReadSet or \
               self.sw_access == WriteClean or \
               self.sw_access == WriteCleanReadSet or \
               self.sw_access == Write1Clean or \
               self.sw_access == Write1CleanReadSet or \
               self.sw_access == Write0Clean or \
               self.sw_access == Write0CleanReadSet or \
               self.sw_access == WriteSet or \
               self.sw_access == WriteSetReadClean or \
               self.sw_access == Write1Set or \
               self.sw_access == Write1SetReadClean or \
               self.sw_access == Write0Set or \
               self.sw_access == Write0SetReadClean or \
               self.sw_access == Write1Toggle or \
               self.sw_access == Write0Toggle or \
               self.sw_access == WriteOnce
               

    @property
    def sw_writeable(self):
        return self.sw_access == WriteOnly or \
               self.sw_access == WriteOnlyClean or \
               self.sw_access == WriteOnlySet or \
               self.sw_access == ReadWrite or \
               self.sw_access == WriteReadClean or \
               self.sw_access == WriteReadSet or \
               self.sw_access == WriteClean or \
               self.sw_access == WriteCleanReadSet or \
               self.sw_access == Write1Clean or \
               self.sw_access == Write1CleanReadSet or \
               self.sw_access == Write0Clean or \
               self.sw_access == Write0CleanReadSet or \
               self.sw_access == WriteSet or \
               self.sw_access == WriteSetReadClean or \
               self.sw_access == Write1Set or \
               self.sw_access == Write1SetReadClean or \
               self.sw_access == Write0Set or \
               self.sw_access == Write0SetReadClean or \
               self.sw_access == Write1Toggle or \
               self.sw_access == Write0Toggle or \
               self.sw_access == WriteOnce or \
               self.sw_access == WriteOnlyOnce or \
               self.sw_access == Write1Pulse or \
               self.sw_access == Write0Pulse

    @property
    def sw_read_clean(self):
        return self.sw_access == ReadClean or \
               self.sw_access == WriteReadClean or \
               self.sw_access == WriteSetReadClean or \
               self.sw_access == Write1SetReadClean or \
               self.sw_access == Write0SetReadClean
    @property
    def sw_read_set(self):
        return self.sw_access == ReadSet or \
               self.sw_access == WriteReadSet or \
               self.sw_access == WriteCleanReadSet or \
               self.sw_access == Write1CleanReadSet or \
               self.sw_access == Write0CleanReadSet
    
    @property
    def sw_write_clean(self):
        return self.sw_access == WriteClean or \
               self.sw_access == WriteOnlyClean or \
               self.sw_access == WriteCleanReadSet

    @property 
    def sw_write_one_to_clean(self):
        return self.sw_access == Write1Clean or \
               self.sw_access == Write1CleanReadSet
    
    @property
    def sw_write_zero_to_clean(self):
        return self.sw_access == Write0Clean or \
               self.sw_access == Write0CleanReadSet

    @property 
    def sw_write_set(self):
        return self.sw_access == WriteSet or \
               self.sw_access == WriteOnlySet or \
               self.sw_access == WriteSetReadClean 
               

    @property 
    def sw_write_one_to_set(self):
        return self.sw_access == Write1Set or \
               self.sw_access == Write1SetReadClean

    @property 
    def sw_write_zero_to_set(self):
        return self.sw_access == Write0Set or \
               self.sw_access == Write0SetReadClean
    
    @property
    def sw_write_one_to_toggle(self):
        return self.sw_access == Write1Toggle
    
    @property
    def sw_write_zero_to_toggle(self):
        return self.sw_access == Write0Toggle
    
    @property
    def sw_write_once(self):
        return self.sw_access == WriteOnce or \
               self.sw_access == WriteOnlyOnce
    
    @property
    def sw_write_one_pulse(self):
        return self.sw_access == Write1Pulse
    
    @property
    def sw_write_zero_pulse(self):
        return self.sw_access == Write0Pulse


    ############## Hardware Type ##############
    @property
    def hw_readable(self):
        return self.hw_access == ReadOnly or \
               self.hw_access == ReadWrite or \
               self.hw_access == ReadClean or \
               self.hw_access == WriteReadClean or \
               self.hw_access == ReadSet or \
               self.hw_access == WriteReadSet or \
               self.hw_access == WriteClean or \
               self.hw_access == WriteCleanReadSet or \
               self.hw_access == Write1Clean or \
               self.hw_access == Write1CleanReadSet or \
               self.hw_access == Write0Clean or \
               self.hw_access == Write0CleanReadSet or \
               self.hw_access == WriteSet or \
               self.hw_access == WriteSetReadClean or \
               self.hw_access == Write1Set or \
               self.hw_access == Write1SetReadClean or \
               self.hw_access == Write0Set or \
               self.hw_access == Write0SetReadClean or \
               self.hw_access == Write1Toggle or \
               self.hw_access == Write0Toggle or \
               self.hw_access == WriteOnce

    @property
    def hw_writeable(self):
        return self.hw_access == WriteOnly or \
               self.hw_access == WriteOnlyClean or \
               self.hw_access == WriteOnlySet or \
               self.hw_access == ReadWrite or \
               self.hw_access == WriteReadClean or \
               self.hw_access == WriteReadSet or \
               self.hw_access == WriteClean or \
               self.hw_access == WriteCleanReadSet or \
               self.hw_access == Write1Clean or \
               self.hw_access == Write1CleanReadSet or \
               self.hw_access == Write0Clean or \
               self.hw_access == Write0CleanReadSet or \
               self.hw_access == WriteSet or \
               self.hw_access == WriteSetReadClean or \
               self.hw_access == Write1Set or \
               self.hw_access == Write1SetReadClean or \
               self.hw_access == Write0Set or \
               self.hw_access == Write0SetReadClean or \
               self.hw_access == Write1Toggle or \
               self.hw_access == Write0Toggle or \
               self.hw_access == WriteOnce or \
               self.hw_access == WriteOnlyOnce

    @property
    def hw_read_clean(self):
        return self.hw_access == ReadClean or \
               self.hw_access == WriteReadClean or \
               self.hw_access == WriteSetReadClean or \
               self.hw_access == Write1SetReadClean or \
               self.hw_access == Write0SetReadClean
    @property
    def hw_read_set(self):
        return self.hw_access == ReadSet or \
               self.hw_access == WriteReadSet or \
               self.hw_access == WriteCleanReadSet or \
               self.hw_access == Write1CleanReadSet or \
               self.hw_access == Write0CleanReadSet
    
    @property
    def hw_write_clean(self):
        return self.hw_access == WriteClean or \
               self.hw_access == WriteOnlyClean or \
               self.hw_access == WriteCleanReadSet

    @property 
    def hw_write_one_to_clean(self):
        return self.hw_access == Write1Clean or \
               self.hw_access == Write1CleanReadSet
    
    @property
    def hw_write_zero_to_clean(self):
        return self.hw_access == Write0Clean or \
               self.hw_access == Write0CleanReadSet

    @property 
    def hw_write_set(self):
        return self.hw_access == WriteSet or \
               self.hw_access == WriteOnlySet or \
               self.hw_access == WriteSetReadClean 
               

    @property 
    def hw_write_one_to_set(self):
        return self.hw_access == Write1Set or \
               self.hw_access == Write1SetReadClean

    @property 
    def hw_write_zero_to_set(self):
        return self.hw_access == Write0Set or \
               self.hw_access == Write0SetReadClean
    
    @property
    def hw_write_one_to_toggle(self):
        return self.hw_access == Write1Toggle
    
    @property
    def hw_write_zero_to_toggle(self):
        return self.hw_access == Write0Toggle
    
    @property
    def hw_write_once(self):
        return self.hw_access == WriteOnce or \
               self.hw_access == WriteOnlyOnce


    ############## Hardware Type ##############

    @property
    def reserved(self):
        return self.hw_access == Null and \
               self.sw_access == Null

    @property
    def field_reg_read(self):
        return  self.hw_readable or \
                self.sw_readable
    
    @property
    def field_reg_write(self):
        return  self.hw_writeable or \
                self.sw_writeable or \
                self.hw_read_clean or \
                self.hw_read_set or \
                self.sw_read_clean or \
                self.sw_read_set










    def report_json_core(self):
        if isinstance(self, FilledField):
            return Null
        field_dict = {}
        field_dict["key"]               = ADD_KEY()
        field_dict["name"]              = self._name 
        field_dict["size"]              = "%d bit"% self.bit
        field_dict["Position"]          = "[%d:%d]"% (self.end_bit, self.start_bit)
        field_dict["External"]          = "%s" % self.is_external
        field_dict["Software Access"]   = self.sw_access.name
        field_dict["Hardware Access"]   = self.hw_access.name
        field_dict["description"]       = self.description
        return field_dict 



class FilledField(FieldRoot):

    def __init__(self,bit):
        super().__init__(name='FilledField',bit=bit,
                         sw_access     = Null, 
                         hw_access     = Null
                         )

class Field(FieldRoot):
    def __init__(self, name, bit, sw_access=ReadWrite, hw_access=ReadWrite, init_value=0, description=''):
        super().__init__(name, bit, sw_access, hw_access, init_value, description)
        self.is_external = False
        self.detect_pulse()


class ExternalField(FieldRoot):
    def __init__(self, name, bit, sw_access=ReadWrite, hw_access=ReadWrite, init_value=0, description=''):
        super().__init__(name, bit, sw_access, hw_access, init_value, description)
        self.is_external = True
        self.detect_pulse()


class W1PField(Field):
    def __init__(self, name, bit, init_value=0, description=''):
        super().__init__(name, bit, Write1Pulse, ReadOnly, init_value, description)


class W0PField(Field):
    def __init__(self, name, bit, init_value=0, description=''):
        super().__init__(name, bit, Write0Pulse, ReadOnly, init_value, description)


class LockField(Field):
    def __init__(self, name, bit=1, description=''):
        super().__init__(name, bit, WriteSet, Null, 0, description)


class MagicNumber(Field):
    def __init__(self, name='field_magic', bit=32, password=0, init_value=0, description=''):
        super().__init__(name, bit, ReadWrite, Null, init_value, description)
        self.password = password


class IntrField(Field):
    def __init__(self, name, bit, init_value=0, description=''):
        super().__init__(name, bit, ReadOnly, ReadWrite, init_value, f'{name} interrupt status field {description}')

class IntrEnableField(Field):
    def __init__(self, name, bit, init_value=0, description=''):
        super().__init__(name, bit, ReadWrite, Null, init_value, f'{name} interrupt enable field {description}')

class IntrMaskField(Field):
    def __init__(self, name, bit, init_value=0, description=''):
        super().__init__(name, bit, ReadWrite, Null, init_value, f'{name} interrupt mask field {description}')

class IntrClearField(FieldRoot):
    def __init__(self, name, bit, init_value=0, description=''):
        super().__init__(name, bit, Write1Pulse, Null, init_value, f'{name} interrupt clear field {description}')
        self.is_external = False

class IntrSetField(FieldRoot):
    def __init__(self, name, bit, init_value=0, description=''):
        super().__init__(name, bit, Write1Pulse, Null, init_value, f'{name} interrupt Set field {description}')
        self.is_external = False
 