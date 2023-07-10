from .uhdl import *


class APB(Bundle):
    def __init__(self):
        super().__init__()
        self.addr = 32
        self.data = 32
        self.strb = int(self.data/8)
        # self.auser = 5
        # self.wuser = 5
        # self.ruser = 5
        # self.buser = 5

        self.addr   = Input(UInt(self.addr))
        self.prot   = Input(UInt(3))
        self.sel    = Input(UInt(1))
        self.enable = Input(UInt(1))
        self.write  = Input(UInt(1))
        self.wdata  = Input(UInt(self.data))
        self.strb   = Input(UInt(self.strb))
        self.ready  = Output(UInt(1))
        self.rdata  = Output(UInt(self.data))
        self.slverr = Output(UInt(1))
        # self.wakeup = Input(UInt(1))
        # self.auser  = Input(UInt(self.auser))
        # self.wuser  = Input(UInt(self.wuser))
        # self.ruser  = Output(UInt(self.ruser))
        # self.buser  = Output(UInt(self.buser))





