import json
from .GlobalValues  import *
from .AddressSpace  import AddressSpace
from copy               import deepcopy
from .RegSpaceRTL import *
import shutil
import re

class RegSpace(AddressSpace):

    def __init__(self,name,size,description='',path='./',bus_width=APG_BUS_WIDTH,software_interface='apb'):
        super().__init__(name=name,size=size,description=description,path=path)
        self.bus_width = bus_width
        self.data_width = APG_BUS_WIDTH
        #self._name_prefix = 'reg'
        self.software_interface = software_interface
        self.rtl_path = ''

    def __str__(self) -> str:
        return self.module_name

    def add(self,sub_space,offset,name=None,lock_list=[], magic_list=[]):
        bit_offset = offset*8
        sub_space_copy = deepcopy(sub_space)
        sub_space_copy.offset = bit_offset
        sub_space_copy.father = self
        sub_space_copy.module_name = sub_space_copy.module_name if name==None else name

        self.check_list(lock_list)
        for member in lock_list:
            if member not in sub_space_copy.lock_list:
                sub_space_copy.lock_list.append(member)

        self.check_list(magic_list)
        for member in magic_list:
            if member not in sub_space_copy.magic_list:
                sub_space_copy.magic_list.append(member)

        # if not self.intr_detect(sub_space_copy):
        #     raise Exception('Intr err')

        if not self.inclusion_detect(sub_space_copy):
            raise Exception('Sub space %s is not included in space %s' %(sub_space_copy.module_name,self.module_name))

        for exist_space in self.sub_space_list:
            if self.collision_detect(exist_space,sub_space_copy):
                raise Exception('Sub space %s(%s to %s) and current sub space %s(%s to %s) conflict.' \
                    % (sub_space_copy.module_name,hex(sub_space_copy.start_address),hex(sub_space_copy.end_address),exist_space.module_name,hex(exist_space.start_address),hex(exist_space.end_address)))
        self.sub_space_list.append(sub_space_copy)
        
        self._next_offset = bit_offset + sub_space.bit
    

    def add_incr(self,sub_space,name=None,lock_list=[],magic_list=[]):
        self.add(sub_space=sub_space,offset=int(self._next_offset/8),name=name,lock_list=lock_list,magic_list=magic_list)


    def add_intr(self,sub_space,offset,name=None):
        from .Reg import Register
        if not self.intr_detect(sub_space):
            raise Exception('Intr err')
        
        reg_raw_statue  = Register(name=f'{sub_space.module_name}_raw_status',bit=32,description=f'interrupt raw status register {sub_space.description}',reg_type=sub_space.reg_type)
        reg_enable      = Register(name=f'{sub_space.module_name}_enable',bit=32,description=f'interrupt enable register {sub_space.description}',reg_type=sub_space.reg_type)
        if sub_space.reg_type==IntrMask:
            reg_mask        = Register(name=f'{sub_space.module_name}_mask',bit=32,description=f'interrupt mask register {sub_space.description}',reg_type=sub_space.reg_type)
        
        for field in sub_space.field_list:
            if isinstance(field, IntrField):                                            reg_raw_statue.add(field, field.bit_offset)
            elif isinstance(field, IntrEnableField):                                    reg_enable.add(field, field.bit_offset-32)
            elif sub_space.reg_type==IntrMask and isinstance(field, IntrMaskField):     reg_mask.add(field, field.bit_offset-64) 
            else:                                                                       raise Exception('Error field!')
            
        name_raw_status = None if name==None else f'{name}_raw_status'
        name_enable     = None if name==None else f'{name}_enable'
        self.add(sub_space=reg_raw_statue, offset=offset, name=name_raw_status)
        self.add(sub_space=reg_enable, offset=offset+4, name=name_enable)
        if sub_space.reg_type==IntrMask:
            name_mask       = None if name==None else f'{name}_mask'
            self.add(sub_space=reg_mask, offset=offset+8, name=name_mask)


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
    
    
    # report and check rtl ==============================================
    def report_rtl(self):
        component = RegSpaceRTL(self).u
        component.output_dir = self._rtl_dir
        self.rtl_path = os.path.join(component.output_path)
        component.generate_verilog(iteration=True)
        component.generate_filelist(abs_path=True)
        component.run_lint()
        

    # total ==============================================================
    def generate(self, path=None, report_dv=False):
        super().generate(path)
        self.report_rtl()
        if report_dv: self.report_dv()


    def check(self, path=None):
        super().check(path)
        self.check_rtl()

    def report_dv(self):
        self.report_dv_testbench()
        self.report_dv_filelist()
        self.report_dv_ral()
        self.report_dv_testcase()
        self.move_dv_env()

        
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
    # check 
    ########################################

    def check_rtl(self):
        flst_path = os.path.join(self.rtl_path, 'filelist.f')
        check_dir = os.path.join(self._rtl_dir, 'vcs_check')
        os.makedirs(check_dir, exist_ok=True)

        print("\n################################################################################")
        print("[Check RTL] Check rtl file: %s"% flst_path)
        print("################################################################################\n")
        command = f'vcs -full64 -cpp g++-4.8 -cc gcc-4.8 -LDFLAGS -Wl,--no-as-needed +lint=PCWM -debug_access+all -o {check_dir}/simv -Mdir={check_dir}/csrc -f {flst_path} | tee {check_dir}/vcs.log'
        os.system(command)

        # with open(f'{check_dir}/vcs.log','r') as f:
        #     if not re.search(r'simv\sup\sto\sdate', f.readlines()[-1]): 
        #         raise Exception("vcs check error occur, log path:%s"% os.path.abspath(f'{check_dir}/vcs.log'))
        if not os.path.exists(f'{check_dir}/simv'):
            raise Exception("vcs check error occur, log path:%s"% os.path.abspath(f'{check_dir}/vcs.log'))
        print("[Check RTL] vcs check output log: %s"% os.path.abspath(f'{check_dir}/vcs.log'))


    def check_ralf(self):
        output_file = self._ralf_dir+'/'+self.module_name+'.ralf'
        output_path = self._ral_model_dir+'/'
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        print("\n################################################################################")
        print("[Check Ralf] Check ralf file: %s"% output_file)
        print("################################################################################\n")
        command = f'ralgen -full64 -uvm -t {self.module_name} {output_file}'

        # if os.path.exists(f'ral_{self.module_name}.sv'): os.system(f'mv ral_{self.module_name}.sv {output_path}')
        if os.system(command)==0: os.system(f'mv ral_{self.module_name}.sv {output_path}')
        else: raise Exception("ralgen fail!")
        print("[Check Ralf] output path of ral model: %s"% os.path.abspath(os.path.join(output_path, f'ral_{self.module_name}.sv')))


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
                    internal_field_dict = {}
                    if field.hw_readable:
                        internal_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in INTERNAL_FIELD.rd_field_dict.items() }
                        if field.hw_read_clean or field.hw_read_set:
                            internal_field_dict = {prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in INTERNAL_FIELD.rd_extra_field_dict.items()}
                    if field.hw_writeable:
                        internal_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in INTERNAL_FIELD.wr_field_dict.items() }

                    internal_port_dict[prefix+ss.module_name+'_'+field.name]=internal_field_dict
        
        return internal_port_dict
                
    
    def report_external_field_port(self, is_base=True, prefix=''):
        # if "apb" in self.software_interface:
        #     prefix = prefix+'rs_'

        external_port_dict = {}
        for ss in self.sub_space_list:
            for field in ss.field_list:
                if field.is_external==True:
                    external_field_dict = {}
                    if field.sw_readable:
                        external_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in EXTERNAL_FIELD.rd_define_dict.items() }
                    if field.sw_writeable:
                        external_field_dict = { prefix+ss.module_name+'_'+field.name+'_'+key:value for key,value in EXTERNAL_FIELD.wr_define_dict.items() }

                    external_port_dict[prefix+ss.module_name+'_'+field.name]=external_field_dict
        
        return external_port_dict


    def report_top_software_port(self, prefix='p_'):
        if "apb" in self.software_interface:
            top_sw_port_dict = { prefix+key: value for key,value in APB_PORT.define_dict.items() }
        else:
            top_sw_port_dict = { prefix+key: value for key,value in BASE_PORT.define_dict.items() }

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
    
    def move_dv_env(self):
        dir_path, _ = os.path.split(os.path.realpath(__file__))
        root_path = os.path.abspath(os.path.join(dir_path,'..'))
        src_path = os.path.join(root_path, 'dv_env')
        dst_path = os.path.join(self._dv_dir, 'dv_env')
        if os.path.exists(dst_path): shutil.rmtree(dst_path)
        shutil.copytree(src_path, dst_path)
        
        setup_path = os.path.join(dst_path,'setup_dv.sh')
        dv_setup_path = os.path.join(self._dv_dir,'setup_dv.sh')
        if not os.path.exists(dv_setup_path): shutil.move(setup_path, self._dv_dir)






            
