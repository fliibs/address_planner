import os,sys 
sys.path.append(os.getcwd())
from address_planner import * # pylint: disable=unused-wildcard-import

res = \
AddressSpace                (name="address_space_test", size=10*KB) \
    .regspace               (name='reg_bank_tables_3',size=1*KB,description='reg_bank_B,contain few reg.', software_interface="apb", offset=1*KB)\
        .register           (name='internal_reg',       bit=32,description='contain many fields.', offset=32) \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.', offset=0) \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
        .end\
        .register           (name='internal_reg_2',       bit=32,description='contain many fields.', offset=96) \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.', offset=0) \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
        .end \
    .end\
    .regspace               (name='reg_bank_tables_4',size=1*KB,description='reg_bank_B,contain few reg.', software_interface="apb", offset=2*KB)\
        .register           (name='internal_reg',       bit=32,description='contain many fields.', offset=32) \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.', offset=0) \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
        .end\
        .register           (name='internal_reg_2',       bit=32,description='contain many fields.', offset=96) \
            .field          (name='field0',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.', offset=0) \
            .field          (name='field1',     bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=5)\
        .end \
    .end

res.generate('build/example')


