from ..uhdl.uhdl import *
from ..GlobalValues import *


class APB3(Bundle):
    def __init__(self, data_width=APG_DATA_WIDTH, addr_width=APG_ADDR_WIDTH):
        super().__init__()
        self.addr_width = addr_width
        self.data_width = data_width
        # self.strb_width = int(self.data_width/8)
        # self.auser = 5
        # self.wuser = 5
        # self.ruser = 5
        # self.buser = 5

        self.addr   = Input(UInt(self.addr_width))
        # self.prot   = Input(UInt(3))
        self.sel    = Input(UInt(1))
        self.enable = Input(UInt(1))
        self.write  = Input(UInt(1))
        self.wdata  = Input(UInt(self.data_width))
        # self.strb   = Input(UInt(self.strb_width))
        self.ready  = Output(UInt(1))
        self.rdata  = Output(UInt(self.data_width))
        self.slverr = Output(UInt(1))
        # self.wakeup = Input(UInt(1))
        # self.auser  = Input(UInt(self.auser))
        # self.wuser  = Input(UInt(self.wuser))
        # self.ruser  = Output(UInt(self.ruser))
        # self.buser  = Output(UInt(self.buser))

    def reverse(self):
        return APB3Reverse(self.data_width, self.addr_width)

class APB3Reverse(Bundle):
    def __init__(self, data_width=32, addr_width=32):
        super().__init__()
        self.addr_width = addr_width
        self.data_width = data_width
        # self.strb_width = int(self.data_width/8)

        self.addr   = Output(UInt(self.addr_width))
        self.prot   = Output(UInt(3))
        self.sel    = Output(UInt(1))
        self.enable = Output(UInt(1))
        self.write  = Output(UInt(1))
        self.wdata  = Output(UInt(self.data_width))
        # self.strb   = Output(UInt(self.strb_width))
        self.ready  = Input(UInt(1))
        self.rdata  = Input(UInt(self.data_width))
        self.slverr = Input(UInt(1))

class APB4(Bundle):
    def __init__(self, data_width=APG_DATA_WIDTH, addr_width=APG_ADDR_WIDTH):
        super().__init__()
        self.addr_width = addr_width
        self.data_width = data_width
        self.strb_width = int(self.data_width/8)
        # self.auser = 5
        # self.wuser = 5
        # self.ruser = 5
        # self.buser = 5

        self.addr   = Input(UInt(self.addr_width))
        # self.prot   = Input(UInt(3))
        self.sel    = Input(UInt(1))
        self.enable = Input(UInt(1))
        self.write  = Input(UInt(1))
        self.wdata  = Input(UInt(self.data_width))
        self.strb   = Input(UInt(self.strb_width))
        self.ready  = Output(UInt(1))
        self.rdata  = Output(UInt(self.data_width))
        self.slverr = Output(UInt(1))
        # self.wakeup = Input(UInt(1))
        # self.auser  = Input(UInt(self.auser))
        # self.wuser  = Input(UInt(self.wuser))
        # self.ruser  = Output(UInt(self.ruser))
        # self.buser  = Output(UInt(self.buser))

    def reverse(self):
        return APB4Reverse(self.data_width, self.addr_width)

class APB4Reverse(Bundle):
    def __init__(self, data_width=32, addr_width=32):
        super().__init__()
        self.addr_width = addr_width
        self.data_width = data_width
        self.strb_width = int(self.data_width/8)

        self.addr   = Output(UInt(self.addr_width))
        self.prot   = Output(UInt(3))
        self.sel    = Output(UInt(1))
        self.enable = Output(UInt(1))
        self.write  = Output(UInt(1))
        self.wdata  = Output(UInt(self.data_width))
        self.strb   = Output(UInt(self.strb_width))
        self.ready  = Input(UInt(1))
        self.rdata  = Input(UInt(self.data_width))
        self.slverr = Input(UInt(1))



# if __name__=="__main__":
#     u_apb = APB().reverse()






