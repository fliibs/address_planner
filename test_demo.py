
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
            .field          (name='field4',     bit=4,sw_access=ReadWrite,hw_access=WriteOnly,description='fied4, hardware write only.', offset=11)\
            .field          (name='field5',     bit=8,sw_access=ReadWrite,hw_access=ReadWrite,description='fied5, hardware read write.', offset=15)\
            .field          (name='field6',     bit=1,sw_access=ReadOnly, hw_access=ReadWrite,description='fied0, software read only.' , offset=24) \
            .field          (name='field7',     bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied1, software write only.', offset=26) \
            .field          (name='field8',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, software read write.', offset=27)\
            .field          (name='field9',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied3, hardware read only.' , offset=28)\
            .field          (name='field10',    bit=1,sw_access=ReadWrite,hw_access=WriteOnly,description='fied4, hardware write only.', offset=29)\
            .field          (name='field11',    bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied5, hardware read write.', offset=30)\
        .end\
        .register           (name='external_reg',       bit=32,description='contain many fields.')\
            .external_field (name='field0',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied0, external hardware read only.')\
            .external_field (name='field1',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied1, external hardware write only.', offset=3)\
            .external_field (name='field2',     bit=3,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, external hardware read write.', offset=5)\
            .external_field (name='field3',     bit=4,sw_access=ReadWrite,hw_access=ReadOnly, description='fied3, external hardware read only.' , offset=8)\
            .external_field (name='field4',     bit=2,sw_access=ReadWrite,hw_access=ReadOnly, description='fied4, external hardware write only.', offset=12)\
            .external_field (name='field5',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied5, external hardware read write.', offset=16)\
            .external_field (name='field6',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied0, external hardware read only.' , offset=17)\
            .external_field (name='field7',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied1, external hardware write only.', offset=18)\
            .external_field (name='field8',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, external hardware read write.', offset=19)\
            .external_field (name='field9',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied3, external hardware read only.' , offset=20)\
            .external_field (name='field10',    bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied4, external hardware write only.', offset=21)\
            .external_field (name='field11',    bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied5, external hardware read write.', offset=22)\
            .external_field (name='field12',    bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied0, external hardware read only.' , offset=23)\
            .external_field (name='field13',    bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied1, external hardware write only.', offset=24)\
            .external_field (name='field14',    bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, external hardware read write.', offset=25)\
            .external_field (name='field15',    bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied3, external hardware read only.' , offset=26)\
            .external_field (name='field16',    bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied4, external hardware write only.', offset=27)\
            .external_field (name='field17',    bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied5, external hardware read write.', offset=28)\
            .external_field (name='field18',    bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied1, external hardware write only.', offset=29)\
            .external_field (name='field19',    bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied2, external hardware read write.', offset=30)\
            .external_field (name='field20',    bit=1,sw_access=ReadWrite,hw_access=ReadOnly, description='fied3, external hardware read only.' , offset=31)\
        .end \
        .register           (name='sw_no_write_reg_1',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=9)\
            .external_field (name='field5',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=13)\
            .field          (name='field6',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=14)\
            .field          (name='field7',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=16)\
            .field          (name='field8',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=19)\
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
            .external_field (name='field5',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=13)\
            .field          (name='field6',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=14)\
            .field          (name='field7',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=16)\
            .field          (name='field8',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=19)\
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
        .register           (name='sw_no_write_reg_3',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=9)\
            .external_field (name='field5',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=13)\
            .field          (name='field6',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=14)\
            .field          (name='field7',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=16)\
            .field          (name='field8',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=19)\
        .end \
        .register           (name='sw_no_read_reg_3',bit=32,description='contain many fields.')\
            .external_field (name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,external write only.')\
            .field          (name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=2)\
            .field          (name='field3',bit=3,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=4)\
            .field          (name='field4',bit=4,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=8)\
        .end \
        .register           (name='read_clean_reg_3',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,external read clean.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=9)\
        .end \
        .register           (name='sw_no_write_reg_4',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=9)\
            .external_field (name='field5',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=13)\
            .field          (name='field6',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=14)\
            .field          (name='field7',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=16)\
            .field          (name='field8',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=19)\
        .end \
        .register           (name='sw_no_read_reg_4',bit=32,description='contain many fields.')\
            .external_field (name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,external write only.')\
            .field          (name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=2)\
            .field          (name='field3',bit=3,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=4)\
            .field          (name='field4',bit=4,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=8)\
        .end \
        .register           (name='read_clean_reg_4',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,external read clean.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadClean,hw_access=ReadWrite,description='fied0,internal read clean.',offset=9)\
        .end \
        .register           (name='sw_no_write_reg_5',bit=32,description='contain many fields.')\
            .reserved_field (bit=2)\
            .external_field (name='field1',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=2)\
            .field          (name='field2',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=3)\
            .field          (name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=5)\
            .field          (name='field4',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=9)\
            .external_field (name='field5',bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, external read only.',offset=13)\
            .field          (name='field6',bit=2,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=14)\
            .field          (name='field7',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=16)\
            .field          (name='field8',bit=4,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0, internal read only.',offset=19)\
        .end \
        .register           (name='sw_no_read_reg_5',bit=32,description='contain many fields.')\
            .external_field (name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,external write only.')\
            .field          (name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=2)\
            .field          (name='field3',bit=3,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=4)\
            .field          (name='field4',bit=4,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,internal write only.',offset=8)\
        .end \
        .register           (name='read_clean_reg_5',bit=32,description='contain many fields.')\
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

