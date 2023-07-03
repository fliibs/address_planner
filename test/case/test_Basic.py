

from address_planner import * # pylint: disable=unused-wildcard-import
import address_planner
import sys
sys.path.append('./submodules')

def test_smoke():
    assert True

def test_AddrSpace():
    ip_A = AddressSpace(name='ip_A',size=4*KB,description='ip_A,contains mem_A0 and mem_A1.')

    mem_A = AddressSpace(name='mem_A',size=1*KB,description='mem_A,size 1KB.')

    ip_A.add(mem_A,name='mem_A0',offset=0*KB)

def test_Register():

    # declare reg bank for ip_B
    reg_bank_B = RegSpace(name='reg_bank_B',size=1*KB,description='reg_bank_B,contain many regs.')

    # declare reg_B
    reg_B = Register(name='regB',bit=32,description='contain many fields.')
    # add many field to reg_B
    reg_B.add_incr(FieldExternalReadOnly(name='field0',bit=1,description='fied0,ext read only.'))
    reg_B.add_incr(FieldExternalWriteOnly(name='field1',bit=1,description='fied0,ext write only.'))
    reg_B.add_incr(FieldExternalReadWrite(name='field2',bit=1,description='fied0,ext read write.'))
    reg_B.add_incr(FieldReadOnly(name='field3',bit=1,description='fied0,read only.'))
    reg_B.add_incr(FieldWriteOnly(name='field4',bit=1,description='fied0,write only.'))
    reg_B.add_incr(FieldReadWrite(name='field5',bit=1,description='fied0,read write.'))

    #add reg0 and reg1(inst from reg_B) to reg_bank_B
    reg_bank_B.add_incr(reg_B,'reg0')
    reg_bank_B.add_incr(reg_B,'reg1')


def test_Top():
    # declare ip_A with 4KB space.
    ip_A = AddressSpace(name='ip_A',size=4*KB,description='ip_A,contains mem_A0 and mem_A1.')  

    # declare type mem_A with 1KB space
    mem_A = AddressSpace(name='mem_A',size=1*KB,description='mem_A,size 1KB.')

    # add mem_A0 and mem_A1(inst from mem_A) to ip_A
    ip_A.add(mem_A,name='mem_A0',offset=0*KB)
    ip_A.add(mem_A,name='mem_A1',offset=2*KB)



    ###################################################
    # Define ip_B
    #
    #   ip_B contains a mem and a reg space
    ###################################################

    # declare ip_B with 4KB space.
    ip_B = AddressSpace(name='ip_B',size=4*KB,description='ip_B,contains mem_B and reg_bank_B.')  

    # declare mem_B with 2KB space
    mem_B = AddressSpace(name='mem_B',size=2*KB,description='mem_B,size 2KB.')

    # declare reg bank for ip_B
    reg_bank_B = RegSpace(name='reg_bank_B',size=1*KB,description='reg_bank_B,contain many regs.')

    # declare reg_B
    reg_B = Register(name='regB',bit=32,description='contain many fields.')
    # add many field to reg_B
    reg_B.add_incr(FieldExternalReadOnly(name='field0',bit=1,description='fied0,ext read only.'))
    reg_B.add_incr(FieldExternalWriteOnly(name='field1',bit=1,description='fied0,ext write only.'))
    reg_B.add_incr(FieldExternalReadWrite(name='field2',bit=1,description='fied0,ext read write.'))
    reg_B.add_incr(FieldReadOnly(name='field3',bit=1,description='fied0,read only.'))
    reg_B.add_incr(FieldWriteOnly(name='field4',bit=1,description='fied0,write only.'))
    reg_B.add_incr(FieldReadWrite(name='field5',bit=1,description='fied0,read write.'))

    #add reg0 and reg1(inst from reg_B) to reg_bank_B
    reg_bank_B.add_incr(reg_B,'reg0')
    reg_bank_B.add_incr(reg_B,'reg1')

    ip_B.add(mem_B,name='mem',offset=0*KB)
    ip_B.add(reg_bank_B,name='reg',offset=2*KB)

    ###################################################
    # Define ip_C
    #
    #   ip_C has not been implemented yet, leaving only a space of 8KB
    ###################################################

    # declare ip_C with 8KB space.
    ip_C = AddressSpace(name='ip_C',size=8*KB,description='ip_C,only a space of 8KB.')  


    ###################################################
    # Define sys0
    #
    #   contains ip_A,ip_B,ip_C
    ###################################################

    # declare sys0 with 3MB space.
    sys0 = AddressSpace(name='sys0',size=3*MB,description='sys0.')
    sys0.add(ip_A,name='ip_A',offset=0*MB)
    sys0.add(ip_B,name='ip_B',offset=1*MB)
    sys0.add(ip_C,name='ip_C',offset=2*MB)


    ###################################################
    # Define sys1
    #
    #   empty with 1MB space.
    ###################################################

    sys1 = AddressSpace(name='sys1',size=1*MB,description='sys1.')


    ###################################################
    # Define top
    #
    #   cotains sys0 and sys1
    ###################################################

    top = AddressSpace(name='top',size=4*MB,description='demo top.')
    top.add_incr(sys0,name='sys0')
    top.add_incr(sys1,name='sys1')