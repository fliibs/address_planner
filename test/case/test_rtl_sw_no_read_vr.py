
import os
import sys

from address_planner import * # pylint: disable=unused-wildcard-import


def test_sw_no_read_vr():

    reg_bank_C = RegSpace(name='reg_bank_C',size=1*KB,description='reg_bank_B,contain many regs.', external_interface='vr')
    reg_B = Register(name='regB',bit=32,description='contain many fields.')

    reg_B.add_incr(FieldExternalWriteOnly(name='field1',bit=1,description='fied0,ext write only.'))
    reg_B.add(FieldExternalWriteOnly(name='field2',bit=2,description='fied0,ext write only.'),offset=2)
    reg_B.add(FieldExternalWriteOnly(name='field3',bit=3,description='fied0,ext write only.'),offset=4)
    reg_B.add(FieldExternalWriteOnly(name='field4',bit=4,description='fied0,ext write only.'),offset=8)

    reg_bank_C.add_incr(reg_B,'reg0')
    reg_bank_C.add(reg_B,32,'reg1')
    reg_bank_C.report_rtl()


if __file__ == '__main__':
    test_sw_no_read_vr()
