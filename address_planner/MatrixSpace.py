from .GlobalValues      import *
from .AddressSpace      import *
from copy               import deepcopy
from .address_planner_rtl.MatrixCFG import *

class MatrixSpace(AddressSpace):
    def __init__(self,name, offset=None,size=None,description='', path='./',bus_width=APG_BUS_WIDTH,data_width=APG_DATA_WIDTH,software_interface='apb'):
        super().__init__(name=name,size=size,description=description,path=path)
        self.bus_width = bus_width
        self.data_width = data_width
        self.software_interface = software_interface
        self.offset = offset
        self.attr = None
        self._next_offset = 0
        
        
    @property
    def start_address(self):
        return self.offset
    
    @property
    def end_address(self):
        return self.offset + self.size - 1
    
    def add_attr(self, attr):
        if attr is None:                        pass                  
        elif not isinstance(attr, MatrixAttr):  raise Exception()
        self.attr = attr

    def add(self,sub_space,name=None,attr=None, offset=None):
        sub_space_copy = deepcopy(sub_space)
        # sub_space_copy.offset = offset
        sub_space_copy.father = self
        sub_space_copy.module_name = sub_space_copy.module_name if name==None else name
        sub_space_copy.offset = sub_space_copy.offset if offset==None else offset
        sub_space_copy.add_attr(attr)
        
        self.sub_space_list.append(sub_space_copy)
        if sub_space_copy.offset != None:
            self._next_offset = sub_space_copy.offset + sub_space_copy.size


    def add_incr(self,sub_space,name,attr=None):
        self.add(sub_space=sub_space,offset=self._next_offset,name=name,attr=attr)
        
        
    def report_master_matrix(self):
        master_list = deepcopy(master_content)
        master_dict = self.report_master()
        attr_dict   = master_dict['attribute']
        
        for key, value in master_mapping.items():
            if key in master_dict.keys():
                master_list[value] = master_dict[key]
            elif key in attr_dict.keys():
                master_list[value] = attr_dict[key]
                
        return master_list
    
    # def report_slave_matrix(self):
    
    
    def report_master(self):
        if self.father is None or not isinstance(self.father, MatrixSpace):
            json_dict={}
            json_dict["key"]        = ADD_KEY()
            json_dict["name"]       = self.module_name
            json_dict["is_active"]  = True
            json_dict["protocol"]   = self.software_interface
            json_dict["addr_width"] = self.bus_width
            json_dict["data_width"] = self.data_width
            json_dict["attribute"]  = self.report_json_attr_core()
            json_dict["children"]   = self.expand_list([c.report_interconnect() for c in self.sub_space_list])
            return json_dict
        
    def report_slave(self):
        if self.father is None or not isinstance(self.father, MatrixSpace):
            return self.expand_list([c.report_json_core() for c in self.sub_space_list])
        elif self.sub_space_list == []:
            return self.report_json_core()
        else:
            json_list = [c.report_json_core() for c in self.sub_space_list]
            return json_list
            
        
    def report_interconnect(self, mst_name=None):
        return self.report_interconnect_core(mst_name)

    def report_interconnect_core(self, mst_name):
        if self.father is None or not isinstance(self.father, MatrixSpace):
            return self.expand_list([c.report_interconnect_core(mst_name) for c in self.sub_space_list])
        elif self.sub_space_list == []:
            
            if mst_name == None:
                return f"{self.module_name}"
            else:
                return f"{mst_name}.{self.module_name}"
        else: 
            return [c.report_interconnect_core(mst_name) for c in self.sub_space_list]


    def report_matrix(self, path=None):
        if path != None:        self.path = path
        json_list= [self.report_json_core()]
        jtext = json.dumps(json_list, ensure_ascii=False, indent=2)
        if not os.path.exists(self._json_dir):  os.makedirs(self._json_dir) 
        with open(self.matrix_path, 'w') as f:
            f.write(jtext)

    def report_json_core(self):
        if self.father is None or not isinstance(self.father, MatrixSpace):
            json_dict={}
            json_dict["key"]        = ADD_KEY()
            json_dict["name"]       = self.module_name
            json_dict["protocol"]   = self.software_interface
            json_dict["addr_width"] = self.bus_width
            json_dict["data_width"] = self.data_width
            json_dict["attribute"]  = self.report_json_attr_core()
            json_dict["children"]   = self.expand_list([c.report_json_core() for c in self.sub_space_list])
            return json_dict
        elif self.sub_space_list == []:
            json_dict={}
            json_dict["key"]        = ADD_KEY()
            json_dict["name"]       = self.module_name
            json_dict["protocol"]   = self.software_interface
            json_dict["addr_width"] = self.bus_width
            json_dict["data_width"] = self.data_width
            json_dict["start_addr"] = hex(int(self.start_address))
            json_dict["end_addr"]   = hex(int(self.end_address))
            json_dict["size"]       = ConvertSize(self.size, is_byte=True)
            json_dict["attribute"]  = self.report_json_attr_core()
            return json_dict
        else:
            json_list = [c.report_json_core() for c in self.sub_space_list]
            return json_list
        
    def expand_list(self, sub_list):
        return [item for elem in sub_list for item in (self.expand_list(elem) if isinstance(elem, list) else [elem])]

    def naming_detect(self, space_A, space_B):
        return space_A.inst_name == space_B.inst_name

    def report_json_attr_core(self):
        json_dict={}
        if self.attr is None:       return json_dict
        for key, val in self.attr.attr_dict.items():
            json_dict[key]      = val
        return json_dict
    
    


