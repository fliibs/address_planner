import os
import sys

from address_planner import * # pylint: disable=unused-wildcard-import


def test_external_apb():

    reg_bank_C = RegSpace(name='external',size=1*KB,description='reg_bank_B,contain many regs.', software_interface='apb')
    reg_B = Register(name='regB',bit=32,description='contain many fields.')

    reg_B.add_incr(ExternalField(name='field1',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,ext write only.'))
    reg_B.add(ExternalField(name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=2)
    reg_B.add(ExternalField(name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=4)

    reg_bank_C.add_incr(reg_B,'reg0')
    reg_bank_C.add(reg_B,32,'reg1')
    reg_bank_C.report_rtl()


def test_external_vr():

    reg_bank_C = RegSpace(name='external',size=1*KB,description='reg_bank_B,contain many regs.', software_interface='vr')
    reg_B = Register(name='regB',bit=32,description='contain many fields.')

    reg_B.add_incr(ExternalField(name='field1',bit=1,sw_access=ReadWrite,hw_access=ReadWrite,description='fied0,ext write only.'))
    reg_B.add(ExternalField(name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=2)
    reg_B.add(ExternalField(name='field3',bit=3,sw_access=ReadOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=4)

    reg_bank_C.add_incr(reg_B,'reg0')
    reg_bank_C.add(reg_B,32,'reg1')
    reg_bank_C.report_rtl()


if __file__ == '__main__':
    test_external_vr()
    test_external_apb()