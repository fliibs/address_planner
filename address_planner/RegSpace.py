import json
from .GlobalValues  import *
from .AddressSpace  import AddressSpace
from copy               import deepcopy
from .RegSpaceRTL import *

class RegSpace(AddressSpace):

    def __init__(self,name,size,description='',path='./',bus_width=APG_BUS_WIDTH,software_interface='apb'):
        super().__init__(name=name,size=size,description=description,path=path)
        self.bus_width = bus_width
        #self._name_prefix = 'reg'
        self.software_interface = software_interface

    def __str__(self) -> str:
        return self.module_name

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
        
        self._next_offset = offset + sub_space.bit


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
    
    
    def report_ral_model(self):
        output_path = self._ral_model_dir+'/'
        self.report_ral_model_core(output_path)
        #self.report_ral_model_define_core(output_path)
        #self.report_ral_model_csv_core(output_path)

    def report_ralf(self):
        output_path = self._ralf_dir+'/'
        self.report_ralf_core(output_path)


    def report_ralf_core(self, output_dir):
        if self.sub_space_list == []:
            return []
        else:
            file_name = 'ralf_'+self.module_name+'.ralf'
            path = output_dir+'/'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            text = self.report_from_template(APG_REG_RALF_FILE_REG_SPACE, {'head_type':'ralf'})
            with open(path+file_name,'w') as f:
                f.write(text)


    def report_ral_model_core(self, output_dir):
        if self.sub_space_list == []:
            return []
        else:
            file_name = 'ral_block_'+self.module_name+'.sv'
            path = output_dir+'/'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            text = self.report_from_template(APG_REG_RMODEL_FILE_REG_SPACE, {'head_type':'sv'})
            with open(path+file_name,'w') as f:
                f.write(text)

    
    # def report_ral_model_define_core(self, output_dir):
    #     if self.sub_space_list == []:
    #         return []
    #     else:
    #         file_name = 'ral_block_'+self.module_name+'_define.v'
    #         path = output_dir+'/'
    #         os.makedirs(os.path.dirname(path), exist_ok=True)
    #         text = self.report_from_template(APG_REG_RMDEFINE_FILE_REG_SPACE, {'head_type':'v'})
    #         with open(path+file_name,'w') as f:
    #             f.write(text)

    # def report_ral_model_csv_core(self, output_dir):
    #     if self.sub_space_list == []:
    #         return []
    #     else:
    #         file_name = self.module_name+'.csv'
    #         path = output_dir+'/'
    #         os.makedirs(os.path.dirname(path), exist_ok=True)
    #         text = self.report_from_template(APG_REG_RMCSV_FILE_REG_SPACE, {'head_type':'csv'})
    #         with open(path+file_name,'w') as f:
    #             f.write(text)
    
    # def report_json_core(self, output_dir='.'):
    #     json_list=[]
    #     json_dict={}
    #     json_dict["key"] = ADD_KEY()
    #     json_dict["type"] = "sys"
    #     json_dict["name"] = self.module_name
    #     json_dict["start_addr"] = self.start_address
    #     json_dict["end_addr"] = self.end_address
    #     json_dict["size"] = ConvertSize(self.size)
    #     child_list = []
    #     for sub in self.sub_space_list:
    #         sub.report_json(child_list)

    #     json_dict["children"] = child_list
    #     json_list.append(json_dict)
    #     jtext = json.dumps(json_list,ensure_ascii=False, indent=2)
    #     json_name = self.module_name+'.json'
    #     with open(output_dir+'/'+json_name, 'w') as f:
    #         f.write(jtext)



    def report_rtl(self):
        component = RegSpaceRTL(self).u
        component.output_dir = self._rtl_dir
        component.generate_verilog(iteration=True)
        component.generate_filelist()
        component.run_lint()
        # component.run_slang_compile()

    def register(self, name, bit=32, description='', bus_width=APG_BUS_WIDTH, offset=0):
        from .Reg import Register

        u_reg = Register(name, bit, description, bus_width)
        u_reg.offset = offset
        u_reg.father = self
        return u_reg
    
    def add_register(self, sub_space, offset, name):
        self.add(sub_space, offset+self.offset, name)
        return self
    

    @property
    def end(self):
        self.father.add(self, self.offset, self.module_name)
        return self.father

    def generate(self, path=None):
        super().generate(path)
        self.report_rtl()


    