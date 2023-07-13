

from .uhdl.uhdl import *

from .Field import FilledField
from .address_planner_rtl.APBInterface import APB
from .address_planner_rtl.Common import *


class RegSpaceRTL(Component):

    def __init__(self,cfg):
        super().__init__()
        self._cfg = cfg

        self.clk       = Input(UInt(1))
        self.rst_n     = Input(UInt(1))

        if 'apb' in self._cfg.external_interface:
            self.p              = APB()

            self.p.slverr       += UInt(1,0)

            rack_dat_read_mux   = EmptyWhen()
            rack_read_mux       = EmptyWhen()
            wack_rdy_mux        = EmptyWhen()
           
        else:
            if get_sw_readable(self._cfg.sub_space_list):
                self.rreq_addr = Input(UInt(32))
                self.rreq_vld  = Input(UInt(1))
                self.rreq_rdy  = Output(UInt(1))

                self.rack_data = Output(UInt(32))
                self.rack_vld  = Output(UInt(1))
                self.rack_rdy  = Input(UInt(1))

                self.rreq_rdy += And(self.rack_rdy,self.rack_vld)

                rack_dat_read_mux = EmptyWhen()
                rack_read_mux     = EmptyWhen()
            
            if get_sw_writeable(self._cfg.sub_space_list):
                self.wreq_addr = Input(UInt(32))
                self.wreq_data = Input(UInt(32))
                self.wreq_vld  = Input(UInt(1))
                self.wreq_rdy  = Output(UInt(1))

                wack_rdy_mux = EmptyWhen()
            

        for sub_space in self._cfg.sub_space_list:
            if get_sw_readable(self._cfg.sub_space_list):
                if 'apb' in self._cfg.external_interface:
                    reg_rdat = self.set('%s_rdat' % sub_space.module_name, Wire(UInt(32,0)))
                    reg_rrdy = self.set('%s_rrdy' % sub_space.module_name, Wire(UInt(1)))

                    reg_rrdy += And(Not(self.p.write), self.p.sel, self.p.enable, Equal(self.p.addr,UInt(32,sub_space.start_address)))
                    rack_dat_read_mux.when(And(And(Not(self.p.write), self.p.sel, self.p.enable, Equal(self.p.addr,UInt(32,sub_space.start_address))))).then(reg_rdat)
                    rack_read_mux.when(And(Not(self.p.write), self.p.sel, self.p.enable, Equal(self.p.addr,UInt(32,sub_space.start_address)))).then(UInt(1,1))
                    
                else:
                    reg_rdat = self.set('%s_rdat' % sub_space.module_name, Wire(UInt(32)))
                    reg_rrdy = self.set('%s_rrdy' % sub_space.module_name, Wire(UInt(1)))


                    reg_rrdy += And(self.rreq_vld, Equal(self.rreq_addr,UInt(32,sub_space.start_address)))
                    rack_dat_read_mux.when(Equal(self.rreq_addr,UInt(32,sub_space.start_address))).then(reg_rdat)
                    rack_read_mux.when(Equal(self.rreq_addr,UInt(32,sub_space.start_address))).then(UInt(1,1))
            else:
                reg_rrdy = self.set('%s_rrdy' % sub_space.module_name, Wire(UInt(1)))
                reg_rrdy += UInt(1,0)

            if get_sw_writeable(self._cfg.sub_space_list):
                if 'apb' in self._cfg.external_interface:
                    reg_wdat = self.set('%s_wdat' % sub_space.module_name, Wire(UInt(32)))
                    reg_wrdy = self.set('%s_wvld' % sub_space.module_name, Wire(UInt(1)))

                    # add mask
                    reg_wdat += byte_mask(self.p.rdata, self.p.strb)
                    reg_wrdy += And(self.p.write, self.p.sel, self.p.enable, Equal(self.p.addr,UInt(32,sub_space.start_address)))
                    wack_rdy_mux.when(And(self.p.write, self.p.sel, self.p.enable, Equal(self.p.addr,UInt(32,sub_space.start_address)))).then(UInt(1,1))
                    
                else:
                    reg_wdat = self.set('%s_wdat' % sub_space.module_name, Wire(UInt(32)))
                    reg_wrdy = self.set('%s_wvld' % sub_space.module_name, Wire(UInt(1)))

                    reg_wdat += self.wreq_data
                    reg_wrdy += And(self.wreq_vld, Equal(self.wreq_addr,UInt(32,sub_space.start_address)))
                    wack_rdy_mux.when(Equal(self.wreq_addr, UInt(32,sub_space.start_address))).then(UInt(1,1))
            else:
                reg_wrdy = self.set('%s_wvld' % sub_space.module_name, Wire(UInt(1)))
                reg_wrdy += UInt(1,0)


            ##########################################################################################################
            #   Internal interface
            ##########################################################################################################
            rdat_list = []

            for field in sub_space.filled_field_list:
                if isinstance(field, FilledField):
                    rdat_list.append(UInt(field.bit,0))
                else:
                    field_name = "%s_%s" % (sub_space.module_name, field.module_name)
                    reg_val = EmptyWhen()

                    if field.hw_writeable:
                        field_hw_wdat = self.set("%s_wdat" % field_name , Input(UInt(field.bit)))
                        field_hw_wenable = self.set("%s_wenable" % field_name , Input(UInt(1)))
                        # field_hw_wrdy = self.set("%s_wrdy" % field_name , Output(UInt(1)))

                        # field_hw_wrdy += UInt(1,1)
                        reg_val.when(field_hw_wenable).then(field_hw_wdat)

                    if field.sw_writeable:
                        if field.sw_write_one_to_set:
                            pass
                        else:
                            reg_val.when(reg_wrdy).then(reg_wdat[field.end_bit:field.start_bit])

                    field_reg = self.set(field_name, Reg(UInt(field.bit,0),self.clk,self.rst_n))

                    if field.hw_readable:
                        field_hw_rdat = self.set("%s_rdat" % field_name , Output(UInt(field.bit)))
                        
                        if field.hw_read_clean:
                            field_hw_rdat += UInt(field.bit,0)
                        else:
                            field_hw_rdat += field_reg
                        
                    if field.sw_readable:
                        if field.sw_read_clean:
                            reg_val.when(reg_rrdy).then(UInt(field.bit,0))                   
                        rdat_list.append(field_reg)
                    else:
                        rdat_list.append(UInt(field.bit,0))
                           
                    field_reg += reg_val
                                    
            if get_sw_readable(self._cfg.sub_space_list):
                reg_rdat += Combine(*rdat_list)
       
        ##########################################################################################################


        if get_sw_readable(self._cfg.sub_space_list):
            if 'apb' in self._cfg.external_interface:
                rack_dat_read_mux.otherwise(UInt(32,0))
                rack_read_mux.otherwise(UInt(1,0))

                self.p_rdata_r = Reg(UInt(self.p.rdata.width), self.clk, self.rst_n)
                self.p_rdata_r += rack_dat_read_mux
                self.p.rdata   += self.p_rdata_r
            else:
                rack_dat_read_mux.otherwise(UInt(32,0))
                rack_read_mux.otherwise(UInt(1,0))

                self.rack_data += rack_dat_read_mux
                self.rack_vld  += rack_read_mux

        if get_sw_writeable(self._cfg.sub_space_list):
            if 'apb' in self._cfg.external_interface:
                wack_rdy_mux.otherwise(UInt(1,0))
            else:
                wack_rdy_mux.otherwise(UInt(1,0))
                self.wreq_rdy  += wack_rdy_mux

        if 'apb' in self._cfg.external_interface:
            self.p_ready_r = Reg(UInt(1,0), self.clk, self.rst_n)
            self.p_ready_r += when(Or(reg_wrdy, reg_rrdy)).then(UInt(1,1)).otherwise(UInt(1,0))
            self.p.ready += self.p_ready_r


        

        