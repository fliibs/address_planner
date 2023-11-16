import os,sys
import importlib.util
from enum   import Enum,unique

APG_BUS_WIDTH = 32
APG_DATA_WIDTH = APG_BUS_WIDTH
APG_ADDR_WIDTH = 32
APG_HTML_FILE_ADDR_SPACE            = 'addr_space_html.j2'
APG_HTML_FILE_REG_SPACE             = 'reg_space_html.j2'
APG_VHEAD_FILE_ADDR_SPACE           = 'addr_space_chead.j2'
APG_VHEAD_FILE_REG_SPACE            = 'reg_space_vhead.j2'
APG_CHEAD_FILE_ADDR_SPACE           = 'addr_space_chead.j2'
APG_CHEAD_FILE_REG_SPACE            = 'reg_space_chead.j2'
APG_ADDR_RMODEL_FILE_REG_SPACE      = 'ral_model.j2'
APG_ADDR_RMDEFINE_FILE_REG_SPACE    = 'addr_ral_model_define.j2'
APG_ADDR_RMCSV_FILE_REG_SPACE       = 'addr_ral_model_csv.j2'
APG_REG_RMODEL_FILE_REG_SPACE       = 'ral_model.j2'
APG_REG_RMDEFINE_FILE_REG_SPACE     = 'reg_ral_model_define.j2'
APG_REG_RMCSV_FILE_REG_SPACE        = 'reg_ral_model_csv.j2'
APG_REG_RALF_FILE_REG_SPACE         = 'ralf.j2'

B  = 1
KB = 1024 * B
MB = 1024 * KB
GB = 1024 * MB

# @unique
# class FieldSoftwareAccess(Enum):
#     ReadOnly    = 'Read Only'
#     WriteOnly   = 'Write Only'
#     ReadWrite   = 'Read Write'
#     Null        = 'Null'

# ExternalReadOnly  = FieldSoftwareAccess.ReadOnly
# ExternalWriteOnly = FieldSoftwareAccess.WriteOnly
# ExternalReadWrite = FieldSoftwareAccess.ReadWrite
# ExternalNull      = FieldSoftwareAccess.Null


# @unique
# class FieldHardwareType(Enum):
#     ReadOnly  = 'Read Only'
#     WriteOnly = 'Write Only'
#     ReadWrite = 'Read Write'
#     Null      = 'Null'

# InternalReadOnly  = FieldHardwareType.ReadOnly
# InternalWriteOnly = FieldHardwareType.WriteOnly
# InternalReadWrite = FieldHardwareType.ReadWrite
# InternalNull      = FieldHardwareType.Null


@unique
class FieldAccess(Enum):
    Null                 = 'reserved'
    ReadWrite            = 'RW'
    ReadOnly             = 'RO'
    ReadClean            = 'RC'
    ReadSet              = 'RS'

    WriteReadClean       = 'WRC'
    WriteReadSet         = 'WRS'
    WriteOnly            = 'WO'
    WriteOnlyClean       = 'WOC'
    WriteOnlySet         = 'WOS'
    WriteClean           = 'WC'
    WriteCleanReadSet    = 'WCRS'
    Write1Clean          = 'W1C'
    Write1CleanReadSet   = 'W1CRS'
    Write0Clean          = 'W0C'
    Write0CleanReadSet   = 'W0CRS'
    WriteSet             = 'WS'
    WriteSetReadClean    = "WSRC"
    Write1Set            = 'W1S'
    Write1SetReadClean   = 'W1SRC'
    Write0Set            = 'W0S'
    Write0SetReadClean   = 'W0SRC'
    Write1Toggle         = 'W1T'
    Write0Toggle         = 'W0T'
    WriteOnce            = 'W1'
    WriteOnlyOnce        = 'WO1'

    Write1Pulse          = 'W1P'
    Write0Pulse          = 'W0P'     
    
    

Null                 = FieldAccess.Null
ReadWrite            = FieldAccess.ReadWrite
ReadOnly             = FieldAccess.ReadOnly
ReadClean            = FieldAccess.ReadClean
ReadSet              = FieldAccess.ReadSet

WriteReadSet         = FieldAccess.WriteReadSet
WriteReadClean       = FieldAccess.WriteReadClean
WriteOnly            = FieldAccess.WriteOnly
WriteOnlyClean       = FieldAccess.WriteOnlyClean
WriteOnlySet         = FieldAccess.WriteOnlySet
WriteClean           = FieldAccess.WriteClean
WriteCleanReadSet    = FieldAccess.WriteCleanReadSet
Write1Clean          = FieldAccess.Write1Clean 
Write1CleanReadSet   = FieldAccess.Write1CleanReadSet 
Write0Clean          = FieldAccess.Write0Clean
Write0CleanReadSet   = FieldAccess.Write0CleanReadSet
WriteSet             = FieldAccess.WriteSet
WriteSetReadClean    = FieldAccess.WriteSetReadClean
Write1Set            = FieldAccess.Write1Set
Write1SetReadClean   = FieldAccess.Write1SetReadClean
Write0Set            = FieldAccess.Write0Set
Write0SetReadClean   = FieldAccess.Write0SetReadClean
Write1Toggle         = FieldAccess.Write1Toggle
Write0Toggle         = FieldAccess.Write0Toggle
WriteOnce            = FieldAccess.WriteOnce
WriteOnlyOnce        = FieldAccess.WriteOnlyOnce