class MatrixAttr:
    def __init__(self, name='', support_incr=None, support_wrap=None, 
                 support_fixed=None, rd_enable=True, wr_enable=True, 
                 support_reordering=None, w_req_auser_width=None,
                 wuser_width=None, buser_width=None, 
                 r_req_auser_width=None, ruser_width=None, 
                 rd_id_width=None, wr_id_width=None,
                 rd_ost=None, wr_ost=None, clk='clk', 
                 freq=1000, rst='rst_n', hier='tb.dut', **kwargs):
        
        self.name = name
        self.support_incr       = support_incr
        self.support_wrap       = support_wrap
        self.support_fixed      = support_fixed
        self.rd_enable          = rd_enable
        self.wr_enable          = wr_enable
        self.support_reordering = support_reordering
        self.w_req_auser_width  = w_req_auser_width
        self.wuser_width        = wuser_width
        self.buser_width        = buser_width
        self.r_req_auser_width  = r_req_auser_width
        self.ruser_width        = ruser_width
        self.rd_id_width        = rd_id_width
        self.wr_id_width        = wr_id_width
        self.rd_ost             = rd_ost
        self.wr_ost             = wr_ost
        self.clk                = clk 
        self.freq               = freq 
        self.rst                = rst
        self.hier               = hier
        
        for key, value in kwargs.items():
            if not hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"'{key}' is not a valid class member.")

    @property    
    def attr_dict(self):      
        all_members = {k: v for k, v in self.__dict__.items() if not k.startswith('__')}
        return all_members

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
            
    def __repr__(self):
        all_members = {k: v for k, v in self.__dict__.items() if not k.startswith('__')}
        return f"MatrixAttr({all_members})"

    # def __deepcopy__(self, memo):
    #     new_copy = type(self)()
    #     new_copy._attributes = deepcopy(self._attributes, memo)
    #     return new_copy

class SlvMatrixAttr(MatrixAttr):
    def __init__(self, name='', support_incr=None, 
                 support_wrap=None, support_fixed=None, 
                 rd_enable=True, wr_enable=True, 
                 support_reordering=None, w_req_auser_width=None, 
                 wuser_width=None, buser_width=None, 
                 r_req_auser_width=None, ruser_width=None, 
                 rd_id_width=None, wr_id_width=None, 
                 rd_ost=None, wr_ost=None, 
                 clk='clk', freq=1000, rst='rst_n', 
                 hier='tb.dut', **kwargs):
        super().__init__(name, support_incr, 
                         support_wrap, support_fixed, 
                         rd_enable, wr_enable, 
                         support_reordering, w_req_auser_width, 
                         wuser_width, buser_width, 
                         r_req_auser_width, ruser_width, 
                         rd_id_width, wr_id_width, 
                         rd_ost, wr_ost, clk, freq, rst, hier, **kwargs)

    
class MstMatrixAttr(MatrixAttr):
    def __init__(self, name='', support_incr=None, 
                 support_wrap=None, support_fixed=None, 
                 rd_enable=True, wr_enable=True, 
                 support_reordering=None, w_req_auser_width=None, 
                 wuser_width=None, buser_width=None, 
                 r_req_auser_width=None, ruser_width=None, 
                 rd_id_width=None, wr_id_width=None, 
                 rd_ost=None, wr_ost=None, 
                 clk='clk', freq=1000, rst='rst_n', 
                 hier='tb.dut', support_exclusive=None, 
                 unique_id=None, max_len=None, min_size=None, **kwargs):
        super().__init__(name, support_incr, 
                         support_wrap, support_fixed, 
                         rd_enable, wr_enable, 
                         support_reordering, w_req_auser_width, 
                         wuser_width, buser_width, 
                         r_req_auser_width, ruser_width, 
                         rd_id_width, wr_id_width, 
                         rd_ost, wr_ost, clk, freq, rst, hier, **kwargs)
        
        self.support_exclusive  = support_exclusive
        self.unique_id          = unique_id
        self.max_len            = max_len
        self.min_size           = min_size
        