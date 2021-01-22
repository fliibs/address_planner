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
    ReadWrite   = 'Read Write'

ReadOnly  = FieldSoftwareAccess.ReadOnly
WriteOnly = FieldSoftwareAccess.WriteOnly
ReadWrite = FieldSoftwareAccess.ReadWrite


@unique
class FieldSoftwareEffect(Enum):
    NoEffect    = 'No Effect'
    ClearField  = 'Clear Field'
    GenPulse    = 'Generate Pulse'

NoEffect    = FieldSoftwareEffect.NoEffect
ClearField  = FieldSoftwareEffect.ClearField
GenPulse    = FieldSoftwareEffect.GenPulse

@unique
class FieldHardwareType(Enum):
    Unknown           = 'Unknown'
#    ExternalReadOnly  = 'External Read Only'
#    ExternalWriteOnly = 'External Write Only'
#    ExternalReadWrite = 'External Read Write'

Unknown           = FieldHardwareType.Unknown
#ExternalReadOnly  = FieldHardwareType.ExternalReadOnly
#ExternalWriteOnly = FieldHardwareType.ExternalWriteOnly
#ExternalReadWrite = FieldHardwareType.ExternalReadWrite


def ADD_TO_GLOBAL_VALUES(**kwargs):
    gbl = globals()
    for k,v in kwargs.items():
        gbl[k] = v

def ADD_TO_FIELD_HARDWARE_TYPE(**kwargs):
    for k,v in kwargs.items():
        setattr(FieldHardwareType,k,v)