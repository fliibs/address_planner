

from .uhdl.uhdl import *
from .Field import *
from .address_planner_rtl.APBInterface import APB
from .address_planner_rtl.Common import *


class RegSpaceRTL(Component):
    def __init__(self, cfg):
        super().__init__()
        self._cfg = cfg
        if "apb" in self._cfg.external_interface:
            self.u = RegSpaceAPB(cfg=cfg)
        else:
            self.u = RegSpaceBase(cfg=cfg)


class RegSpaceBase(Component):

    def __init__(self,cfg):
        super().__init__()
        self._cfg = cfg

        self.clk       = Input(UInt(1))
        self.rst_n     = Input(UInt(1))
        
        self.rreq_addr = Input(UInt(APG_ADDR_WIDTH))
        self.rreq_vld  = Input(UInt(1))
        self.rreq_rdy  = Output(UInt(1))

        self.rack_data = Output(UInt(APG_DATA_WIDTH))
        self.rack_vld  = Output(UInt(1))
        self.rack_rdy  = Input(UInt(1))

        if get_sw_readable(self._cfg.sub_space_list):
            self.rreq_rdy += And(self.rack_rdy,self.rack_vld)
        else:
            self.rreq_rdy += UInt(1,0)

        rack_dat_read_mux = EmptyWhen()
        rack_read_mux     = EmptyWhen()
        
        self.wreq_addr = Input(UInt(APG_ADDR_WIDTH))
        self.wreq_data = Input(UInt(APG_DATA_WIDTH))
        self.wreq_vld  = Input(UInt(1))
        self.wreq_rdy  = Output(UInt(1))

        wack_rdy_mux = EmptyWhen()
        
        #########################################################################################################
        #   Reg box
        #########################################################################################################
        for sub_space in self._cfg.sub_space_list:
            if get_sw_readable(self._cfg.sub_space_list):
                reg_rdat = self.set('%s_rdat' % sub_space.module_name, Wire(UInt(sub_space.bit)))
                reg_rrdy = self.set('%s_rrdy' % sub_space.module_name, Wire(UInt(1)))
                reg_rvld = self.set('%s_rvld' % sub_space.module_name, Wire(UInt(1)))

                reg_rrdy += UInt(1,1)
                reg_rvld += And(And(self.rack_rdy, self.rack_vld), Equal(self.rreq_addr,UInt(APG_ADDR_WIDTH,sub_space.start_address)))
                rack_dat_read_mux.when(Equal(self.rreq_addr,UInt(APG_ADDR_WIDTH,sub_space.start_address))).then(reg_rdat)
                rack_read_mux.when(Equal(self.rreq_addr,UInt(APG_ADDR_WIDTH,sub_space.start_address))).then(reg_rrdy)
            
            if get_sw_writeable(self._cfg.sub_space_list):
                
                reg_wdat = self.set('%s_wdat' % sub_space.module_name, Wire(UInt(sub_space.bit)))
                reg_wrdy = self.set('%s_wrdy' % sub_space.module_name, Wire(UInt(1)))
                reg_wvld = self.set('%s_wvld' % sub_space.module_name, Wire(UInt(1)))

                reg_wrdy += UInt(1,1)
                reg_wdat += self.wreq_data[sub_space.bit-1:0]
                reg_wvld += And(self.wreq_vld, Equal(self.wreq_addr,UInt(APG_ADDR_WIDTH,sub_space.start_address)))
                wack_rdy_mux.when(Equal(self.wreq_addr, UInt(APG_ADDR_WIDTH,sub_space.start_address))).then(reg_wrdy)
           

            ##########################################################################################################
            #   Internal interface
            ##########################################################################################################
            rdat_list = []

            for field in sub_space.filled_field_list:
                if isinstance(field, FilledField):
                    rdat_list.append(UInt(field.bit,0))

                # External Register Software Access
                elif field.is_external:
                    field_name = "%s_sw_%s" % (sub_space.module_name, field.module_name)
                    if get_sw_readable(self._cfg.sub_space_list):
                        field_sw_rdat  = self.set('%s_rdat' % field_name, Input(UInt(field.bit)))
                        field_sw_rvld  = self.set('%s_rvld' % field_name, Output(UInt(1)))
                        field_sw_rrdy  = self.set('%s_rrdy' % field_name, Input(UInt(1)))
                        
                        field_sw_rvld += reg_rvld
                        rdat_list.append(field_sw_rdat)

                    else:
                        rdat_list.append(UInt(field.bit,0))


                    if get_sw_writeable(self._cfg.sub_space_list):
                        field_sw_wdat  = self.set('%s_wdat' % field_name, Output(UInt(field.bit)))
                        field_sw_wvld  = self.set('%s_wvld' % field_name, Output(UInt(1)))
                        field_sw_wrdy  = self.set('%s_wrdy' % field_name, Input(UInt(1)))

                        field_sw_wdat += reg_wdat[field.end_bit:field.start_bit]
                        field_sw_wvld += reg_wvld

                # Internal Register    
                else:
                    field_name = "%s_%s" % (sub_space.module_name, field.module_name)
                    reg_val = EmptyWhen()

                    if field.hw_writeable:
                        field_hw_wdat = self.set("%s_wdat" % field_name , Input(UInt(field.bit)))
                        field_hw_wvld = self.set("%s_wvld" % field_name , Input(UInt(1)))
                        field_hw_wrdy = self.set("%s_wrdy" % field_name , Output(UInt(1)))

                        field_hw_wrdy += UInt(1,1)
                        reg_val.when(field_hw_wvld).then(field_hw_wdat)

                    if field.sw_writeable:
                        if field.sw_write_one_to_set:
                            pass
                        else:
                            reg_val.when(reg_wvld).then(reg_wdat[field.end_bit:field.start_bit])

                    field_reg = self.set(field_name, Reg(UInt(field.bit,0),self.clk,self.rst_n))

                    if field.hw_readable:
                        field_hw_rdat = self.set("%s_rdat" % field_name , Output(UInt(field.bit)))
                        field_hw_rvld = self.set("%s_rvld" % field_name , Output(UInt(1)))
                        field_hw_rrdy = self.set("%s_rrdy" % field_name , Input(UInt(1)))
                        
                        field_hw_rvld += UInt(1,1)
                        if field.hw_read_clean:
                            field_hw_rdat += UInt(field.bit,0)
                        else:
                            field_hw_rdat += field_reg
                        
                    if field.sw_readable:
                        if field.sw_read_clean:
                            reg_val.when(reg_rvld).then(UInt(field.bit,0))                   
                        rdat_list.append(field_reg)
                    else:
                        rdat_list.append(UInt(field.bit,0))

                    # if (field.sw_writeable and field.is_external) or field.hw_writeable:
                    field_reg += reg_val
                                    
            if get_sw_readable(self._cfg.sub_space_list):
                reg_rdat += Combine(*rdat_list)
       
        ##########################################################################################################

        if get_sw_readable(self._cfg.sub_space_list):
            rack_dat_read_mux.otherwise(UInt(sub_space.bit,0))
            rack_read_mux.otherwise(UInt(1,0))

            self.rack_data += rack_dat_read_mux
            self.rack_vld  += rack_read_mux
        else:
            self.rack_data += UInt(sub_space.bit,0)
            self.rack_vld  += UInt(1,0)

        if get_sw_writeable(self._cfg.sub_space_list):
            wack_rdy_mux.otherwise(UInt(1,0))
            self.wreq_rdy  += wack_rdy_mux
        else:
            self.wreq_rdy  += UInt(1,0)

        

