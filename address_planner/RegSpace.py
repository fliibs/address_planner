import json
from .GlobalValues  import *
from .AddressSpace  import AddressSpace

from .RegSpaceRTL import *

class RegSpace(AddressSpace):

    def __init__(self,name,size,description='',path='./',bus_width=APG_BUS_WIDTH,software_interface='apb'):
        super().__init__(name=name,size=size,description=description,path=path)
        self.bus_width = bus_width
        #self._name_prefix = 'reg'
        self.software_interface = software_interface

    def __str__(self) -> str:
        return self.module_name


    #########################################################################################
    # output generate
    #########################################################################################

    def report_html(self):
        text = self.report_from_template(APG_HTML_FILE_REG_SPACE)
        with open(self.html_path,'w') as f:
            f.write(text)
        for ss in self.sub_space_list:
            ss.report_html()

    def report_chead_core(self):
        chead_name_list = [self.chead_name]
        text = self.report_from_template(APG_CHEAD_FILE_REG_SPACE)
        with open(self.chead_path,'w') as f:
            f.write(text)
        for ss in self.sub_space_list:
            chead_name_list += ss.report_chead_core()
        return chead_name_list

    def report_vhead_core(self):
        vhead_name_list = [self.vhead_name]
        text = self.report_from_template(APG_VHEAD_FILE_REG_SPACE)
        with open(self.vhead_path,'w') as f:
            f.write(text)
        for ss in self.sub_space_list:
            vhead_name_list += ss.report_vhead_core()
        return vhead_name_list
    
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
        component.output_dir = "address_planner_reg_rtl"
        component.generate_verilog(iteration=True)
        component.generate_filelist()
        component.run_lint()
        # component.run_slang_compile()

    def register(self, name, bit=32, description='', bus_width=APG_BUS_WIDTH):
        from .Reg import Register

        u_reg = Register(name, bit, description, bus_width)
        u_reg.father = self
        return u_reg
    
    @property
    def generate(self):
        self.report_rtl()
        self.report_json()


    