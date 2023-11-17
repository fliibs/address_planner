

from .uhdl.uhdl import *
from .Field import *
from .address_planner_rtl.APBInterface import APB3
from .address_planner_rtl.Common import *


class RegSpaceRTL():
    def __init__(self, cfg):
        # super().__init__()
        # self._cfg = cfg
        # if "apb" in self._cfg.software_interface:
        #     self.u = RegSpaceAPB(cfg=cfg)
        # else:
        #     self.u = RegSpaceBase(cfg=cfg)
        self.u = Regbank(cfg=cfg)


class Regbank(Component):

    def __init__(self,cfg):
        super().__init__()
        self._cfg      = cfg
        self.clk       = Input(UInt(1))
        self.rst_n     = Input(UInt(1))


        if "apb" in cfg.software_interface:
            self.rreq_addr      = Wire(UInt(self._cfg.bus_width))
            # self.rreq_vld       = Wire(UInt(1))
            # self.rreq_rdy       = Wire(UInt(1))

            self.rack_data      = Wire(UInt(self._cfg.data_width))
            self.rack_vld       = Wire(UInt(1))
            self.rack_rdy       = Wire(UInt(1))

            self.wreq_addr      = Wire(UInt(self._cfg.bus_width))
            self.wreq_data      = Wire(UInt(self._cfg.data_width))
            self.wreq_vld       = Wire(UInt(1))
            # self.wreq_rdy       = Wire(UInt(1))

            self.p              =  APB3(addr_width=self._cfg.bus_width)
            self.p.slverr       += UInt(1,0)
            
            # Software Input
            # self.rreq_vld       += BitAnd(Inverse(self.p.write), self.p.sel)
            self.rack_rdy       += BitAnd(Inverse(self.p.write), self.p.sel, self.p.enable)
            self.rreq_addr      += self.p.addr

            self.p.rdata        += self.rack_data
            self.p.ready        += UInt(1,1)

            self.wreq_vld       += BitAnd(self.p.write, self.p.sel, Inverse(self.p.enable))  
            self.wreq_addr      += self.p.addr
            # self.wreq_data      += byte_mask(self.p.wdata,self.p.strb)
            self.wreq_data      += self.p.wdata

        else:
            self.rreq_addr = Input(UInt(self._cfg.bus_width))
            self.rreq_vld  = Input(UInt(1))
            self.rreq_rdy  = Output(UInt(1))

            self.rack_data = Output(UInt(self._cfg.data_width))
            self.rack_vld  = Output(UInt(1))
            self.rack_rdy  = Input(UInt(1))

            self.wreq_addr = Input(UInt(self._cfg.bus_width))
            self.wreq_data = Input(UInt(self._cfg.data_width))
            self.wreq_vld  = Input(UInt(1))
            self.wreq_rdy  = Output(UInt(1))


        if hasattr(self, 'rreq_rdy'):
            if get_sw_readable(self._cfg.sub_space_list):
                self.rreq_rdy += BitAnd(self.rreq_vld, self.rack_rdy,self.rack_vld)
            else:
                self.rreq_rdy += UInt(1,0)

        rack_dat_read_mux = EmptyWhen()
        rack_read_mux     = EmptyWhen()
        wreq_rdy_mux      = EmptyWhen()
        
        #########################################################################################################
        #   Reg box
        #########################################################################################################
        for sub_space in self._cfg.sub_space_list:
            if sub_space.start_address >= sub_space.father.offset:
                start_address = int((sub_space.start_address - sub_space.father.offset)/8)
            else:
                start_address = int((sub_space.start_address)/8)
            # print("address:",start_address, sub_space.start_address, sub_space.offset)
            # print(sub_space.reg_type, self.__dict__)

            if get_sw_readable(self._cfg.sub_space_list):
                reg_rdat = self.set('%s_rdat' % sub_space.module_name, Wire(UInt(sub_space.bit)))
                reg_rrdy = self.set('%s_rrdy' % sub_space.module_name, Wire(UInt(1)))
                reg_rrdy += UInt(1,1)

                if get_sw_writevalid(sub_space):
                    print(sub_space.module_name)
                    reg_rvld = self.set('%s_rvld' % sub_space.module_name, Wire(UInt(1)))
                    reg_rvld += BitAnd(BitAnd(self.rack_rdy, self.rack_vld), Equal(self.rreq_addr,UInt(self._cfg.bus_width,start_address,'hex')))
                
                rack_dat_read_mux.when(Equal(self.rreq_addr,UInt(self._cfg.bus_width,start_address,'hex'))).then(reg_rdat)
                rack_read_mux.when(Equal(self.rreq_addr,UInt(self._cfg.bus_width,start_address,'hex'))).then(reg_rrdy)
            
            if get_sw_writeable(self._cfg.sub_space_list):
                reg_wdat = self.set('%s_wdat' % sub_space.module_name, Wire(UInt(sub_space.bit)))
                reg_wrdy = self.set('%s_wrdy' % sub_space.module_name, Wire(UInt(1)))
                reg_wvld = self.set('%s_wvld' % sub_space.module_name, Wire(UInt(1)))

                reg_wrdy += UInt(1,1)
                reg_wdat += self.wreq_data[sub_space.bit-1:0]
                
                magic_intf_list = []
                for magic in sub_space.get_magic_list:
                    if hasattr(self,f'{magic.module_name}_rdat'):
                        magic_intf_list.append(Equal(getattr(self,f'{magic.module_name}_rdat'), UInt(32,magic.field_list[0].password,'hex')))
                    else:
                        magic_intf_list.append(Equal(self.set('%s_rdat' % magic.module_name, Wire(UInt(magic.bit))), UInt(magic.bit,magic.field_list[0].password,'hex')))

                reg_wvld += BitAnd(self.wreq_vld, Equal(self.wreq_addr,UInt(self._cfg.bus_width,start_address,'hex')),*magic_intf_list)
                wreq_rdy_mux.when(Equal(self.wreq_addr, UInt(self._cfg.bus_width,start_address,'hex'))).then(reg_wrdy)
        

            ##########################################################################################################
            #   Internal interface
            ##########################################################################################################
            rdat_list = []

            for field in sub_space.filled_field_list:
                if isinstance(field, FilledField):
                    rdat_list.append(UInt(field.bit,0))
                # External Register Software Access
                elif field.reserved:
                    rdat_list.append(UInt(field.bit,0))
                elif not field.field_reg_write:
                    rdat_list.append(UInt(field.bit,field.init_value))

                elif field.is_external:
                    field_name = "%s_sw_%s" % (sub_space.module_name, field.module_name)
                    if get_sw_readable(self._cfg.sub_space_list):
                        field_sw_rdat  = self.set('%s_rdat' % field_name, Input(UInt(field.bit)))
                        field_sw_rvld  = self.set('%s_rvld' % field_name, Output(UInt(1)))
                        # field_sw_rrdy  = self.set('%s_rrdy' % field_name, Input(UInt(1)))
                        
                        field_sw_rvld += reg_rvld
                        rdat_list.append(field_sw_rdat)
                    else:
                        rdat_list.append(UInt(field.bit,0))

                    if get_sw_writeable(self._cfg.sub_space_list):
                        field_sw_wdat  = self.set('%s_wdat' % field_name, Output(UInt(field.bit)))
                        field_sw_wvld  = self.set('%s_wvld' % field_name, Output(UInt(1)))
                        # field_sw_wrdy  = self.set('%s_wrdy' % field_name, Input(UInt(1)))

                        field_sw_wdat += reg_wdat[field.end_bit:field.start_bit]
                        field_sw_wvld += reg_wvld

                # write one pulse field
                elif field.sw_write_one_pulse or field.sw_write_zero_pulse:
                    rdat_list.append(UInt(field.bit,0))
                    field_name = "%s_%s" % (sub_space.module_name, field.module_name)
                    field_hw_rdat = self.set("%s_rdat" % field_name , Output(UInt(field.bit)))
                    # field_hw_rdat_reg = self.set("%s" % field_name, Reg(UInt(field.bit,0), self.clk, self.rst_n))
                    field_hw_rdat_reg = self.set("%s" % field_name, Wire(UInt(field.bit)))

                    lock_intf_list = []
                    for lock in field.get_lock_list:
                        lock_field_name = f'{lock[0].module_name}_{lock[1].name}'
                        if hasattr(self, lock_field_name):
                            lock_intf_list.append(Fanout(getattr(self, lock_field_name),field_hw_rdat_reg.width))
                        else:
                            lock_intf_list.append(Fanout(self.set(lock_field_name, Reg(UInt(lock[1].bit,lock[1].init_value),self.clk,self.rst_n)),field_hw_rdat_reg.width))
                    
                    field_lock_ena = self.set('%s_lock_ena'% field_name, Wire(UInt(field_hw_rdat_reg.width)))
                    field_lock_ena += BitAnd(Fanout(reg_wvld,field_hw_rdat_reg.width),*lock_intf_list)

                    if field.sw_write_one_pulse:
                        field_hw_rdat_reg+=BitAnd(reg_wdat[field.end_bit:field.start_bit], field_lock_ena)
                    else:
                        field_hw_rdat_reg+=BitAnd(Inverse(reg_wdat[field.end_bit:field.start_bit]), field_lock_ena)
                    field_hw_rdat += field_hw_rdat_reg  

                # Internal Register  
                else:
                    field_name = "%s_%s" % (sub_space.module_name, field.module_name)
                    field_reg = self.set(field_name, Reg(UInt(field.bit,field.init_value),self.clk,self.rst_n))
                    reg_val = EmptyWhen()

                    if field.hw_writeable:
                        if not (field.hw_write_clean or field.hw_write_set):
                            field_hw_wdat = self.set("%s_wdat" % field_name , Input(UInt(field.bit)))
                        field_hw_wena = self.set("%s_wena" % field_name , Input(UInt(1)))

                        if field.hw_write_clean:
                            reg_val.when(field_hw_wena).then(UInt(field.bit,0))
                        elif field.hw_write_one_to_clean:
                            reg_val.when(field_hw_wena).then(BitAnd(Inverse(field_hw_wdat), field_reg))
                        elif field.hw_write_zero_to_clean:
                            reg_val.when(field_hw_wena).then(BitAnd(field_hw_wdat, field_reg))
                        elif field.hw_write_set:
                            reg_val.when(field_hw_wena).then(UInt(field.bit,2**(field.bit)-1))
                        elif field.hw_write_one_to_set:
                            reg_val.when(field_hw_wena).then(BitOr(field_hw_wdat, field_reg))
                        elif field.hw_write_zero_to_set:
                            reg_val.when(field_hw_wena).then(BitOr(Inverse(field_hw_wdat), field_reg))
                        elif field.hw_write_one_to_toggle:
                            reg_val.when(field_hw_wena).then(BitXor(field_hw_wdat, field_reg))
                        elif field.hw_write_zero_to_toggle:
                            reg_val.when(field_hw_wena).then(BitXnor(field_hw_wdat, field_reg))
                        elif field.hw_write_once:
                            hw_flag = self.set("%s_hw_flag" % field_name, Reg(UInt(1,0),self.clk,self.rst_n))
                            hw_flag += when(field_hw_wena).then(UInt(1,1))
                            reg_val.when(BitAnd(field_hw_wena, Inverse(hw_flag))).then(field_hw_wdat)
                        else:
                            reg_val.when(field_hw_wena).then(field_hw_wdat)

                    if field.sw_writeable:
                        lock_intf_list = []
                        for lock in field.get_lock_list:
                            lock_field_name = f'{lock[0].module_name}_{lock[1].name}'
                            if hasattr(self, lock_field_name):
                                lock_intf_list.append(getattr(self, lock_field_name))
                            else:
                                lock_intf_list.append(self.set(lock_field_name, Reg(UInt(lock[1].bit,lock[1].init_value),self.clk,self.rst_n)))
                        
                        field_write_enable = self.set('%s_sw_wren'% field_name, Wire(UInt(1)))
                        field_write_enable += BitAnd(reg_wvld, *lock_intf_list)

                        if field.sw_write_clean:
                            reg_val.when(field_write_enable).then(UInt(field.bit,0))
                        elif field.sw_write_one_to_clean:
                            reg_val.when(field_write_enable).then(BitAnd(Inverse(reg_wdat[field.end_bit:field.start_bit]), field_reg))
                        elif field.sw_write_zero_to_clean:
                            reg_val.when(field_write_enable).then(BitAnd(reg_wdat[field.end_bit:field.start_bit], field_reg))
                        elif field.sw_write_set:
                            reg_val.when(field_write_enable).then(UInt(field.bit,2**(field.bit)-1))
                        elif field.sw_write_one_to_set:
                            reg_val.when(field_write_enable).then(BitOr(reg_wdat[field.end_bit:field.start_bit], field_reg))
                        elif field.sw_write_zero_to_set:
                            reg_val.when(field_write_enable).then(BitOr(Inverse(reg_wdat[field.end_bit:field.start_bit]), field_reg))
                        elif field.sw_write_one_to_toggle:
                            reg_val.when(field_write_enable).then(BitXor(reg_wdat[field.end_bit:field.start_bit], field_reg))
                        elif field.sw_write_zero_to_toggle:
                            reg_val.when(field_write_enable).then(BitXnor(reg_wdat[field.end_bit:field.start_bit], field_reg))
                        elif field.sw_write_once:
                            sw_flag = self.set("%s_sw_flag" % field_name, Reg(UInt(1,0),self.clk,self.rst_n))
                            sw_flag += when(field_write_enable).then(UInt(1,1))
                            reg_val.when(BitAnd(field_write_enable, Inverse(sw_flag))).then(reg_wdat[field.end_bit:field.start_bit])
                        else:
                            reg_val.when(field_write_enable).then(reg_wdat[field.end_bit:field.start_bit])

                    if field.hw_readable:
                        field_hw_rdat = self.set("%s_rdat" % field_name , Output(UInt(field.bit)))
                        
                        if field.hw_read_clean:
                            field_hw_rena = self.set("%s_rena" % field_name , Input(UInt(1)))
                            reg_val.when(field_hw_rena).then(UInt(field.bit,0))
                        elif field.hw_read_set:
                            field_hw_rena = self.set("%s_rena" % field_name , Input(UInt(1)))
                            reg_val.when(field_hw_rena).then(UInt(field.bit,2**(field.bit)-1))
                        
                        field_hw_rdat += field_reg
                        
                    if field.sw_readable:
                        if field.sw_read_clean:
                            reg_val.when(reg_rvld).then(UInt(field.bit,0))
                        elif field.sw_read_set:
                            reg_val.when(reg_rvld).then(UInt(field.bit,2**(field.bit)-1))   
                        rdat_list.append(field_reg)
                    else:
                        rdat_list.append(UInt(field.bit,0))

                    field_reg += reg_val
                                        
            
            ### Interrupt register logic
            if get_sw_readable(self._cfg.sub_space_list):
                rdat_list.reverse()
                if sub_space.reg_type==Intr:
                    reg_rdat += BitAnd(Combine(*rdat_list),getattr(self,f'{sub_space.module_name}_enable_rdat'))
                elif sub_space.reg_type==IntrMask:
                    reg_rdat += BitAnd(Combine(*rdat_list),getattr(self,f'{sub_space.module_name}_enable_rdat'),Inverse(getattr(self,f'{sub_space.module_name}_mask_rdat')))
                else:
                    reg_rdat += Combine(*rdat_list)
                
        
        ##########################################################################################################
        if get_sw_readable(self._cfg.sub_space_list):
            rack_dat_read_mux.otherwise(UInt(self._cfg.data_width,2**(self._cfg.data_width)-2,'hex'))
            rack_read_mux.otherwise(UInt(1,0))

            self.rack_data += rack_dat_read_mux
            self.rack_vld  += rack_read_mux
        else:
            self.rack_data += UInt(self._cfg.data_width,0)
            self.rack_vld  += UInt(1,0)

        if hasattr(self, 'wreq_rdy'):
            if get_sw_writeable(self._cfg.sub_space_list):
                wreq_rdy_mux.otherwise(UInt(1,0))
                self.wreq_rdy  += wreq_rdy_mux
            else:
                self.wreq_rdy  += UInt(1,0)



        