class RegSpaceAPB(Component):
    def __init__(self, cfg):
        super().__init__()
        self._cfg = cfg
        self.rs = RegSpaceBase(cfg=cfg)

        self.clk    = Input(UInt(1))
        self.rst_n  = Input(UInt(1))


        self.rs.clk     += self.clk
        self.rs.rst_n   += self.rst_n

        # if self._cfg.
        self.p          = APB()
        self.p.slverr  += UInt(1,0)

        self.p_ready_r = Reg(UInt(1,0), self.clk, self.rst_n)
        self.p_rready  = Wire(UInt(1))
        self.p_wready  = Wire(UInt(1))
        

        # Software Input
        self.rs.rreq_vld    += And(Not(self.p.write), self.p.sel)
        self.rs.rack_rdy    += And(Not(self.p.write), self.p.sel, self.p.enable)
        self.rs.rreq_addr   += self.p.addr
        # self.rs.rreq_addr   += UInt(16,0)

        self.p_rdata_r = Reg(UInt(self.p.rdata.width,0), self.clk, self.rst_n)
        rdata_ff = EmptyWhen()
        rdata_ff.when(And(self.rs.rreq_vld, self.rs.rreq_rdy)).then(self.rs.rack_data).otherwise(UInt(self.p.rdata.width,0))
        self.p_rdata_r      += rdata_ff
        self.p.rdata        += self.p_rdata_r

        self.p_rready       += And(self.rs.rreq_vld, self.rs.rreq_rdy)
       
        

        self.rs.wreq_vld    += And(self.p.write, self.p.sel, self.p.enable)  
        self.rs.wreq_addr   += self.p.addr

        self.rs.wreq_data   += byte_mask(self.p.wdata,self.p.strb)

        self.p_wready       += self.rs.wreq_rdy
       
            
        ready_ff = EmptyWhen()
        ready_ff.when(Or(self.p_rready, self.p_wready)).then(UInt(1,1)).otherwise(UInt(1,0))
        self.p_ready_r += ready_ff
        self.p.ready   += self.p_ready_r


        # Internal Hardware Field
        self.expose_io(self.rs.get_io(r'reg[0-9]_field'))

        # Software External Field
        self.expose_io(self.rs.get_io(r'reg[0-9]_sw_field'))
            
                    





                