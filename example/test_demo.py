
import os
import sys
sys.path.append('..')

from address_planner import * # pylint: disable=unused-wildcard-import

def test_regbank():

    # declare reg bank for ip_B
    reg_bank_B = RegSpace(name='reg_bank_A',size=1*KB,description='reg_bank_B,contain many regs.')

    # declare reg_B
    reg_B = Register(name='regB',bit=32,description='contain many fields.')
    # add many field to reg_B
    reg_B.add_incr(Field(name='field0',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0,ext read only.'))
    reg_B.add(Field(name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=3)
    reg_B.add(Field(name='field2',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,ext read write.'),offset=5)
    reg_B.add(Field(name='field3',bit=1,sw_access=ReadWrite,hw_access=ReadOnly,description='fied0,read only.'),offset=7)
    reg_B.add(Field(name='field4',bit=1,sw_access=ReadWrite,hw_access=WriteOnly,description='fied0,write only.'),offset=9)
    reg_B.add(Field(name='field5',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,read write.'),offset=11)
    reg_B.add(Field(name='field6',bit=2,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,read clean.'),offset=13)

    #add reg0 and reg1(inst from reg_B) to reg_bank_B
    reg_bank_B.add_incr(reg_B,'reg0')
    reg_bank_B.add_incr(reg_B,'reg1')
    reg_bank_B.report_rtl()

def test():

    RegSpace                (name='reg_bank_tables',size=1*KB,description='reg_bank_B,contain many regs.', software_interface="apb")  \
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
        .register           (name='sw_no_write_reg_1',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=9)\
        .end \
        .register           (name='sw_no_read_reg_1',bit=32,description='contain many fields.')\
            .external_field (name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,external write only.')\
            .field          (name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=2)\
            .field          (name='field3',bit=3,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=4)\
            .field          (name='field4',bit=4,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=8)\
        .end \
        .register           (name='read_clean_reg_1',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,external read clean.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=9)\
        .end \
        .register           (name='sw_no_write_reg_2',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=9)\
        .end \
        .register           (name='sw_no_read_reg_2',bit=32,description='contain many fields.')\
            .external_field (name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,external write only.')\
            .field          (name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=2)\
            .field          (name='field3',bit=3,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=4)\
            .field          (name='field4',bit=4,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=8)\
        .end \
        .register           (name='read_clean_reg_2',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,external read clean.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=9)\
        .end \
        .generate
    

if __name__ == '__main__':
    test()

    # from address_planner.Field import *
    # from address_planner.Reg import *
    # import json

    # flist = []
    # ft = Field(name='field0', bit=1,description='this is field0')
    # jtext = ft.report_json(flist)
    # print(jtext)
    # # jtext = json.dumps(flist,ensure_ascii=False)
    # # print(jtext)

    # rt = Register           (name='reg0',       bit=32,description='contain many fields.') \
    #             .field          (name='field0',     bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0,ext read only.') \
    #             .field          (name='field1',     bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.',offset=3) \
    #             .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,ext read write.',offset=5)


    # rt.report_json(flist)
    # jtext = json.dumps(flist,ensure_ascii=False)
    # print(jtext)

