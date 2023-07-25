import os,sys
from enum   import Enum,unique

APG_BUS_WIDTH = 32
APG_DATA_WIDTH = APG_BUS_WIDTH
APG_ADDR_WIDTH = 16
APG_HTML_FILE_ADDR_SPACE    = 'addr_space_html.j2'
APG_HTML_FILE_REG_SPACE     = 'reg_space_html.j2'
APG_VHEAD_FILE_ADDR_SPACE   = 'addr_space_head.j2'
APG_VHEAD_FILE_REG_SPACE    = 'reg_space_head.j2'
APG_CHEAD_FILE_ADDR_SPACE   = 'addr_space_head.j2'
APG_CHEAD_FILE_REG_SPACE    = 'reg_space_head.j2'

KB = 1024
MB = 1024 * 1024
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
    Null            = 'Null'
    ReadWrite       = 'Read Write'
    ReadCleanWrite  = 'ReadClean Write'
    ReadSetWrite    = 'ReadSet Write'

    ReadOnly        = 'Read Only'
    ReadClean       = 'Read Clean'
    ReadSet         = 'Read Set'

    WriteOnly       = 'Write Only'
    WriteClean      = 'Write Clean'
    Write1Clean     = 'Write 1 Clean'
    Write0Clean     = 'Write 0 Clean'
    WriteSet        = 'Write Set'
    Write1Set       = 'Write 1 Set'
    Write0Set       = 'Write 0 Set'
    Write1Toggle    = 'Write 1 Toggle'
    Write0Toggle    = 'Write 0 Toggle'
    
    
Null            = FieldAccess.Null
ReadWrite       = FieldAccess.ReadWrite
ReadOnly        = FieldAccess.ReadOnly
ReadClean       = FieldAccess.ReadClean
ReadCleanWrite  = FieldAccess.ReadCleanWrite
ReadSet         = FieldAccess.ReadSet
ReadSetWrite    = FieldAccess.ReadSetWrite

WriteOnly       = FieldAccess.WriteOnly
WriteClean      = FieldAccess.WriteClean
Write1Clean     = FieldAccess.Write1Clean  
Write0Clean     = FieldAccess.Write0Clean
WriteSet        = FieldAccess.WriteSet
Write1Set       = FieldAccess.Write1Set
Write0Set       = FieldAccess.Write0Set
Write1Toggle    = FieldAccess.Write1Toggle
Write0Toggle    = FieldAccess.Write0Toggle



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


def import_inst(file_path, var_list=None):
    split_list = file_path.rsplit("/",1)
    if len(split_list) > 1:
        dir_path = split_list[0]
        file_name = split_list[-1].rsplit(".")[0]
        sys.path.append(dir_path)
    else:
        file_name = split_list[-1].rsplit(".")[0]
    
    if var_list is not None: pattern = ','.join(var_list)
    # exec('from %s import *'% file_name) if var_list is None else exec('from %s import %s'% (file_name, pattern))
    if var_list is None:
        print("[package import execute]: from %s import *"% file_name)
        exec('from %s import *'% file_name, GlobalValue.globals)
    else:
        print("[package import execute]: from %s import %s"% (file_name, pattern))
        exec('from %s import %s'% (file_name, pattern), GlobalValue.globals)
    


# def ADD_TO_FIELD_HARDWARE_TYPE(**kwargs):
#     for k,v in kwargs.items():
#         setattr(FieldHardwareType,k,v)


if __name__=="__main__":
    import_inst('address_planner')
    import_inst('/home/stevenhuang/Desktop/addressplanner_workplace/address_planner/example/ip1/regspace_demo_1.py',['RS_1', 'RS_2'])
    