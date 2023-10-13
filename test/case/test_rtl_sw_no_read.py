import sys
sys.path.append('.')
from address_planner import * # pylint: disable=unused-wildcard-import


def test_sw_no_read_apb():

    reg_bank_C = RegSpace(name='sw_no_read',size=1*KB,description='reg_bank_B,contain many regs.', software_interface='apb')
    reg_B = Register(name='regB',bit=32,description='contain many fields.')

    reg_B.add_incr(ExternalField(name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'))
    reg_B.add(Field(name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=2)
    reg_B.add(Field(name='field3',bit=3,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=4)
    reg_B.add(Field(name='field4',bit=4,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=8)

    reg_bank_C.add_incr(reg_B,'reg0')
    reg_bank_C.add(reg_B,32,'reg1')
    reg_bank_C.generate('build/test')


def test_sw_no_read_vr():

    reg_bank_C = RegSpace(name='sw_no_read',size=1*KB,description='reg_bank_B,contain many regs.', software_interface='vr')
    reg_B = Register(name='regB',bit=32,description='contain many fields.')

    reg_B.add_incr(ExternalField(name='field1',bit=1,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'))
    reg_B.add(Field(name='field2',bit=2,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=2)
    reg_B.add(Field(name='field3',bit=3,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=4)
    reg_B.add(Field(name='field4',bit=4,sw_access=WriteOnly,hw_access=ReadWrite,description='fied0,ext write only.'),offset=8)

    reg_bank_C.add_incr(reg_B,'reg0')
    reg_bank_C.add(reg_B,32,'reg1')
    reg_bank_C.generate('build/example')

if __file__ == '__main__':
    test_sw_no_read_vr()
    test_sw_no_read_apb()
    