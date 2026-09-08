from ..timing import phase, timed
from tkinter import Tcl
from ..GlobalValues import *
from copy               import deepcopy
import re 



# tcl_interpreter = Tcl()
# tcl_interpreter.eval("source ralf_parser.tcl")

py_dict = {}


class RalfParseError(ValueError):
    """Raised when a RALF input cannot be converted into an address model."""


class RalfNumericParseError(RalfParseError):
    """Carry the failing RALF token and Tcl hierarchy to the file-level caller."""

    def __init__(self, raw_value, hierarchy):
        self.raw_value = raw_value
        self.hierarchy = hierarchy
        super().__init__(
            f"invalid RALF numeric value {raw_value!r} at Tcl hierarchy {hierarchy}"
        )


def convert_address_with_context(value, hierarchy):
    try:
        return convert_address(value)
    except (TypeError, ValueError) as exc:
        raise RalfNumericParseError(value, hierarchy) from exc


@timed("ralf.select_root", progress=True)
def search_longest_string(tcl_interpreter):
    keys =  tcl_interpreter.eval('array names DEF')
    max_length_key  = max(keys.split(' '),key=lambda k: len(tcl_interpreter.eval(f'set result [dict get $DEF({k})]')))
    return max_length_key


@timed("ralf.build_model", progress=True)
def build_addrspace(tcl_interpreter):

    # search the longest string 
    key_array = search_longest_string(tcl_interpreter)
    py_dict.clear()
    py_dict[key_array] = {}

    #### update py_dict
    tcl_array = f'$DEF({key_array})'
    data_array = tcl_interpreter.eval(f'set result [dict get {tcl_array}]')
    keys_array = tcl_interpreter.eval('set keys [dict keys $result]')
    key_list = keys_array.split(' ')
    with phase("ralf.tcl_to_python", progress=True):
        tcl_dict_recur(key_list, dict_=py_dict[key_array], tcl_dict=tcl_array, tcl_interpreter=tcl_interpreter)
    # print(py_dict)

    #### build rb
    from ..RegSpace import RegSpace
    # RALF offsets are byte-addressed and can be byte-granular.  This importer is
    # an address-model path, not a promise that every imported map can use the
    # 32-bit register-RTL backend.
    reg_bank_B = RegSpace(name=py_dict[key_array]['name'], size=1e20*GB,bus_width=8,software_interface='apb')
    with phase("ralf.build_objects", progress=True):
        reg_bank_B_copy = build_subspace_recur(py_dict[key_array]['ADDR_DICT'], reg_bank_B, tcl_interpreter=tcl_interpreter)
    # reg_bank_B_copy.generate('build/ralf')
    reg_bank_B_copy = minimum_size(reg_bank_B_copy)
    return reg_bank_B_copy



def build_subspace_recur(dict_, father, tcl_interpreter):
    # Keep the caller's tree isolated, but do not clone the growing tree for
    # every child. Recursive work below owns this one private copy.
    with phase("ralf.deepcopy"):
        owned = deepcopy(father)
    return _build_subspace_inplace(dict_, owned, tcl_interpreter)


