import os,sys 
sys.path.append(os.getcwd())

from address_planner import * # pylint: disable=unused-wildcard-import

R_3 = Register(name='sw_no_write_reg_5',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=9)\
            .external_field (name='field5',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=13)\
            .field          (name='field6',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=14)\
            .field          (name='field7',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=16)\
            .field          (name='field8',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=19)
