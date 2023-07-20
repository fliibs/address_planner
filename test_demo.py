
import os
import sys
sys.path.append('../../..')

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

    RegSpace                (name='reg_bank_tables',size=1*KB,description='reg_bank_B,contain many regs.')  \
        .register           (name='reg0',       bit=32,description='contain many fields.') \
            .field          (name='field0',     bit=1,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0,ext read only.') \
            .field          (name='field1',     bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.',offset=3) \
            .field          (name='field2',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,ext read write.',offset=5)\
        .end\
        .register           (name='reg1',       bit=32,description='contain many fields 2.')\
            .external_field (name='field3',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly,description='fied0,read only.')\
            .external_field (name='field4',     bit=1,sw_access=ReadWrite,hw_access=ReadOnly,description='fied0,read only.', offset=3)\
            .external_field (name='field5',     bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,read write.', offset=5)\
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

