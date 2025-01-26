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
    def _offset(self):
        return max(self.offset) if isinstance(self.offset, list) else self.offset
     
    @property
    def _size(self):
        return self.size[self.offset.index(self._offset)] if isinstance(self.offset, list) else self.size
        
    @property
    def start_address(self):
        if isinstance(self.offset, list):
            return '\n'.join([hex(elem) for elem in self.offset])
        else:
            return hex(self.offset)
    
    @property
    def end_address(self):
        if isinstance(self.offset, list):
            return '\n'.join([hex(self.offset[idx] + self.size[idx] - 1) for idx in range(len(self.offset))])
        else: 
            return hex(self.offset + self.size - 1)
    
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
            self._next_offset = sub_space_copy._offset + sub_space_copy._size


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
            # elif key not in attr_dict.keys():
            #     print(f'[Warn] {self.module_name} has no attr: {key}')
        return {self.module_name: master_list}
    
    
    def report_slave_matrix(self):
        slave_dict = {}
        slave_json_list = self.report_slave()
        
        for slave in slave_json_list:
            slave_list = deepcopy(slave_content)
            attr_dict = slave['attribute']
            for key, value in slave_mapping.items():
                if key in slave.keys():
                    slave_list[value] = slave[key]
                elif key in attr_dict.keys():
                    slave_list[value] = attr_dict[key]
                # elif key not in attr_dict.keys():
                #     print(f'[Warn] {self.module_name} has no attr: {key}')
            slave_dict[slave["name"]] = slave_list
        
        return slave_dict
    
    
    def report_interconnect_matrix(self):
        interconnect_dict = {}
        interconnect_list = list(self.report_interconnect().values())[0]
        interconnect_dict['name'] = interconnect_list
        interconnect_dict[self.module_name] = [True for _ in interconnect_list]
        return interconnect_dict
    
    
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
        return {self.module_name: self.report_interconnect_core(mst_name)}

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
        
        
    def generate_matrix_excel(self, path=None):
        if path != None:        self.path = path
        if not os.path.exists(self._json_dir):  os.makedirs(self._json_dir) 
        wb = openpyxl.Workbook()
        # master
        ws_mst       = wb.active
        ws_mst.title = "master"
        headers0     = list(master_mapping.keys())
        ws_mst.append(headers0)

        for key, values in self.report_master_matrix().items():
            ws_mst.append(values)
            
        # slave
        ws_slv      = wb.create_sheet(title="slave")
        headers1    = list(slave_mapping.keys())
        ws_slv.append(headers1)
            
        for key, values in self.report_slave_matrix().items():
            ws_slv.append(values)
            
        # interconnection    
        ws2          = wb.create_sheet(title="interconnection")
        mapping_dict = self.report_interconnect_matrix()
        headers2     = ['name'] + list(mapping_dict['name'])
        ws2.append(headers2)

        for key in mapping_dict.keys():
            if key == 'name':   continue
            ws2.append(list([key] + mapping_dict[key]))

        wb.save(self.matrix_path)


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
            json_dict["is_active"]  = True
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
            json_dict["is_active"]  = True
            json_dict["addr_width"] = self.bus_width
            json_dict["data_width"] = self.data_width
            json_dict["min_addr"]   = self.start_address
            json_dict["max_addr"]   = str(self.end_address)
            # json_dict["size"]       = ConvertSize(self.size, is_byte=True)
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
                 rd_ost=None, wr_ost=None, ignore_signal='',
                 pre='', post='', upper='', clk='clk', 
                 freq=1000, rst='rst_n', hier='tb.dut', 
                 wr_latency=None, rd_latency=None, 
                 wr_bandwidth='', rd_bandwidth='',
                 cacheline_size=None, support_write_evict=None, 
                 no_shareable_min_addr=None, no_shareable_max_addr=None, 
                 inner_min_addr=None, inner_max_addr=None, 
                 outer_min_addr=None, outer_max_addr=None, **kwargs):
        
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
        self.ignore_signal      = ignore_signal
        self.pre                = pre 
        self.post               = post 
        self.upper              = upper
        self.clk                = clk 
        self.freq               = freq 
        self.rst                = rst
        self.hier               = hier
        self.wr_latency         = wr_latency
        self.rd_latency         = rd_latency
        self.wr_bandwidth       = wr_bandwidth
        self.rd_bandwidth       = rd_bandwidth
        self.cacheline_size     = cacheline_size
        self.support_write_evict= support_write_evict
        self.no_shareable_min_addr= no_shareable_min_addr
        self.no_shareable_max_addr= no_shareable_max_addr
        self.inner_min_addr       = inner_min_addr
        self.inner_max_addr       = inner_max_addr
        self.outer_min_addr       = outer_min_addr
        self.outer_max_addr       = outer_max_addr
        
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
    def __init__(self, name='', 
                 support_incr=True, 
                 support_wrap=True, 
                 support_fixed=True, 
                 rd_enable=True, 
                 wr_enable=True, 
                 support_reordering='NA', 
                 w_req_auser_width='NA', 
                 wuser_width='NA', 
                 buser_width='NA', 
                 r_req_auser_width='NA', 
                 ruser_width='NA', 
                 rd_id_width='NA', 
                 wr_id_width='NA', 
                 rd_ost='NA', 
                 wr_ost='NA', 
                 ignore_signal='',
                 pre='',
                 post='',
                 upper='',
                 clk='clk', 
                 freq=1000, 
                 rst='rst_n', 
                 hier='tb.dut', 
                 wr_latency='NA', 
                 rd_latency='NA', 
                 wr_bandwidth='', 
                 rd_bandwidth='',
                 cacheline_size='NA', 
                 support_write_evict='NA', 
                 no_shareable_min_addr='NA', 
                 no_shareable_max_addr='NA', 
                 inner_min_addr='NA', 
                 inner_max_addr='NA', 
                 outer_min_addr='NA', 
                 outer_max_addr='NA', **kwargs):
        super().__init__(name, support_incr, 
                         support_wrap, support_fixed, 
                         rd_enable, wr_enable, 
                         support_reordering, w_req_auser_width, 
                         wuser_width, buser_width, 
                         r_req_auser_width, ruser_width, 
                         rd_id_width, wr_id_width, 
                         rd_ost, wr_ost, ignore_signal,
                         pre, post, upper, clk, 
                         freq, rst, hier,
                         wr_latency, rd_latency,
                         wr_bandwidth, rd_bandwidth, 
                         cacheline_size, support_write_evict, 
                         no_shareable_min_addr, 
                         no_shareable_max_addr,
                         inner_min_addr, inner_max_addr,
                         outer_min_addr, outer_max_addr, **kwargs)

    