Write1Pulse          = FieldAccess.Write1Pulse
Write0Pulse          = FieldAccess.Write0Pulse


@unique
class RegType(Enum):
    Normal   = 'Normal'
    Magic    = 'Magic'
    Lock     = 'Lock'
    Intr     = 'Interrupt without Mask'
    IntrMask = 'Interrupt with Mask'

Normal      = RegType.Normal
Magic       = RegType.Magic
Lock        = RegType.Lock
Intr        = RegType.Intr
IntrMask    = RegType.IntrMask


@unique
class IntrBitWidth(Enum):
    Intr     = 128
    IntrMask = 160


key = 0

def ADD_KEY():
    global key 
    key = key + 1
    return key

def ConvertSize(size, is_byte=False):
    if is_byte: bit = 1
    else:       bit = 8
        
    if size/bit   > KB-1:
        return "%.1fKB"% float(size / KB / bit)
    elif size/bit > MB-1:
        return "%.1fMB"% float(size / MB / bit)
    elif size/bit > GB-1:
        return "%.1fGB"% float(size / GB / bit)
    elif size/bit >=1:
        return "%dB"% int(size / bit)
    else:
        return "%db"% size
    
def Convert2Byte(size):
    return "%dB"% int(size/8)

# @unique
# class FieldEffect(Enum):
#     NoEffect    = 'No Effect'
#     # ClearField  = 'Clear Field'
#     GenPulse    = 'Generate Pulse'
#     WriteClean  = 'Write Clean'
#     WriteOnce = 'Write One to Set'
#     ReadClean   = 'Read Clean'
#     ReadSet     = 'Read Set'



# NoEffect    = FieldEffect.NoEffect
# # ClearField  = FieldEffect.ClearField
# GenPulse    = FieldEffect.GenPulse
# WriteOnce   = FieldEffect.WriteOnce
# ReadClean   = FieldEffect.ReadClean

@unique
class GlobalValue(Enum):
    globals: None
    locals:  None


def add_scope(**kwargs):
    for k,v in kwargs.items():
        setattr(GlobalValue,k,v)


def ADD_TO_GLOBAL_VALUES(**kwargs):
    gbl = globals()
    for k,v in kwargs.items():
        gbl[k] = v


# def import_inst(file_path, module_name):
#     dir_path, file_name = os.path.split(file_path)
#     file_name = file_name.rstrip('.py')

#     dir_path = dir_path.strip('/').replace('/','.')
#     try:
#         res = importlib.import_module(dir_path+'.'+file_name, package=__package__)
#         print("[package import execute]: from %s.%s import %s"% (dir_path, file_name, module_name))
#         res = getattr(res, module_name)
#         return res
#     except ImportError as err:
#         print("[ImportError]", err)

def import_inst(file_path, module_name='regBank'):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, module_name)
    except ImportError as err:
        print("[ImportError]", err)

def get_full_path(path):
    return os.path.expandvars(path)

    

#### port attribute
class BASE_PORT(object):
    define_dict={
        'rreq_addr' :     'input' ,
        'rreq_vld'  :     'input' ,
        'rreq_rdy'  :     'output',
        'rack_data' :     'output',
        'rack_vld'  :     'output',
        'rack_rdy'  :     'input' ,
        'wreq_addr' :     'input' ,
        'wreq_data' :     'input' ,
        'wreq_vld'  :     'input' ,
        'wreq_rdy'  :     'output' 
    }
    
    def __init__(self):
        pass


class APB_PORT(object):
    define_dict={
        'addr'    :    'input' ,
        'prot'    :    'input' ,
        'sel'     :    'input' ,
        'enable'  :    'input' ,
        'write'   :    'input' ,
        'wdata'   :    'input' ,
        'strb'    :    'input' ,
        'ready'   :    'output',
        'rdata'   :    'output',
        'slverr'  :    'output'
    }

    def __init__(self):
        pass


class EXTERNAL_FIELD(object):
    wr_define_dict={
        'wdat'  :   'output',
        'wvld'  :   'output',
        'wrdy'  :   'input' ,
    }

    rd_define_dict={
        'rdat'  :   'input' ,
        'rvld'  :   'output' ,
        'rrdy'  :   'input'
    }

    def __init__(self):
        pass


class INTERNAL_FIELD(object):
    wr_field_dict={
        'wdat'  :   'input' ,
        'wena'  :   'input' 
    }

    rd_field_dict={
        'rdat'  :   'output',
    }

    rd_extra_field_dict={
        'rdat'  :   'output',
        'rena'  :   'input' 
    }

    def __init__(self):
        pass