# class RegSpaceAPB(Component):
#     def __init__(self, cfg):
#         super().__init__()
#         self._cfg = cfg
#         self.rs = RegSpaceBase(cfg=cfg)

#         self.clk    = Input(UInt(1))
#         self.rst_n  = Input(UInt(1))


#         self.rs.clk     += self.clk
#         self.rs.rst_n   += self.rst_n

#         # if self._cfg.
#         self.p          = APB(addr_width=self._cfg.bus_width)
#         self.p.slverr  += UInt(1,0)

#         # self.p_ready_r = Reg(UInt(1,0), self.clk, self.rst_n)
#         self.p_rready  = Wire(UInt(1))
#         self.p_wready  = Wire(UInt(1))
        
#         # Software Input
#         self.rs.rreq_vld    += And(Not(self.p.write), self.p.sel)
#         self.rs.rack_rdy    += And(Not(self.p.write), self.p.sel, self.p.enable)
#         self.rs.rreq_addr   += self.p.addr

#         # self.p_rdata_r = Reg(UInt(self.p.rdata.width,0), self.clk, self.rst_n)
#         # rdata_ff = EmptyWhen()
#         # rdata_ff.when(And(self.rs.rreq_vld, self.rs.rreq_rdy)).then(self.rs.rack_data).otherwise(UInt(self.p.rdata.width,0))
#         # self.p_rdata_r      += rdata_ff
#         # self.p.rdata        += self.p_rdata_r
#         self.p.rdata        += self.rs.rack_data

