from copy               import deepcopy
from functools          import reduce
from .AddressLogicRoot  import *
from .GlobalValues      import *

import os
import builtins
import json
import shutil
import re

class AddressSpace(AddressLogicRoot):

    def __init__(self,name,size,description='',path='./'):
        super().__init__(name=name,description=description,path=path)
        self.size           = size
        self.sub_space_list = []
        self.offset         = 0
        self._next_offset   = 0
        #self.module_name    = name
        #self.module_name      = ''
        #self.name           = name
        #self.start_address  = start_address
        #self.end_address    = self.start_address + self.size - 1
        #self.description    = description
        #self.path           = path
        #self.father         = None



    @property
    def bit_offset(self):
        return self.offset*8
    
    @property
    def bit_size(self):
        return self.size*8

    @property
    def global_offset(self):
        return 0 if self.father is None else self.father.global_offset + self.bit_offset

    @property
    def global_start_address(self):
        return self.global_offset

    @property
    def global_end_address(self):
        return self.global_offset + self.bit_size - 1

    @property
    def start_address(self):
        return self.bit_offset

    @property
    def end_address(self):
        return self.bit_offset + self.bit_size - 1

    @property
    def hex_offset(self):
        hex_value = hex(self.bit_offset)
        if hex_value == '0x0':
            return '\'h0'
        else:
            return '\'h'+hex_value.lstrip('0x')



    def add(self,sub_space,offset,name):
        sub_space_copy = deepcopy(sub_space)
        sub_space_copy.offset = offset
        sub_space_copy.father = self
        sub_space_copy.module_name = name
        if not self.inclusion_detect(sub_space_copy):
            raise Exception('Sub space %s is not included in space %s' %(sub_space_copy.module_name,self.module_name))

        for exist_space in self.sub_space_list:
            if self.collision_detect(exist_space,sub_space_copy):
                raise Exception('Sub space %s(%s to %s) and current sub space %s(%s to %s) conflict.' \
                    % (sub_space_copy.module_name,hex(sub_space_copy.start_address),hex(sub_space_copy.end_address),exist_space.module_name,hex(exist_space.start_address),hex(exist_space.end_address)))
        self.sub_space_list.append(sub_space_copy)
        self._next_offset = offset + sub_space.size


    def add_incr(self,sub_space,name):
        self.add(sub_space=sub_space,offset=self._next_offset,name=name)
        


    def collision_detect(self,space_A,space_B):
        if      (space_A.start_address <= space_B.start_address ) and (space_B.start_address <= space_A.end_address ): return True
        elif    (space_A.start_address <= space_B.end_address   ) and (space_B.end_address   <= space_A.end_address ): return True
        elif    (space_B.start_address <= space_A.start_address ) and (space_A.start_address <= space_B.end_address ): return True
        elif    (space_B.start_address <= space_A.end_address   ) and (space_A.end_address   <= space_B.end_address ): return True
        else:                                                                                                return False

    def inclusion_detect(self,other):
        return True if (self.start_address <= other.start_address) and (other.end_address <= self.end_address) else False
    
    def intr_detect(self,space):
        if space.reg_type==Intr and space.bit!=IntrBitWidth.Intr.value:             return False 
        elif space.reg_type==IntrMask and space.bit!=IntrBitWidth.IntrMask.value:   return False
        else:                                                                       return True

    def search_field(self, reg_name, field_name):
        for sub_space in self.sub_space_list:
            for field in sub_space.field_list:
                if reg_name == sub_space.module_name and field_name == field.name:
                    self.lock_inclusion_detect(field)
                    return [sub_space, field]
        
        raise Exception(f'lock field {reg_name}_{field_name} not exist')
    
    def search_magic(self, reg_name):
        for sub_space in self.sub_space_list:
            if reg_name == sub_space.module_name:
                self.magic_inclusion_detect(sub_space)
                return sub_space
        raise Exception(f'magic register {reg_name} not exist')

    
    def check_list(self, other):
        if not isinstance(other, list):     raise Exception("input must be a List type")

    def lock_inclusion_detect(self, field):
        from .Field import LockField
        if not isinstance(field, LockField):
            raise Exception(f'field in lock list is not LockField Type')
        
    def magic_inclusion_detect(self, reg):
        from .Field import MagicNumber
        if not isinstance(reg.field_list[0], MagicNumber):
            raise Exception(f'field in magic list is not MagicNumber Type')
        


    #########################################################################################
    # output generate
    #########################################################################################

    # def report_html(self):
    #     text = self.report_from_template(APG_HTML_FILE_ADDR_SPACE)
    #     os.makedirs(os.path.dirname(self.html_path), exist_ok=True)
    #     with open(self.html_path,'w') as f:
    #         f.write(text)
    #     #for ss in self.sub_space_list:
    #     #    ss.report_html()


    def report_chead(self):
        chead_name_list = self.report_chead_core()
        with open(os.path.join(self._chead_dir,'all.h'),'w') as f:
            for chead_name in chead_name_list:
                f.write("#include \"%s\"\n" % chead_name)
    

    def report_chead_core(self):
        if self.sub_space_list == []:
            return []
        else:
            chead_name_list = [self.chead_name]
            text = self.report_from_template(APG_CHEAD_FILE_ADDR_SPACE,{'head_type':'c'})
            os.makedirs(os.path.dirname(self.chead_path), exist_ok=True)
            with open(self.chead_path,'w') as f:
                f.write(text)
            for ss in self.sub_space_list:
                chead_name_list += ss.report_chead_core()
            return chead_name_list


    # report v head.==============================================
    def report_vhead(self):
        vhead_name_list = self.report_vhead_core()
        with open(os.path.join(self._vhead_dir,'all.vh'),'w') as f:
            for vhead_name in vhead_name_list:
                f.write("`include \"%s\"\n" % os.path.join(self._vhead_dir, vhead_name))

        
    def report_vhead_core(self):
        if self.sub_space_list == []:
            return []
        else:
            vhead_name_list = [self.vhead_name]
            text = self.report_from_template(APG_VHEAD_FILE_ADDR_SPACE,{'head_type':'v'})
            os.makedirs(os.path.dirname(self.vhead_path), exist_ok=True)
            with open(self.vhead_path,'w') as f:
                f.write(text)
            for ss in self.sub_space_list:
                vhead_name_list += ss.report_vhead_core()
            return vhead_name_list
        

    # report and check ralf ==============================================
    def report_ralf(self):
        output_path = self._ralf_dir+'/'
        self.recursive_report_ralf_core(output_path)

    
    def recursive_report_ralf_core(self, output_dir):
        for ss in self.sub_space_list:
            if hasattr(ss,'report_ralf_core'):
                ss.report_ralf_core(output_dir)
            else:
                ss.recursive_report_ralf_core(output_dir)

    
    # report and check json ==========================================
    def report_json(self):
        json_list= [self.report_json_core()]
        jtext = json.dumps(json_list, ensure_ascii=False, indent=2)
        if not os.path.exists(self._html_dir):  os.makedirs(self._html_dir) 
        with open(self.json_path, 'w') as f:
            f.write(jtext)
        
    

    def report_json_core(self):
        json_dict={}
        json_dict["key"]        = ADD_KEY()
        json_dict["type"]       = "sys"
        json_dict["name"]       = self.module_name
        json_dict["start_addr"] = ConvertSize(self.start_address, is_byte=True)
        json_dict["end_addr"]   = ConvertSize(self.end_address+1, is_byte=True)
        json_dict["size"]       = ConvertSize(self.size, is_byte=True)
        json_dict["description"]= self.description
        json_dict["children"]   = [c.report_json_core() for c in self.sub_space_list]
        return json_dict
    

    # total ========================================
    def generate(self,path=None):
        if path != None:
            self.path = path
        self.report_json()
        self.report_ralf()
        self.report_chead()
        self.report_vhead()

    def check(self, path=None):
        if path != None:
            self.path = path
        self.check_json()
        self.check_ralf()
        self.check_chead()
        self.check_vhead()
        

    #########################################
    # tablelike support
    #########################################

    def regspace(self, name,size,description='',path='./',bus_width=APG_BUS_WIDTH,software_interface='apb', offset=0):
        from .RegSpace import RegSpace

        u_ss = RegSpace(name=name, size=size, description=description, path=path, bus_width=bus_width, software_interface=software_interface)
        u_ss.offset = offset
        u_ss.father = self 
        return u_ss
    
    def addrspace(self, sub_space, offset, name):
        self.add(sub_space, offset, name)
        return self



















    ############################
    # check
    ############################


    def check_ralf(self):
        self.recursive_check_ralf_core()


    def recursive_check_ralf_core(self):
        for ss in self.sub_space_list:
            if hasattr(ss,'report_ralf_core'):
                ss.check_ralf()
            else:
                ss.recursive_check_ralf_core()


    def check_vhead(self):
        check_dir = os.path.join(self._vhead_dir, 'vcs_check')
        file_path = os.path.join(self._vhead_dir, 'all.vh')
        os.makedirs(check_dir, exist_ok=True)
        
        print("\n################################################################################")
        print("[Check vhead] Check vhead: %s"% file_path)
        print("################################################################################\n")
        
        command_vhead = f'vcs -full64 -sverilog -cpp g++-4.8 -cc gcc-4.8 -LDFLAGS -Wl,--no-as-needed +lint=PCWM -debug_access+all -o {check_dir}/simv -Mdir={check_dir}/csrc {file_path} | tee {check_dir}/vcs.log'
        os.system(command_vhead)
        # with open(f'{check_dir}/vcs.log','r') as f:
        #     if not re.search(r'simv\sup\sto\sdate', f.readlines()[-1]): 
        #         raise Exception("vhead check error occur, log path:%s"% os.path.abspath(f'{check_dir}/vcs.log'))
        if not os.path.exists(f'{check_dir}/simv'):
            raise Exception("vhead check error occur, log path:%s"% os.path.abspath(f'{check_dir}/vcs.log'))
        print("[Check vhead] vhead check output log: %s"% os.path.abspath(f'{check_dir}/vcs.log'))
    

    def check_json(self):
        json_path = os.path.join(self._html_dir, 'data.json')
        try:
            print("\n################################################################################")
            print("[Check Json] Check Json: %s"% json_path)
            print("################################################################################\n")
            json_file = open(json_path, 'r')
            json.load(json_file)

            print("[Check Json] json file correct")
        except:
            raise Exception("[Check Json] Error in Json file")
        
    
    def check_chead(self):
        file_path = os.path.join(self._chead_dir,'all.h')
        print("\n################################################################################")
        print("[Check chead] Check chead: %s"% file_path)
        print("################################################################################\n")
        
        if os.system('gcc -include stdint.h %s' % file_path) !=0:
            raise Exception('c head compile error.')
        print("[Check chead]  c head correct")