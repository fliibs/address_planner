from ..uhdl.uhdl import *


class APB(Bundle):
    def __init__(self):
        super().__init__()
        self.addr_width = 32
        self.data_width = 32
        self.strb_width = int(self.data_width/8)
        # self.auser = 5
        # self.wuser = 5
        # self.ruser = 5
        # self.buser = 5

        self.addr   = Input(UInt(self.addr_width))
        self.prot   = Input(UInt(3))
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





