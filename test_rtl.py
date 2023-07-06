
import os
import sys
sys.path.append('./submodules')

from address_planner import * # pylint: disable=unused-wildcard-import

def test_regbank():

    # declare reg bank for ip_B
    reg_bank_B = RegSpace(name='reg_bank_B',size=1*KB,description='reg_bank_B,contain many regs.')

    # declare reg_B
    reg_B = Register(name='regB',bit=32,description='contain many fields.')
    # add many field to reg_B
    reg_B.add_incr(FieldExternalReadOnly(name='field0',bit=1,description='fied0,ext read only.'))
    reg_B.add(FieldExternalWriteOnly(name='field1',bit=1,description='fied0,ext write only.'),offset=3)
    reg_B.add(FieldExternalReadWrite(name='field2',bit=1,description='fied0,ext read write.'),offset=5)
    reg_B.add(FieldExternalReadWrite(name='field3',bit=1,hw_access=InternalReadOnly,description='fied0,read only.'),offset=7)
    reg_B.add(FieldExternalReadWrite(name='field4',bit=1,hw_access=InternalWriteOnly,description='fied0,write only.'),offset=9)
    reg_B.add(FieldExternalReadWrite(name='field5',bit=1,hw_access=InternalReadWrite,description='fied0,read write.'),offset=11)
    reg_B.add(Field(name='field6',bit=2,sw_read_effect=ReadClean,description='fied0,read clean.'),offset=13)

    #add reg0 and reg1(inst from reg_B) to reg_bank_B
    reg_bank_B.add_incr(reg_B,'reg0')
    reg_bank_B.add_incr(reg_B,'reg1')
    reg_bank_B.report_rtl()

def test_sw_no_read():

    reg_bank_C = RegSpace(name='reg_bank_C',size=1*KB,description='reg_bank_B,contain many regs.')
    reg_B = Register(name='regB',bit=32,description='contain many fields.')

    reg_B.add_incr(FieldExternalWriteOnly(name='field1',bit=1,description='fied0,ext write only.'))
    reg_B.add(FieldExternalWriteOnly(name='field2',bit=2,description='fied0,ext write only.'),offset=2)
    reg_B.add(FieldExternalWriteOnly(name='field3',bit=3,description='fied0,ext write only.'),offset=4)
    reg_B.add(FieldExternalWriteOnly(name='field4',bit=4,description='fied0,ext write only.'),offset=8)

    reg_bank_C.add_incr(reg_B,'reg0')
    reg_bank_C.add(reg_B,32,'reg1')
    reg_bank_C.report_rtl()

def test_sw_no_write():
    reg_bank_D = RegSpace(name='reg_bank_D',size=1*KB,description='reg_bank_B,contain many regs.')
    reg_B = Register(name='regB',bit=32,description='contain many fields.')

    reg_B.add_incr(FilledField(bit=2))
    reg_B.add(FieldExternalReadOnly(name='field1',bit=1,description='fied0,ext write only.'),offset=2)
    reg_B.add(FieldExternalReadOnly(name='field2',bit=2,description='fied0,ext write only.'),offset=3)
    reg_B.add(FieldExternalReadOnly(name='field3',bit=3,description='fied0,ext write only.'),offset=5)
    reg_B.add(FieldExternalReadOnly(name='field4',bit=4,description='fied0,ext write only.'),offset=9)

    reg_bank_D.add_incr(reg_B,'reg0')
    reg_bank_D.add(reg_B,32,'reg1')
    reg_bank_D.report_rtl()



if __name__ == '__main__':
    test_regbank()
    test_sw_no_read()
    test_sw_no_write()