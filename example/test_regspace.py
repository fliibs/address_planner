import os,sys 
sys.path.append(os.getcwd())
from address_planner import * # pylint: disable=unused-wildcard-import

RegSpace                    (name='reg_bank_tables',size=1*KB,description='reg_bank_B,contain many regs.', software_interface="apb")  \
        .register           (name='internal_reg',       bit=32,description='contain many fields.') \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.') \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
            .field          (name='field3',     bit=3,sw_access=ReadWrite,hw_access=ReadOnly, description='fied3, hardware read only.' , offset=7)\
        .end\
        .register           (name='external_reg',       bit=32,description='contain many fields.')\
            .external_field (name='field0',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied0, external hardware read only.')\
            .external_field (name='field1',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied1, external hardware write only.', offset=3)\
            .external_field (name='field2',     bit=3,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, external hardware read write.', offset=5)\
            .external_field (name='field3',     bit=4,sw_access=ReadWrite,hw_access=ReadOnly, description='fied3, external hardware read only.' , offset=8)\
        .end \
    .generate