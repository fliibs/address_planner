from enum   import Enum,unique

APG_BUS_WIDTH = 32
APG_HTML_FILE_ADDR_SPACE    = 'addr_space_html.j2'
APG_HTML_FILE_REG_SPACE     = 'reg_space_html.j2'
APG_VHEAD_FILE_ADDR_SPACE   = 'addr_space_head.j2'
APG_VHEAD_FILE_REG_SPACE    = 'reg_space_head.j2'
APG_CHEAD_FILE_ADDR_SPACE   = 'addr_space_head.j2'
APG_CHEAD_FILE_REG_SPACE    = 'reg_space_head.j2'

KB = 1024
MB = 1024 * 1024
GB = 1024 * 1024 * 1024

@unique
class FieldSoftwareAccess(Enum):
    ReadOnly    = 'Read Only'
    WriteOnly   = 'Write Only'
    # WriteOnce   = 'Write One to Set'
    ReadWrite   = 'Read Write'
    # ReadClean   = 'Read Clean'
    Null        = 'Null'

ExternalReadOnly  = FieldSoftwareAccess.ReadOnly
ExternalWriteOnly = FieldSoftwareAccess.WriteOnly
ExternalReadWrite = FieldSoftwareAccess.ReadWrite
# ExternalReadClean = FieldSoftwareAccess.ReadClean
ExternalNull      = FieldSoftwareAccess.Null


@unique
class FieldEffect(Enum):
    NoEffect    = 'No Effect'
    # ClearField  = 'Clear Field'
    GenPulse    = 'Generate Pulse'
    WriteOnce   = 'Write One to Set'
    ReadClean   = 'Read Clean'

NoEffect    = FieldEffect.NoEffect
# ClearField  = FieldEffect.ClearField
GenPulse    = FieldEffect.GenPulse
WriteOnce   = FieldEffect.WriteOnce
ReadClean   = FieldEffect.ReadClean

@unique
class FieldHardwareType(Enum):
    ReadOnly  = 'Read Only'
    WriteOnly = 'Write Only'
    ReadWrite = 'Read Write'
    Null      = 'Null'

InternalReadOnly  = FieldHardwareType.ReadOnly
InternalWriteOnly = FieldHardwareType.WriteOnly
InternalReadWrite = FieldHardwareType.ReadWrite
InternalNull      = FieldHardwareType.Null


def ADD_TO_GLOBAL_VALUES(**kwargs):
    gbl = globals()
    for k,v in kwargs.items():
        gbl[k] = v

def ADD_TO_FIELD_HARDWARE_TYPE(**kwargs):
    for k,v in kwargs.items():
        setattr(FieldHardwareType,k,v)