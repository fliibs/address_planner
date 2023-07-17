
from address_planner import *


reg_bank_B = RegSpace(name='reg_bank_B',size=1*KB,description='reg_bank_B,contain many regs.')



reg_bank_B.add_incr([
    Register(
        name='regB',
        bit=32,
        description='contain many fields.'),
        field = [
            Field(
                name='field0',
                bit=1,
                description="asdfasdf"
            ),
            Field(
                name='field1',
                bit=1,
                description='asdfasdf'
            )],
    Register(

    ),
    Register(

    )]
    )



