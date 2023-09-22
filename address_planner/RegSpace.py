import json
from .GlobalValues  import *
from .AddressSpace  import AddressSpace
from copy               import deepcopy
from .RegSpaceRTL import *
from subprocess import Popen


class RegSpace(AddressSpace):

    def __init__(self,name,size,description='',path='./',bus_width=APG_BUS_WIDTH,software_interface='apb'):
        super().__init__(name=name,size=size,description=description,path=path)
        self.bus_width = bus_width
        #self._name_prefix = 'reg'
        self.software_interface = software_interface
        self.rtl_path = ''

    def __str__(self) -> str:
        return self.module_name

    def add(self,sub_space,offset,name):
        bit_offset = offset*8
        sub_space_copy = deepcopy(sub_space)
        
        sub_space_copy.offset = bit_offset
        sub_space_copy.father = self
        sub_space_copy.module_name = name
        if not self.inclusion_detect(sub_space_copy):
            raise Exception('Sub space %s is not included in space %s' %(sub_space_copy.module_name,self.module_name))

        for exist_space in self.sub_space_list:
            if self.collision_detect(exist_space,sub_space_copy):
                raise Exception('Sub space %s(%s to %s) and current sub space %s(%s to %s) conflict.' \
                    % (sub_space_copy.module_name,hex(sub_space_copy.start_address),hex(sub_space_copy.end_address),exist_space.module_name,hex(exist_space.start_address),hex(exist_space.end_address)))
        self.sub_space_list.append(sub_space_copy)
        
        self._next_offset = bit_offset + sub_space.bit
    

    def add_incr(self,sub_space,name):
        self.add(sub_space=sub_space,offset=int(self._next_offset/8),name=name)




    #########################################################################################
    # output generate
    #########################################################################################

    # def report_html(self):
    #     text = self.report_from_template(APG_HTML_FILE_REG_SPACE)
    #     os.makedirs(os.path.dirname(self.html_path), exist_ok=True)
    #     with open(self.html_path,'w') as f:
    #         f.write(text)
    #     for ss in self.sub_space_list:
    #         ss.report_html()

    def report_chead_core(self):
        chead_name_list = [self.chead_name]
        text = self.report_from_template(APG_CHEAD_FILE_REG_SPACE)
        os.makedirs(os.path.dirname(self.chead_path), exist_ok=True)
        with open(self.chead_path,'w') as f:
            f.write(text)
        for ss in self.sub_space_list:
            chead_name_list += ss.report_chead_core()
        return chead_name_list

    def report_vhead_core(self):
        vhead_name_list = [self.vhead_name]
        text = self.report_from_template(APG_VHEAD_FILE_REG_SPACE)
        os.makedirs(os.path.dirname(self.vhead_path), exist_ok=True)
        with open(self.vhead_path,'w') as f:
            f.write(text)
        for ss in self.sub_space_list:
            vhead_name_list += ss.report_vhead_core()
        return vhead_name_list

    # report and check ralf ==============================================
    def report_ralf(self):
        output_path = self._ralf_dir+'/'
        self.report_ralf_core(output_path)
        

    def check_ralf(self):
        output_file = self._ralf_dir+'/'+self.module_name+'.ralf'
        output_path = self._ral_model_dir+'/'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print("[Check Ralf] Check ralf file: %s"% output_file)
        command = f'ralgen -full64 -uvm -t {self.module_name} {output_file}'
        os.system(command)

        if os.path.exists(f'ral_{self.module_name}.sv'): os.system(f'mv ral_{self.module_name}.sv {output_path}')
        else: raise Exception("ralgen fail!")


    def report_ralf_core(self, output_dir):
        if self.sub_space_list == []:
            return []
        else:
            file_name = self.module_name+'.ralf'
            path = output_dir
            os.makedirs(os.path.dirname(path), exist_ok=True)
            text = self.report_from_template(APG_REG_RALF_FILE_REG_SPACE, {'head_type':'ralf'})
            with open(path+file_name,'w') as f:
                f.write(text)
            

    
    # report and check rtl ==============================================
    def report_rtl(self):
        component = RegSpaceRTL(self).u
        component.output_dir = self._rtl_dir
        self.rtl_path = os.path.join(component.output_path)
        component.generate_verilog(iteration=True)
        component.generate_filelist(abs_path=True)
        component.run_lint()
        

    def check_rtl(self):
        flst_path = os.path.join(self.rtl_path, 'filelist.f')
        check_dir = os.path.join(self._rtl_dir, 'vcs_check')
        os.makedirs(check_dir, exist_ok=True)

        print("[Check RTL] Check rtl file: %s"% flst_path)
        command = f'vcs -full64 -cpp g++-4.8 -cc gcc-4.8 -LDFLAGS -Wl,--no-as-needed +lint=PCWM -debug_access+all -o {check_dir}/simv -Mdir={check_dir}/csrc -f {flst_path} | tee {check_dir}/vcs.log'

        os.system(command)


    # total ==============================================================
    def generate(self, path=None):
        super().generate(path)
        self.report_rtl()
        self.report_dv()


    def check(self, path=None):
        super().check(path)
        self.check_rtl()

    def report_dv(self):
        self.report_dv_testbench()
        self.report_dv_filelist()
        self.report_dv_ral()
        self.report_dv_testcase()

        
    #########################################
    # tablelike support
    #########################################

    def register(self, name, bit=32, description='', bus_width=APG_BUS_WIDTH, offset=0):
        from .Reg import Register
        bit_offset = offset*8
        u_reg = Register(name, bit, description, bus_width)
        u_reg.offset = bit_offset
        u_reg.father = self
        return u_reg
    
    def add_register(self, sub_space, offset, name):
        self.add(sub_space, offset+self.offset, name)
        return self
    

    @property
    def end(self):
        self.father.add(self, self.offset, self.module_name)
        return self.father

    






















    ########################################
    # report port for testbench
    ########################################

    def report_internal_field_port(self, is_base=True, prefix=''):
        # if "apb" in self.software_interface:
        #     prefix = prefix+'rs_'

        internal_port_dict = {}
        for ss in self.sub_space_list:
            for field in ss.field_list:
                if field.is_external==False:
                    if field.hw_readable and field.hw_writeable:
                        internal_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in INTERNAL_FIELD_DICT.items() }
                    elif field.hw_readable:
                        internal_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in INTERNAL_FIELD_RO_DICT.items() }
                    elif field.hw_writeable:
                        internal_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in INTERNAL_FIELD_WO_DICT.items() }
                    else:
                        internal_field_dict = {}
                    internal_port_dict[prefix+ss.module_name+'_'+field.name]=internal_field_dict
        
        return internal_port_dict
                
    
    def report_external_field_port(self, is_base=True, prefix=''):
        # if "apb" in self.software_interface:
        #     prefix = prefix+'rs_'

        external_port_dict = {}
        for ss in self.sub_space_list:
            for field in ss.field_list:
                if field.is_external==True:
                    if field.sw_readable and field.sw_writeable:
                        external_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in EXTERNAL_FIELD_DICT.items() }
                    elif field.sw_readable:
                        external_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in EXTERNAL_FIELD_RO_DICT.items() }
                    elif field.sw_writeable:
                        external_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in EXTERNAL_FIELD_WO_DICT.items() }
                    else:
                        external_field_dict = {}
                    external_port_dict[prefix+ss.module_name+'_'+field.name]=external_field_dict
        
        return external_port_dict


    def report_top_software_port(self, prefix='p_'):
        if "apb" in self.software_interface:
            top_sw_port_dict = { prefix+key: value for key,value in APB_PORT_DICT.items() }
        else:
            top_sw_port_dict = { prefix+key: value for key,value in BASE_PORT_DICT.items() }

        return top_sw_port_dict
    
    ########################################
    # dv support
    ########################################

    def report_dv_testbench(self):
        if self.sub_space_list == []:
            return []
        else:
            path = self._dv_dir+'/'
            file_name = 'tb.sv'
            input_sig_list=[]
            port_dict=self.report_internal_field_port()
            # print(port_dict)
            for port in port_dict.values():
                for port_name,direct in port.items():
                    if direct=="input":
                        input_sig_list.append(port_name)
            # print(input_sig_list)
            env = Environment(loader=PackageLoader('address_planner','report_template'))
            template = env.get_template("dv_template/tb.j2")
            text = template.render(space=self,input_sig_list=input_sig_list)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path+file_name,'w') as f:
                f.write(text)
            template = env.get_template("dv_template/Makefile.j2")
            text = template.render(space=self)
            with open(path+'Makefile','w') as f:
                f.write(text)
    

    def report_dv_filelist(self):
        if self.sub_space_list == []:
            return []
        else:
            path = self._dv_dir+'/'
            file_name = 'tb.f'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            text = self.report_from_template("dv_template/tb_filelist.j2")
            with open(path+file_name,'w') as f:
                f.write(text)
    
    def report_dv_testcase(self):
        if self.sub_space_list == []:
            return []
        else:
            path = self._dv_dir+'/'+'tc'+'/'
            file_name = 'tc_lib.sv'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            text = self.report_from_template("dv_template/tc_lib.j2")
            with open(path+file_name,'w') as f:
                f.write(text)
    
    def report_dv_ral(self):
        if self.sub_space_list == []:
            return []
        else:
            # prj_root=os.getenv("PRJ_ROOT")
            path = os.path.join(self._dv_dir, 'ral')
            os.makedirs(path, exist_ok=True)
            print(f"ralgen -full64 -t {self.module_name} -o {path}/ral_top -uvm {self._ralf_dir}/{self.module_name}.ralf")
            os.system(f"ralgen -full64 -t {self.module_name} -o {path}/ral_top -uvm {self._ralf_dir}/{self.module_name}.ralf")
            