def _build_subspace_inplace(dict_, father, tcl_interpreter):
    from ..Reg      import Register
    from ..RegSpace import RegSpace 
    from ..AddressSpace import AddressSpace

    father_copy = father
    if 'name' not in dict_.keys():   
        for key in dict_.keys():   
            father_copy = _build_subspace_inplace(dict_[key], father_copy, tcl_interpreter)
        father_copy = _minimum_size_inplace(father_copy)

    elif 'is_memory' in dict_.keys():
        # for memory block
        print(f"Memory: {dict_['name']}: {dict_['size']}")
        mem_B = AddressSpace(name=dict_['name'], size=dict_['size'])
        if isinstance(father_copy, RegSpace):   father_copy = AddressSpace(name=father_copy.module_name, size=1e20*GB)
        father_copy.add(sub_space=mem_B, name=dict_['name'], offset=int(dict_['addr']))
    else:
        # recur field dict
        if dict_['FIELD_DICT']!=None:  
            
            if dict_['inst_num'] in [0,1]:
                print(f"Register: {dict_['name']}")
                reg_B = Register(name=dict_['name'], bit=dict_['width'], description=dict_['doc'])
                # reg_B = Register(name=dict_['name'], bit=dict_['width'])
                reg_B_copy = build_field_recur(dict_['FIELD_DICT'], reg_B, tcl_interpreter)
                if reg_B_copy!=-1:
                    father_copy.add(sub_space=reg_B_copy,offset=int(dict_['addr']))

            else:
                # neo_dict = {}
                # idx = 0
                # for key, value in dict_['FIELD_DICT'].items():
                #     name = dict_['name']+f'_{idx}'
                #     if name not in neo_dict.keys(): neo_dict[name]={}
                #     neo_dict[name] = value
                #     if (int(value['addr'])+int(value['bits']))==32: idx += 1

                # for i in range(int(dict_['inst_num'])+1):
                #     name = dict_['name']+f'_{i}'
                #     reg_B = Register(name=name)
                #     if name not in neo_dict.keys():
                #         reg_B_copy = build_field_recur(neo_dict[dict_['name']+f'_{i-1}'], reg_B, tcl_interpreter)
                #     else:
                #         reg_B_copy = build_field_recur(neo_dict[dict_['name']+f'_{i}'], reg_B, tcl_interpreter)
                #     father_copy.add(sub_space=reg_B_copy,offset=int(dict_['addr'])+i*4)

                for i in range(int(dict_['inst_num'])):
                    name = dict_['name']+f'_{i}'
                    reg_B = Register(name=name)
                    reg_B_copy = build_field_recur(dict_['FIELD_DICT'], reg_B, tcl_interpreter)
                    father_copy.add(sub_space=reg_B_copy,offset=int(dict_['addr'])+i*4)
                # print('====',father_copy.module_name,father_copy.__dict__)
            
        # recur addr dict
        if dict_['ADDR_DICT']!=None:  
            # print(f"AddrSpace: {dict_['name']}")
            reg_bank_B = RegSpace(name=dict_['name'], size=64*MB,bus_width=32,software_interface='apb')
            reg_bank_B_copy = build_subspace_recur(dict_['ADDR_DICT'], reg_bank_B, tcl_interpreter)
            
            if isinstance(father_copy, RegSpace):   father_copy = AddressSpace(name=father_copy.module_name, size=1e20*GB)
            father_copy.add(sub_space=reg_bank_B_copy, name=dict_['name'], offset=int(dict_['addr']))

    return father_copy
        

def build_field_recur(dict_, father, tcl_interpreter):
    with phase("ralf.deepcopy"):
        owned = deepcopy(father)
    return _build_field_inplace(dict_, owned, tcl_interpreter)


def _build_field_inplace(dict_, father_copy, tcl_interpreter):
    if 'name' not in dict_.keys():  
        for key in dict_.keys():    father_copy = _build_field_inplace(dict_[key], father_copy, tcl_interpreter)
    else:
        from ..Field    import Field
        sw_access = get_field_access_by_value(dict_['access'])
        if "Reserve" not in dict_['name']:
            father_copy.add(Field(name=dict_['name'],bit=int(dict_['bits']),sw_access=sw_access, init_value=int(dict_['reset']), description=dict_['doc']),offset=int(dict_['addr']))
            # father_copy.add(Field(name=dict_['name'],bit=int(dict_['bits']),sw_access=sw_access, init_value=int(dict_['reset'])),offset=int(dict_['addr']))
        else:
            father_copy.add(Field(name=dict_['name'],bit=int(dict_['bits']),sw_access=sw_access, init_value=int(dict_['reset']), description=dict_['doc']),offset=int(dict_['addr']))
            # father_copy.add(Field(name=dict_['name'],bit=int(dict_['bits']),sw_access=sw_access, init_value=int(dict_['reset'])),offset=int(dict_['addr']))
    
    return father_copy
    




