#         self.p_rready       += And(self.rs.rreq_vld, self.rs.rreq_rdy)
#         self.p_wready       += And(self.rs.wreq_rdy,self.p.enable)
#         self.p.ready        += Or(self.p_rready, self.p_wready)
        

#         self.rs.wreq_vld    += And(self.p.write, self.p.sel, self.p.enable)  
#         self.rs.wreq_addr   += self.p.addr
#         self.rs.wreq_data   += byte_mask(self.p.wdata,self.p.strb)

        
#         # ready_ff = EmptyWhen()
#         # ready_ff.when(Or(self.p_rready, self.p_wready)).then(UInt(1,1)).otherwise(UInt(1,0))
#         # self.p_ready_r += ready_ff
#         # self.p.ready   += self.p_ready_r
        

#         for sub_space in cfg.sub_space_list:
#             for field in sub_space.filled_field_list:
#                  if isinstance(field, FilledField):
#                     pass
#                  else:
#                     # Internal Hardware Field
#                     for attr_in in INTERNAL_FIELD_DICT:
#                         self.expose_io(perfect_get_io(self.rs, "%s_%s_%s"% (sub_space.module_name, field.name, attr_in)))
#                     # Software External Field
#                     for attr_ex in EXTERNAL_FIELD_DICT:
#                         self.expose_io(perfect_get_io(self.rs, "%s_sw_%s_%s"% (sub_space.module_name, field.name, attr_ex)))
                    

    



                