class MstMatrixAttr(MatrixAttr):
    def __init__(self, name='', 
                 support_incr=True, 
                 support_wrap=True, 
                 support_fixed=True, 
                 rd_enable=True, 
                 wr_enable=True, 
                 support_reordering='NA', 
                 support_exclusive='NA', 
                 unique_id='NA', 
                 max_len='NA', 
                 min_size='NA',
                 w_req_auser_width='NA', 
                 r_req_auser_width='NA',
                 wuser_width='NA', 
                 buser_width='NA', 
                 ruser_width='NA', 
                 rd_id_width='NA',
                 wr_id_width='NA', 
                 rd_ost='NA', 
                 wr_ost='NA', 
                 ignore_signal='',
                 pre='',
                 post='',
                 upper='',
                 clk='clk', 
                 freq=1000, 
                 rst='rst_n', 
                 hier='tb.dut', 
                 wr_latency='NA', 
                 rd_latency='NA', 
                 wr_bandwidth='', 
                 rd_bandwidth='',
                 cacheline_size='NA', 
                 support_write_evict='NA', 
                 no_shareable_min_addr='NA', 
                 no_shareable_max_addr='NA', 
                 inner_min_addr='NA', 
                 inner_max_addr='NA', 
                 outer_min_addr='NA', 
                 outer_max_addr='NA', **kwargs):
        super().__init__(name, support_incr, 
                         support_wrap, support_fixed, 
                         rd_enable, wr_enable, 
                         support_reordering, w_req_auser_width, 
                         wuser_width, buser_width, 
                         r_req_auser_width, ruser_width, 
                         rd_id_width, wr_id_width, 
                         rd_ost, wr_ost, ignore_signal,
                         pre, post, upper, clk, 
                         freq, rst, hier, 
                         wr_latency, rd_latency,
                         wr_bandwidth, rd_bandwidth, 
                         cacheline_size, support_write_evict, 
                         no_shareable_min_addr, 
                         no_shareable_max_addr,
                         inner_min_addr, inner_max_addr,
                         outer_min_addr, outer_max_addr, **kwargs)
        
        self.support_exclusive  = support_exclusive
        self.unique_id          = unique_id
        self.max_len            = max_len
        self.min_size           = min_size

        