from .GlobalValues  import *
from .RegSpace      import RegSpace
import math

class Register(RegSpace):

    def __init__(self,name,bit=32,description='',bus_width=APG_BUS_WIDTH):
        size = math.ceil(bit/bus_width)
        super().__init__(name=name, size=size, description=description, path='./', bus_width=bus_width)
        self.bit            = bit
        self._next_offset   = 0
        self.field_list     = []

    def add(self,field,offset,name=None):
        field.bit_offset    = offset
        field.father    = self
        field.inst_name = field.module_name if name == None else name
        
        if not self.inclusion_detect(field):
            raise Exception()

        for exist_field in self.field_list:
            if self.collision_detect(exist_field,field):
                raise Exception()
        self.field_list.append(field)

        self._next_offset = offset + field.bit


    def add_incr(self,field,name=None):
        self.add(field=field,offset=self._next_offset,name=name)


    def collision_detect(self, field_A, field_B):
        if      (field_A.start_bit <= field_B.start_bit ) and (field_B.start_bit <= field_A.end_bit ): return True
        elif    (field_A.start_bit <= field_B.end_bit   ) and (field_B.end_bit   <= field_A.end_bit ): return True
        elif    (field_B.start_bit <= field_A.start_bit ) and (field_A.start_bit <= field_B.end_bit ): return True
        elif    (field_B.start_bit <= field_A.end_bit   ) and (field_A.end_bit   <= field_B.end_bit ): return True
        else:                                                                                          return False

    def inclusion_detect(self, other):
        return True if (self.start_bit <= other.start_bit) and (other.end_bit <= self.end_bit) else False


    @property
    def start_bit(self):
        return 0

    @property
    def end_bit(self):
        return self.bit - 1


    #########################################################################################
    # output generate
    #
    #  For Reg, there is no need to generate a separate file. report_X is called recursively, 
    #  so all of Reg's related functions need to be modified to empty functions.
    #########################################################################################

    def report_html(self):
        return []

    def report_chead_core(self):
        return []

    def report_vhead_core(self):
        return []