from .GlobalValues  import *
from .RegSpace      import RegSpace
from .Field         import *
import math

class Register(RegSpace):

    def __init__(self,name,bit=32, description='',bus_width=APG_BUS_WIDTH,reg_type=Normal,lock_list=[]):
        size = math.ceil(bit/bus_width)
        super().__init__(name=name, size=size, description=description, path='./', bus_width=bus_width)
        self.bit            = bit
        self._next_offset   = 0
        self.field_list     = []
        self.reg_type       = reg_type
        self.lock_list      = lock_list
        self.magic_list     = []

    def add(self,field,offset=0,name=None, lock_list=[]):
        field.bit_offset    = offset
        field.father        = self
        field.inst_name     = field.module_name if name == None else name

        self.check_list(lock_list)
        for member in lock_list:
            if member not in field.lock_list:
                field.lock_list.append(member)
            
        if not self.inclusion_detect(field):
            raise Exception('Field inclusion detect')

        for exist_field in self.field_list:
            if self.collision_detect(exist_field,field):
                raise Exception('Field collision detect')
        self.field_list.append(field)

        self._next_offset = offset + field.bit


    def add_incr(self,field,name=None,lock_list=[]):
        self.add(field=field,offset=self._next_offset,name=name,lock_list=lock_list)


    def add_magic(self, name='field_magic', bit=32, password=0, init_value=0, description='', lock_list=[]):
        self.add(field=MagicNumber(name=name,bit=bit,password=password,init_value=init_value, description=description), lock_list=lock_list)


    def add_lock_list(self, lock_list):
        lock_list_copy = self.lock_list.copy()
        if lock_list not in lock_list_copy:
            lock_list_copy.append(lock_list)
        self.lock_list = lock_list_copy
    
    def add_magic_list(self, register):
        magic_list_copy = self.magic_list.copy()
        if register not in magic_list_copy:
            magic_list_copy.append(register)
        self.magic_list = magic_list_copy


    def collision_detect(self, field_A, field_B):
        if      (field_A.start_bit <= field_B.start_bit ) and (field_B.start_bit <= field_A.end_bit ): return True
        elif    (field_A.start_bit <= field_B.end_bit   ) and (field_B.end_bit   <= field_A.end_bit ): return True
        elif    (field_B.start_bit <= field_A.start_bit ) and (field_A.start_bit <= field_B.end_bit ): return True
        elif    (field_B.start_bit <= field_A.end_bit   ) and (field_A.end_bit   <= field_B.end_bit ): return True
        else:                                                                                          return False

    def inclusion_detect(self, other):
        return True if (self.start_bit <= other.start_bit) and (other.end_bit <= self.end_bit) else False
    
    def magic_self_detect(self):
        pass

    @property
    def start_bit(self):
        return 0

    @property
    def end_bit(self):
        return self.bit - 1

    @property
    def start_address(self):
        return self.offset
    
    @property
    def end_address(self):
        return self.start_address + self.end_bit

    @property
    def module_name_until_regbank(self):
        return self.father.module_name + '_' + self.module_name
    
    @property
    def sorted_field_list(self):
        return sorted(self.field_list, key=lambda x: x.bit_offset)

    @property
    def filled_field_list(self):
        res = []
        previous_field = None
        # sorted_field_list = sorted(self.field_list, key=lambda x: x.bit_offset)

        if self.sorted_field_list[0].bit_offset != 0:
            filled_field = FilledField(bit=self.sorted_field_list[0].bit_offset)
            res.append(filled_field)

        for field in self.sorted_field_list:
            if previous_field != None and field.start_bit > previous_field.end_bit + 1:
                filled_field = FilledField(bit=field.start_bit - previous_field.end_bit - 1)
                filled_field.bit_offset = previous_field.end_bit + 1

                res.append(filled_field)
            res.append(field)
            previous_field = field
        
        if self.sorted_field_list[-1].end_bit < 31:
            filled_field = FilledField(32 - previous_field.end_bit - 1)
            filled_field.bit_offset = previous_field.end_bit + 1
            res.append(filled_field)

        return res
    
    @property
    def bit_offset(self):
        return self.offset

    @property
    def hex_offset(self):
        hex_value = hex(int(self.reg_offset/8))
        if hex_value == '0x0':
            return '%d\'h0'%(self.bit)
        else:
            return '\'h'+hex_value.lstrip('0x')

    @property
    def reg_offset(self):
        if self.start_address < self.father.offset:
            return self.start_address
        else:
            return self.start_address - self.father.offset
        
    @property
    def get_magic_list(self):
        reg_space = self.father
        real_magic_list = [reg_space.search_magic(magic) for magic in self.magic_list]

        return real_magic_list
    
    @property
    def init_value(self):
        bin_str = 0
        for field in self.filled_field_list:
            bin_str += 2**(field.bit_offset)*field.init_value
        return bin_str


    #########################################################################################
    # output generate
    #
    #  For Reg, there is no need to generate a separate file. report_X is called recursively, 
    #  so all of Reg's related functions need to be modified to empty functions.
    #########################################################################################

    #def report_html(self):
    #    return []

    def report_chead_core(self):
        return []

    def report_vhead_core(self):
        return []
    
    def report_vhead_global_core(self, file):
        pass

    def report_chead_global_core(self, file):
        pass
    
    def add_field(self, name, bit, sw_access=ReadWrite, hw_access=ReadWrite, init_value=0, description=''):
        self.add_incr(Field(name, bit, sw_access, hw_access, init_value, description))
        return self
    
    def field(self, name, bit, sw_access=ReadWrite, hw_access=ReadWrite, init_value=0, description='', offset=0):
        self.add(Field(name, bit, sw_access, hw_access, init_value, description), offset=offset)
        return self

    def reserved_field(self, bit):
        self.add(FilledField(bit))
        return self
    
    def external_field(self, name, bit, sw_access=ReadWrite, hw_access=ReadWrite, init_value=0, description='', offset=0):
        self.add(ExternalField(name, bit, sw_access, hw_access, init_value, description), offset=offset)
        return self
    
    @property
    def end(self):
        self.father.add(self, int((self.father.bit_offset+self.offset)/8), self.module_name)
        return self.father
    
    def report_json_core(self):
        json_dict = {}
        json_dict["key"]        = ADD_KEY()
        json_dict["type"]       = "reg"
        json_dict["name"]       = self.module_name 
        if self.start_address <= self.father.bit_offset:
            json_dict["start_addr"] = hex(int(self.start_address+self.father.start_address/8))
            json_dict["end_addr"]   = hex(int(self.end_address+self.father.end_address/8))
        else:
            json_dict["start_addr"] = hex(int(self.start_address))
            json_dict["end_addr"]   = hex(int(self.end_address))
        
        json_dict["size"]       = ConvertSize(self.bit)
        json_dict["description"]= self.description
        json_dict["fields"]     = [c.report_json_core() for c in self.sorted_field_list if c.report_json_core() is not Null]
        return json_dict