def tcl_dict_recur(key_list, dict_, tcl_dict, tcl_interpreter, father=None):
    # print('---------------------')
    for key in key_list:
        tcl_dict_tmp = f'{tcl_dict} {key}'
        # print('---', tcl_dict_tmp)
        value = tcl_interpreter.eval(f'set value [dict get {tcl_dict_tmp}]')

        # update py_dict
        if    (key == 'FIELD_DICT' or key == 'ADDR_DICT') and value=='':  dict_[key]=None
        elif  key == 'FIELD_DICT' and value!='':  
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_field(keys_dict.split(' '), dict_[key], tcl_dict_tmp, tcl_interpreter, father)
        elif  key == 'ADDR_DICT' and value!='':  
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_recur(keys_dict.split(' '), dict_[key], tcl_dict_tmp, tcl_interpreter, dict_)
        elif  key == 'addr':                                              dict_[key] = convert_address_with_context(value, tcl_dict_tmp)
        elif  key == 'name':                                              dict_[key] = value
        elif  key == 'inst_num':                                          dict_[key] = int(value)
        elif  key == 'size':                                              dict_[key] = convert_address_with_context(value, tcl_dict_tmp)
        elif  key == "is_memory":                                         dict_[key] = value
        elif  key == "width":                                             dict_[key] = int(value)*8
        elif  key == 'doc':                                               dict_[key] = value
        else:
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_recur(keys_dict.split(' '), dict_[key], tcl_dict_tmp, tcl_interpreter, father)  
    

def tcl_dict_field(key_list, dict_, tcl_dict, tcl_interpreter, father=None):
    for key in key_list:
        tcl_dict_tmp = f'{tcl_dict} {key}'
        # print('===', tcl_dict_tmp)
        value = tcl_interpreter.eval(f'set value [dict get {tcl_dict_tmp}]')

        # update py_dict
        if 'name' not in key_list:
            keys_dict = tcl_interpreter.eval('set keys [dict keys $value]')
            dict_[key] = {}
            tcl_dict_field(keys_dict.split(' '), dict_[key], tcl_dict_tmp, tcl_interpreter, father)
        elif  key == 'addr':        dict_[key] = convert_address_with_context(value, tcl_dict_tmp)
        elif  key == 'reset':       dict_[key]=convert_reset(value)
        elif  key == 'doc':         dict_[key] = value
        # elif key == 'doc':        print(dict_)
        else:                       dict_[key]=value 


def convert_address(address):
    clean_address = str(address).strip().replace("@", "").replace("_", "")
    if not clean_address:
        raise ValueError("address is empty")

    # Some intranet RALF producers combine Verilog and C hex prefixes.
    normalized = clean_address.lower().replace("'h0x", "'h")

    # Standard prefixes must be recognized before legacy h/b markers.  A
    # character such as the 'b' in 0xfb4 is a hexadecimal digit, not a binary
    # radix marker.
    if normalized.startswith('0x'):
        return int(normalized[2:], 16)
    if normalized.startswith('0b'):
        return int(normalized[2:], 2)

    # Retain the historical RALF/Verilog spellings: 32'h100, 'h100, h100,
    # 32h100 and their binary/decimal equivalents.  Requiring a full-string
    # match prevents a radix letter embedded in a hexadecimal value from being
    # interpreted as a marker.
    radix_match = re.fullmatch(
        r"(?:[0-9]+)?'?(?P<radix>[hbd])(?P<number>[0-9a-f]+)",
        normalized,
    )
    if radix_match:
        base = {'h': 16, 'b': 2, 'd': 10}[radix_match.group('radix')]
        return int(radix_match.group('number'), base)

    return int(clean_address, 10)
    
    
def convert_reset(reset):
    mb = re.match('([0-9]*)(\'[bB])([01_]+)'        ,reset)
    md = re.match('([0-9]*)(\'[dD])([0-9_]+)'       ,reset)
    mh = re.match('([0-9]*)(\'[hH])([0-9a-fA-F_]+)' ,reset)

    if mb:      value = int(mb.group(3).replace('_',''),2)
    elif md:    value = int(md.group(3).replace('_',''),10)
    elif mh:    value = int(mh.group(3).replace('_',''),16)
    else:       value = int(reset)
    
    return value


def minimum_size(father):
    with phase("ralf.deepcopy"):
        owned = deepcopy(father)
    return _minimum_size_inplace(owned)


def _minimum_size_inplace(father_copy):
    from ..Reg import Register
    if father_copy.sub_space_list != []:
        end_element   = max(father_copy.sub_space_list, key=lambda element: element.bit_offset)
        start_element = min(father_copy.sub_space_list, key=lambda element: element.bit_offset)
    else: return father_copy
    if isinstance(end_element,Register):    father_copy.size=int(end_element.offset/8+end_element.bit/8-start_element.start_address/8)
    else:                                   father_copy.size=end_element.offset+end_element.size
    return father_copy
