from .GlobalValues      import *
from .AddressSpace      import *
from copy               import deepcopy

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
        # if not Options.MultiPortOption:
            # if not self.inclusion_detect(sub_space_copy):
            #     raise Exception('Sub space %s is not included in space %s' %(sub_space_copy.module_name,self.module_name))

            # for exist_space in self.sub_space_list:
            #     # if self.naming_detect(exist_space,sub_space_copy):
            #     #     raise Exception('Sub space %s(%s to %s) and current sub space %s(%s to %s) conflict.' \
            #     #         % (sub_space_copy.module_name,hex(sub_space_copy.start_address),hex(sub_space_copy.end_address),exist_space.module_name,hex(exist_space.start_address),hex(exist_space.end_address)))
            #     if self.collision_detect(exist_space,sub_space_copy):
            #         raise Exception('Sub space %s(%s to %s) and current sub space %s(%s to %s) conflict.' \
            #             % (sub_space_copy.module_name,hex(sub_space_copy.start_address),hex(sub_space_copy.end_address),exist_space.module_name,hex(exist_space.start_address),hex(exist_space.end_address)))
        self.sub_space_list.append(sub_space_copy)
        if sub_space_copy.offset != None:
            self._next_offset = sub_space_copy.offset + sub_space_copy.size


    def add_incr(self,sub_space,name,attr=None):
        self.add(sub_space=sub_space,offset=self._next_offset,name=name,attr=attr)

    # def report_interconnect_core(self):


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
            json_dict["description"]= self.description
            json_dict["attribute"]  = self.report_json_attr_core()
            json_dict["children"]   = self.expand_list([c.report_json_core() for c in self.sub_space_list])
            return json_dict
        elif self.sub_space_list == []:
            json_dict={}
            json_dict["key"]        = ADD_KEY()
            json_dict["name"]       = self.module_name
            json_dict["start_addr"] = hex(int(self.start_address))
            json_dict["end_addr"]   = hex(int(self.end_address))
            
            json_dict["size"]       = ConvertSize(self.size, is_byte=True)
            json_dict["description"]= self.description
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
                 support_reordering=None, awuser_width=None,
                 wuser_width=None, buser_width=None, 
                 aruser_width=None, ruser_width=None, 
                 rd_id_width=None, wr_id_width=None,
                 rd_ost=None, wr_ost=None, clk='clk', 
                 freq=1000, rst='rst_n', hier='tb.dut', **kwargs):
        
        self.name = name
        self.support_incr = support_incr
        self.support_wrap = support_wrap
        self.support_fixed = support_fixed
        self.rd_enable    = rd_enable
        self.wr_enable    = wr_enable
        self.support_reordering = support_reordering
        self.awuser_width = awuser_width
        self.wuser_width  = wuser_width
        self.buser_width  = buser_width
        self.aruser_width = aruser_width
        self.ruser_width  = ruser_width
        self.rd_id_width  = rd_id_width
        self.wr_id_width  = wr_id_width
        self.rd_ost       = rd_ost
        self.wr_ost       = wr_ost
        self.clk          = clk 
        self.freq         = freq 
        self.rst          = rst
        self.hier         = hier
        
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
                 support_reordering=None, awuser_width=None, 
                 wuser_width=None, buser_width=None, 
                 aruser_width=None, ruser_width=None, 
                 rd_id_width=None, wr_id_width=None, 
                 rd_ost=None, wr_ost=None, 
                 clk='clk', freq=1000, rst='rst_n', 
                 hier='tb.dut', **kwargs):
        super().__init__(name, support_incr, 
                         support_wrap, support_fixed, 
                         rd_enable, wr_enable, 
                         support_reordering, awuser_width, 
                         wuser_width, buser_width, 
                         aruser_width, ruser_width, 
                         rd_id_width, wr_id_width, 
                         rd_ost, wr_ost, clk, freq, rst, hier, **kwargs)

    
class MstMatrixAttr(MatrixAttr):
    def __init__(self, name='', support_incr=None, 
                 support_wrap=None, support_fixed=None, 
                 rd_enable=True, wr_enable=True, 
                 support_reordering=None, awuser_width=None, 
                 wuser_width=None, buser_width=None, 
                 aruser_width=None, ruser_width=None, 
                 rd_id_width=None, wr_id_width=None, 
                 rd_ost=None, wr_ost=None, 
                 clk='clk', freq=1000, rst='rst_n', 
                 hier='tb.dut', support_exclusive=None, 
                 unique_id=None, max_len=None, min_size=None, **kwargs):
        super().__init__(name, support_incr, 
                         support_wrap, support_fixed, 
                         rd_enable, wr_enable, 
                         support_reordering, awuser_width, 
                         wuser_width, buser_width, 
                         aruser_width, ruser_width, 
                         rd_id_width, wr_id_width, 
                         rd_ost, wr_ost, clk, freq, rst, hier, **kwargs)
        self.support_exclusive = support_exclusive
        self.unique_id = unique_id
        self.max_len   = max_len
        self.min_size  = min_size
        