import os,sys
import importlib
from enum   import Enum,unique

APG_BUS_WIDTH = 32
APG_DATA_WIDTH = APG_BUS_WIDTH
APG_ADDR_WIDTH = 32
APG_HTML_FILE_ADDR_SPACE            = 'addr_space_html.j2'
APG_HTML_FILE_REG_SPACE             = 'reg_space_html.j2'
APG_VHEAD_FILE_ADDR_SPACE           = 'addr_space_head.j2'
APG_VHEAD_FILE_REG_SPACE            = 'reg_space_head.j2'
APG_CHEAD_FILE_ADDR_SPACE           = 'addr_space_head.j2'
APG_CHEAD_FILE_REG_SPACE            = 'reg_space_head.j2'
APG_ADDR_RMODEL_FILE_REG_SPACE      = 'ral_model.j2'
APG_ADDR_RMDEFINE_FILE_REG_SPACE    = 'addr_ral_model_define.j2'
APG_ADDR_RMCSV_FILE_REG_SPACE       = 'addr_ral_model_csv.j2'
APG_REG_RMODEL_FILE_REG_SPACE       = 'ral_model.j2'
APG_REG_RMDEFINE_FILE_REG_SPACE     = 'reg_ral_model_define.j2'
APG_REG_RMCSV_FILE_REG_SPACE        = 'reg_ral_model_csv.j2'
APG_REG_RALF_FILE_REG_SPACE         = 'ralf.j2'

KB = 1024 * 8
MB = 1024 * 1024 * 8
GB = 1024 * 1024 * 1024

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


@unique
class RegType(Enum):
    Normal = 'Normal'

Normal = RegType.Normal


key = 0

def ADD_KEY():
    global key 
    key = key + 1
    return key

def ConvertSize(size):
    if size/8 > KB-1:
        return "%.1fKB"% float(size / KB /8)
    elif size/8 > MB-1:
        return "%.1fMB"% float(size / MB/8)
    elif size/8 > GB-1:
        return "%.1fGB"% float(size / GB/8)
    elif size/8 >=1:
        return "%dB"% int(size/8)
    else:
        return "%db"% size

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


def import_inst(file_path, module_name):
    dir_path, file_name = os.path.split(file_path)
    file_name = file_name.rstrip('.py')

    dir_path = dir_path.strip('/').replace('/','.')
    try:
        res = importlib.import_module(dir_path+'.'+file_name, package=__package__)
        print("[package import execute]: from %s.%s import %s"% (dir_path, file_name, module_name))
        res = getattr(res, module_name)
        return res
    except ImportError as err:
        print("[ImportError]", err)

    
    
    # if var_list is not None: pattern = ','.join(var_list)
    # if var_list is None:
    #     print("[package import execute]: from %s import *"% file_name)
    #     exec('from %s import *'% file_name, GlobalValue.globals)
    # else:
    #     print("[package import execute]: from %s import %s"% (file_name, pattern))
    #     exec('from %s import %s'% (file_name, pattern), GlobalValue.globals)
    


# def ADD_TO_FIELD_HARDWARE_TYPE(**kwargs):
#     for k,v in kwargs.items():
#         setattr(FieldHardwareType,k,v)
