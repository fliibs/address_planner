from copy               import deepcopy
from functools          import reduce
from .AddressLogicRoot  import *
from .GlobalValues      import *

import os
import builtins
import json

class AddressSpace(AddressLogicRoot):

    def __init__(self,name,size,description='',path='./'):
        super().__init__(name=name,description=description,path=path)
        #self.module_name    = name
        #self.module_name      = ''
        #self.name           = name
        #self.start_address  = start_address
        self.size           = size
        #self.end_address    = self.start_address + self.size - 1
        self.sub_space_list = []
        #self.description    = description
        #self.path           = path
        #self.father         = None
        self.offset         = 0

        self._next_offset   = 0



    @property
    def global_offset(self):
        return 0 if self.father is None else self.father.global_offset + self.offset

    @property
    def global_start_address(self):
        return self.global_offset

    @property
    def global_end_address(self):
        return self.global_offset + self.size - 1

    @property
    def start_address(self):
        return self.offset

    @property
    def end_address(self):
        return self.offset + self.size - 1








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
        # print(self.start_address, self.end_address, self._next_offset, sub_space_copy.size)


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




    #########################################################################################
    # output generate
    #########################################################################################



    def report_html(self):
        text = self.report_from_template(APG_HTML_FILE_ADDR_SPACE)
        with open(self.html_path,'w') as f:
            f.write(text)
        for ss in self.sub_space_list:
            ss.report_html()

    def report_chead(self):
        chead_name_list = self.report_chead_core()
        with open(os.path.join(self._chead_dir,'all.h'),'w') as f:
            for chead_name in chead_name_list:
                f.write("#include \"%s\"\n" % chead_name)

    def check_chead(self):
        file_path = os.path.join(self._chead_dir,'all.h')
        if os.system('gcc -include stdint.h %s' % file_path) !=0:
            raise Exception('c head compile error.')


    def report_vhead(self):
        vhead_name_list = self.report_vhead_core()
        with open(os.path.join(self._vhead_dir,'all.vh'),'w') as f:
            for vhead_name in vhead_name_list:
                f.write("`include \"%s\"\n" % vhead_name)


    def report_chead_core(self):
        if self.sub_space_list == []:
            return []
        else:
            chead_name_list = [self.chead_name]
            text = self.report_from_template(APG_CHEAD_FILE_ADDR_SPACE,{'head_type':'c'})
            with open(self.chead_path,'w') as f:
                f.write(text)
            for ss in self.sub_space_list:
                chead_name_list += ss.report_chead_core()
            return chead_name_list


    def report_vhead_core(self):
        if self.sub_space_list == []:
            return []
        else:
            vhead_name_list = [self.vhead_name]
            text = self.report_from_template(APG_VHEAD_FILE_ADDR_SPACE,{'head_type':'v'})
            with open(self.vhead_path,'w') as f:
                f.write(text)
            for ss in self.sub_space_list:
                vhead_name_list += ss.report_vhead_core()
            return vhead_name_list

        # env = Environment(loader=PackageLoader('address_planner','report_template'))
        # template = env.get_template('mem_space.html')
        # template.globals['builtins'] = builtins
        # text = template.render(space=self)

        # env = Environment(loader=PackageLoader('address_planner','report_template'))
        # template = env.get_template('chead_space.h')
        # template.globals['builtins'] = builtins
        # text = template.render(space=self)

    def regbank(self, name,size,description='',path='./',bus_width=APG_BUS_WIDTH,software_interface='apb'):
        from .RegSpace import RegSpace

        u_ss = RegSpace(name=name, size=size, description=description, path=path, bus_width=bus_width, software_interface=software_interface)
        u_ss.father = self 
        return u_ss
    
    def add_regbank(self, sub_space):
        # sub_space.father = self 
        self.add_incr(sub_space, sub_space.module_name)
        return self

    def report_json_core(self):
        json_dict={}
        json_dict["key"]        = ADD_KEY()
        json_dict["type"]       = "sys"
        json_dict["name"]       = self.module_name
        json_dict["start_addr"] = self.start_address
        json_dict["end_addr"]   = self.end_address
        json_dict["size"]       = ConvertSize(self.size)
        json_dict["description"]= self.description
        json_dict["children"]   = [c.report_json_core() for c in self.sub_space_list]
        return json_dict

    def report_json(self):
        json_list= [self.report_json_core()]
        jtext = json.dumps(json_list, ensure_ascii=False, indent=2)
        with open(self.json_path, 'w') as f:
            f.write(jtext)

    @property
    def generate(self):
        for sub_space in self.sub_space_list:
            sub_space.report_rtl()
        json_list =[sub_space.report_json_core() for sub_space in self.sub_space_list]
        jtext = json.dumps(json_list, ensure_ascii=False, indent=2)
        with open(self.json_path, 'w') as f:
            f.write(jtext)