class InterruptRegister(Register):
    def __init__(self, name, description='',bus_width=APG_BUS_WIDTH,reg_type=Intr, lock_list=[]):
        if reg_type==Intr:       bit_ = IntrBitWidth.IntrFull.value
        elif reg_type==IntrMask: bit_ = IntrBitWidth.IntrFull.value
        else:                    raise Exception()
        super().__init__(name,bit_,description,bus_width,reg_type,lock_list)

    def add_intr_field(self, name, bit, init_value=0, enable_init_value=0, mask_init_value=0, description='', offset=0):
        self.add(field=IntrStatusField(name=name,bit=bit,init_value=init_value,description=description),offset=offset)
        self.add(field=IntrField(name=name,bit=bit,init_value=init_value,description=description),offset=offset+32)
        self.add(field=IntrEnableField(name=f'{name}',bit=bit,init_value=enable_init_value,description=description),offset=offset+64)
        self.add(field=IntrClearField(name=f'{name}',bit=bit,description=description),offset=offset+96)
        self.add(field=IntrSetField(name=f'{name}',bit=bit,description=description),offset=offset+128)
        if self.reg_type==IntrMask:
            self.add(field=IntrMaskField(name=f'{name}',bit=bit,init_value=mask_init_value,description=description),offset=offset+160)

