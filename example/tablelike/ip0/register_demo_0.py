from address_planner import * # pylint: disable=unused-wildcard-import

R_0 = Register(name='read_clean_reg_5',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,external read clean.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=9)

R_1 = Register(name='sw_no_read_reg_5',bit=32,description='contain many fields.')\
            .external_field (name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,external write only.')\
            .field          (name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=2)\
            .field          (name='field3',bit=3,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=4)\
            .field          (name='field4',bit=4,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=8)
