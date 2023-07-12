
import sys

from address_planner import * # pylint: disable=unused-wildcard-import



def test_sw_read_clean_vr():
    reg_bank_D = RegSpace(name='reg_bank_D',size=1*KB,description='reg_bank_B,contain many regs.', external_interface='vr')
    reg_B = Register(name='regB',bit=32,description='contain many fields.')

    reg_B.add_incr(FilledField(bit=2))
    reg_B.add(Field(name='field1',bit=1,sw_read_effect=ReadClean,description='fied0,ext read clean.'),offset=2)
    reg_B.add(Field(name='field2',bit=2,sw_read_effect=ReadClean,description='fied0,ext read clean.'),offset=3)
    reg_B.add(Field(name='field3',bit=3,sw_read_effect=ReadClean,description='fied0,ext read clean.'),offset=5)
    reg_B.add(Field(name='field4',bit=4,sw_read_effect=ReadClean,description='fied0,ext read clean.'),offset=9)

    reg_bank_D.add_incr(reg_B,'reg0')
    reg_bank_D.add(reg_B,32,'reg1')
    reg_bank_D.report_rtl()



if __file__ == '__main__':
    test_sw_read_clean_vr()