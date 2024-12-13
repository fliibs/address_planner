

from .uhdl.uhdl import *
from .Field import *
from .Parity import *
from .address_planner_rtl.APBInterface import APB3, APB4
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
        # self.rst_n     = Input(UInt(1))
        # generate reset domain
        for sub_space in self._cfg.sub_space_list:
            if not hasattr(self, sub_space.rst_domain):     
                self.set(f'{sub_space.rst_domain}', Input(UInt(1)))

        ####
        is_apb3             = True if "apb" in self._cfg.software_interface else False
        is_apb4             = True if "apb4" in self._cfg.software_interface else False
        apb3_has_rack_hsk   = get_sw_read_clean_and_set(sub_space=self._cfg, outer=True) or get_field_external(sub_space=self._cfg, outer=True)
        ####

        if "apb" in self._cfg.software_interface:
            if is_apb4:
                self.p        =  APB4(addr_width=self._cfg.bus_width)
                self.p_unmask =  Wire(UInt(self._cfg.data_width))
                self.p_mask   =  Wire(UInt(self._cfg.data_width))
                self.p_unmask += strb_extend(self.p.strb)
                self.p_mask   += Inverse(self.p_unmask)
            else:
                self.p          =  APB3(addr_width=self._cfg.bus_width)

            self.rreq_addr      = Wire(UInt(self._cfg.bus_width))
            # self.rreq_vld       = Wire(UInt(1))
            # self.rreq_rdy       = Wire(UInt(1))

            self.rack_data      = Wire(UInt(self._cfg.data_width))
            if apb3_has_rack_hsk:
                self.rack_vld       = Wire(UInt(1))
                self.rack_rdy       = Wire(UInt(1))
                self.rack_rdy       += BitAnd(Inverse(self.p.write), self.p.sel, self.p.enable)

            self.wreq_addr      = Wire(UInt(self._cfg.bus_width))
            self.wreq_data      = Wire(UInt(self._cfg.data_width))
            self.wreq_vld       = Wire(UInt(1))
            # self.wreq_rdy       = Wire(UInt(1))

            # Software Input
            # self.rreq_vld       += BitAnd(Inverse(self.p.write), self.p.sel)
            self.rreq_addr      += self.p.addr

            self.p.rdata        += self.rack_data
            self.p.ready        += UInt(1,1)
            self.p.slverr       += UInt(1,0)

            self.wreq_vld       += BitAnd(self.p.write, self.p.sel, self.p.enable)  
            self.wreq_addr      += self.p.addr
            self.wreq_data      += self.p.wdata
            
            pulse_wvld          = BitAnd(self.p.write, self.p.sel, self.p.enable)

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

            pulse_wvld     = self.wreq_vld

            if get_sw_readable(self._cfg.sub_space_list):   self.rreq_rdy += BitAnd(self.rreq_vld, self.rack_rdy,self.rack_vld)
            else:                                           self.rreq_rdy += UInt(1,0)


        if get_reg_parity(self._cfg.sub_space_list):        setattr(self, f"parity_sw_check_err", Output(UInt(1)))

        rack_dat_read_mux    = EmptyWhen()
        rack_read_mux        = EmptyWhen()
        wreq_rdy_mux         = EmptyWhen()
        parity_check_err_mux = EmptyWhen()
        
        #########################################################################################################
        #   Reg box
        #########################################################################################################
        for sub_space in self._cfg.sub_space_list:
            rst = getattr(self, sub_space.rst_domain)

            ####
            just_write_clean_or_set     = get_sw_write_clean_and_set(sub_space)
            sub_space_writeable         = get_sw_writeable(sub_space.field_list, outer=False)
            sub_space_all_write_pulse   = get_sw_all_pulse(sub_space.field_list, outer=False)
            ####

            if sub_space.start_address >= sub_space.father.offset:  start_address = int((sub_space.start_address - sub_space.father.offset)/8)
            else:                                                   start_address = int((sub_space.start_address)/8)

            if get_sw_readable(self._cfg.sub_space_list):
                reg_rdat = self.set('%s_rdat' % sub_space.module_name, Wire(UInt(sub_space.bit)))
                rack_dat_read_mux.when(Equal(self.rreq_addr,UInt(self._cfg.bus_width,start_address,'hex'))).then(reg_rdat)

                if apb3_has_rack_hsk:
                    reg_rrdy = self.set('%s_rrdy' % sub_space.module_name, Wire(UInt(1)))
                    reg_rrdy += UInt(1,1)
                    rack_read_mux.when(Equal(self.rreq_addr,UInt(self._cfg.bus_width,start_address,'hex'))).then(reg_rrdy)

                if apb3_has_rack_hsk:
                    reg_rvld = self.set('%s_rvld' % sub_space.module_name, Wire(UInt(1)))
                    reg_rvld += BitAnd(BitAnd(self.rack_rdy, self.rack_vld), Equal(self.rreq_addr,UInt(self._cfg.bus_width,start_address,'hex')))
                
            
            if get_sw_writeable(self._cfg.sub_space_list):
                if just_write_clean_or_set or sub_space_writeable:
                    reg_wdat = self.set('%s_wdat' % sub_space.module_name, Wire(UInt(sub_space.bit)))
                    reg_wdat += self.wreq_data

                magic_intf_list = []
                for magic in sub_space.get_magic_list:
                    if hasattr(self,f'{magic.module_name}_rdat'):   magic_intf_list.append(Equal(getattr(self,f'{magic.module_name}_rdat'), UInt(32,magic.field_list[0].password,'hex')))
                    else:                                           magic_intf_list.append(Equal(self.set('%s_rdat' % magic.module_name, Wire(UInt(magic.bit))), UInt(magic.bit,magic.field_list[0].password,'hex')))

                if sub_space_writeable and not sub_space_all_write_pulse:
                    reg_wvld = self.set('%s_wvld' % sub_space.module_name, Wire(UInt(1)))
                    reg_wvld += BitAnd(self.wreq_vld, Equal(self.wreq_addr,UInt(self._cfg.bus_width,start_address,'hex')),*magic_intf_list)

                if not is_apb3:
                    reg_wrdy = self.set('%s_wrdy' % sub_space.module_name, Wire(UInt(1)))
                    reg_wrdy += UInt(1,1)
                    wreq_rdy_mux.when(Equal(self.wreq_addr, UInt(self._cfg.bus_width,start_address,'hex'))).then(reg_wrdy)
        

            ##########################################################################################################
            #   Internal interface
            ##########################################################################################################
            rdat_list = []

            for field in sub_space.filled_field_list:
                ####
                is_hw_write_clean_or_set = field.hw_write_clean or field.hw_write_set
                is_sw_write_clean_or_set = field.sw_write_clean or field.sw_write_set
                ####
                if isinstance(field, FilledField):
                    rdat_list.append(UInt(field.bit,0))
                elif field.reserved:
                    rdat_list.append(UInt(field.bit,0))
                #===============================================================
                # External Register Software Access
                #===============================================================
                elif field.is_external:
                    field_name = "%s_%s" % (sub_space.module_name, field.module_name)
                    if field.sw_readable:
                        field_sw_rdat  = self.set('%s_rdat' % field_name, Input(UInt(field.bit)))
                        field_sw_rvld  = self.set('%s_rvld' % field_name, Output(UInt(1)))
                        # field_sw_rrdy  = self.set('%s_rrdy' % field_name, Input(UInt(1)))
                        
                        field_sw_rvld += reg_rvld
                        rdat_list.append(field_sw_rdat)
                    else:
                        rdat_list.append(UInt(field.bit,0))

                    if field.sw_writeable:
                        field_sw_wdat  = self.set('%s_wdat' % field_name, Output(UInt(field.bit)))
                        field_sw_wvld  = self.set('%s_wvld' % field_name, Output(UInt(1)))
                        # field_sw_wrdy  = self.set('%s_wrdy' % field_name, Input(UInt(1)))

                        field_sw_wdat += reg_wdat[field.end_bit:field.start_bit]
                        field_sw_wvld += reg_wvld

                        if is_apb4:
                            field_sw_strb =  self.set('%s_wmask' % field_name, Output(UInt(field.bit)))
                            field_sw_strb += self.p_mask[field.end_bit:field.start_bit]

                    if sub_space.parity:
                        if field.hw_read_clean or field.hw_read_set:
                            field_ext_hw_rena = self.set("%s_parity_hw_rena" % field_name , Input(UInt(1)))

                        if field.hw_writeable:
                            if not is_hw_write_clean_or_set:    field_ext_hw_wdat = self.set("%s_parity_hw_wdat" % field_name , Input(UInt(field.bit)))
                            field_ext_hw_wena = self.set("%s_parity_hw_wena" % field_name , Input(UInt(1)))

                        if field.sw_read_clean or field.sw_read_set:
                            field_ext_sw_wena = self.set("%s_parity_sw_rena" % field_name , Input(UInt(1)))

                        if field.sw_writeable:
                            if not is_sw_write_clean_or_set:    field_ext_sw_wdat = self.set("%s_parity_sw_wdat" % field_name , Input(UInt(field.bit)))
                            field_ext_sw_wena = self.set("%s_parity_sw_wena" % field_name , Input(UInt(1)))

                        field_ext_data = self.set(f'{field_name}_parity_field', Input(UInt(field.bit,field.init_value)))
                
                #===============================================================
                # write one pulse field
                #===============================================================
                elif field.sw_write_one_pulse or field.sw_write_zero_pulse:
                    field_name = "%s_%s" % (sub_space.module_name, field.module_name)
                    field_hw_rdat_reg = self.set("%s" % field_name, Wire(UInt(field.bit)))

                    lock_intf_list = []
                    for lock in field.get_lock_list:
                        lock_field_name = f'{lock[0].module_name}_{lock[1].name}'
                        if hasattr(self, lock_field_name):  field_lock_inv = Inverse(Fanout(getattr(self, lock_field_name),field_hw_rdat_reg.width))
                        else:                               field_lock_inv = Inverse(Fanout(self.set(lock_field_name, Reg(UInt(lock[1].bit,lock[1].init_value),self.clk,rst)),field_hw_rdat_reg.width))
                        lock_intf_list.append(field_lock_inv)

                    field_lock_ena = self.set('%s_ena'% field_name, Wire(UInt(field_hw_rdat_reg.width)))
                    field_lock_ena += BitAnd(Fanout(BitAnd(pulse_wvld, Equal(self.wreq_addr,UInt(self._cfg.bus_width,start_address,'hex')),*magic_intf_list),field_hw_rdat_reg.width),*lock_intf_list)

                    field_wdat = self.set('%s_wdat'% field_name, Wire(UInt(field.bit)))
                    if is_apb4:
                        field_wdat += BitAnd(reg_wdat[field.end_bit:field.start_bit], self.p_unmask[field.end_bit:field.start_bit])
                    else:
                        field_wdat += reg_wdat[field.end_bit:field.start_bit]

                    if field.sw_write_one_pulse:    field_hw_rdat_reg+=BitAnd(field_wdat, field_lock_ena)
                    else:                           field_hw_rdat_reg+=BitAnd(Inverse(field_wdat), field_lock_ena)
                    
                    if field.hw_readable:
                        field_hw_rdat = self.set("%s_rdat" % field_name , Output(UInt(field.bit)))
                        field_hw_rdat += field_hw_rdat_reg 
                    rdat_list.append(field_hw_rdat_reg) 
                
                #===============================================================
                # Internal Register  
                #===============================================================
                else:
                    field_name = "%s_%s" % (sub_space.module_name, field.module_name)

                    if field.field_reg_write:
                        field_reg = self.set(field_name, Reg(UInt(field.bit,field.init_value),self.clk,rst))
                    else:
                        field_reg = UInt(field.bit,field.init_value)
                    reg_val = EmptyWhen()

                    if field.hw_writeable:
                        if not is_hw_write_clean_or_set:    field_hw_wdat = self.set("%s_wdat" % field_name , Input(UInt(field.bit)))
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
                            hw_flag = self.set("%s_hw_flag" % field_name, Reg(UInt(1,0),self.clk,rst))
                            hw_flag += when(field_hw_wena).then(UInt(1,1))
                            reg_val.when(BitAnd(field_hw_wena, Inverse(hw_flag))).then(field_hw_wdat)
                        else:
                            reg_val.when(field_hw_wena).then(field_hw_wdat)

                    if field.sw_writeable:
                        lock_intf_list = []
                        for lock in field.get_lock_list:
                            lock_field_name = f'{lock[0].module_name}_{lock[1].name}'
                            if hasattr(self, lock_field_name):  field_lock_inv = Inverse(getattr(self, lock_field_name))
                            else:                               field_lock_inv = Inverse(self.set(lock_field_name, Reg(UInt(lock[1].bit,lock[1].init_value),self.clk,rst)))
                            lock_intf_list.append(field_lock_inv)

                        field_write_enable = self.set('%s_sw_wren'% field_name, Wire(UInt(1)))
                        field_write_enable += BitAnd(reg_wvld, *lock_intf_list)

                        if not is_sw_write_clean_or_set:
                            field_wdat = self.set('%s_field_wdat'% field_name, Wire(UInt(field.bit)))
                            if is_apb4:
                                field_masked_wdat   = self.set('%s_masked_wdat'% field_name, Wire(UInt(field.bit)))
                                field_unmasked_wdat = self.set('%s_unmasked_wdat'% field_name, Wire(UInt(field.bit)))
                                field_masked_wdat   += BitAnd(field_reg, self.p_mask[field.end_bit:field.start_bit])
                                field_unmasked_wdat += BitAnd(reg_wdat[field.end_bit:field.start_bit], self.p_unmask[field.end_bit:field.start_bit])
                                field_wdat += BitOr(field_masked_wdat, field_unmasked_wdat)
                            else:
                                field_wdat += reg_wdat[field.end_bit:field.start_bit]

                        if field.sw_write_clean:
                            reg_val.when(field_write_enable).then(UInt(field.bit,0))
                        elif field.sw_write_one_to_clean:
                            reg_val.when(field_write_enable).then(BitAnd(field_wdat, field_reg))
                        elif field.sw_write_zero_to_clean:
                            reg_val.when(field_write_enable).then(BitAnd(field_wdat, field_reg))
                        elif field.sw_write_set:
                            reg_val.when(field_write_enable).then(UInt(field.bit,2**(field.bit)-1))
                        elif field.sw_write_one_to_set:
                            reg_val.when(field_write_enable).then(BitOr(field_wdat, field_reg))
                        elif field.sw_write_zero_to_set:
                            reg_val.when(field_write_enable).then(BitOr(Inverse(field_wdat), field_reg))
                        elif field.sw_write_one_to_toggle:
                            reg_val.when(field_write_enable).then(BitXor(field_wdat, field_reg))
                        elif field.sw_write_zero_to_toggle:
                            reg_val.when(field_write_enable).then(BitXnor(field_wdat, field_reg))
                        elif field.sw_write_once:
                            sw_flag = self.set("%s_sw_flag" % field_name, Reg(UInt(1,0),self.clk,rst))
                            sw_flag += when(field_write_enable).then(UInt(1,1))
                            reg_val.when(BitAnd(field_write_enable, Inverse(sw_flag))).then(field_wdat)
                        else:
                            reg_val.when(field_write_enable).then(field_wdat)

                    if field.hw_readable:
                        field_hw_rdat = self.set("%s_rdat" % field_name , Output(UInt(field.bit)))
                        
                        if field.hw_read_clean:
                            field_hw_rena = self.set("%s_rena" % field_name , Input(UInt(1)))
                            reg_val.when(field_hw_rena).then(UInt(field.bit,0))
                        elif field.hw_read_set:
                            field_hw_rena = self.set("%s_rena" % field_name , Input(UInt(1)))
                            reg_val.when(field_hw_rena).then(UInt(field.bit,2**(field.bit)-1))
                        
                        if sub_space.reg_type==IntrMask:
                            field_hw_rdat += BitAnd(getattr(self,f'{sub_space.module_name}_raw_status_{field.module_name}'), getattr(self,f'{sub_space.module_name}_enable_{field.module_name}'), Inverse(getattr(self,f'{sub_space.module_name}_mask_{field.module_name}')))
                        elif sub_space.reg_type==Intr:
                            field_hw_rdat += BitAnd(getattr(self,f'{sub_space.module_name}_raw_status_{field.module_name}'), getattr(self,f'{sub_space.module_name}_enable_{field.module_name}'))
                        else:
                            field_hw_rdat += field_reg
                          
                        
                    if field.sw_readable:
                        if field.sw_read_clean:     reg_val.when(reg_rvld).then(UInt(field.bit,0))
                        elif field.sw_read_set:     reg_val.when(reg_rvld).then(UInt(field.bit,2**(field.bit)-1))   
                        
                        if field.field_reg_write:   rdat_list.append(field_reg)
                        else:        
                            if hasattr(self, f"{field_name}_rdat"):
                                field_sw_rdat = getattr(self, f"{field_name}_rdat")
                            else:
                                field_sw_rdat = self.set("%s_rdat" % field_name , Wire(UInt(field.bit)))
                                field_sw_rdat += UInt(field.bit,field.init_value)
                            rdat_list.append(field_sw_rdat)
                    else:
                        rdat_list.append(UInt(field.bit,0))

                    # for clear and set interrupt register 
                    if sub_space.reg_type in [IntrStatus]:
                        field_set       = getattr(self, "%s_set_%s"% (sub_space.module_name.rstrip('_raw_status'),field.module_name))
                        field_clear     = getattr(self, "%s_clear_%s"% (sub_space.module_name.rstrip('_raw_status'),field.module_name))
                        reg_val.when(SelfOr(field_set)).then(BitOr(field_reg,field_set))
                        reg_val.when(SelfOr(field_clear)).then(BitAnd(field_reg,Inverse(field_clear)))

                    if field.field_reg_write:
                        field_reg += reg_val
                        

            #===============================================================
            #  Interrupt register logic
            #===============================================================
            if get_sw_readable(self._cfg.sub_space_list):
                rdat_list.reverse()
                if sub_space.reg_type==Intr:        reg_rdat += BitAnd(getattr(self,f'{sub_space.module_name}_raw_status_rdat'),getattr(self,f'{sub_space.module_name}_enable_rdat'))
                elif sub_space.reg_type==IntrMask:  reg_rdat += BitAnd(getattr(self,f'{sub_space.module_name}_raw_status_rdat'),getattr(self,f'{sub_space.module_name}_enable_rdat'),Inverse(getattr(self,f'{sub_space.module_name}_mask_rdat')))
                else:                               reg_rdat += Combine(*rdat_list)

            
            #===============================================================
            #  Add Parity logic 
            #===============================================================
            if sub_space.parity:
                # generate parity update always block
                parity_when = EmptyWhen()

                for sig in ['hw_wena', 'hw_rena', 'sw_wena', 'sw_rena']:
                    parity_list = getattr(sub_space, f'parity_{sig}_list')(self)
                    data_list   = getattr(sub_space, f'parity_{sig}_data_list')(self)
                    if parity_list!=[]:
                        ena  = self.set(f"{sub_space.module_name}_parity_{sig}", Wire(UInt(1)))
                        data = self.set(f"{sub_space.module_name}_parity_{sig}_wdata", Wire(UInt(self._cfg.data_width)))
                        parity_update = self.set(f"{sub_space.module_name}_parity_{sig}_update", Wire(UInt(int(self._cfg.data_width/8))))

                        ena           += Or(*parity_list)
                        data          += Combine(*data_list)
                        update_list   = [ SelfXor(data[i*8+7:i*8]) for i in range(int(self._cfg.data_width/8)) ]
                        update_list.reverse()
                        parity_update += Combine(*update_list)
                        parity_when.when(ena).then(parity_update) 

                if parity_when._attribute != None:      
                    parity_bit = self.set(f"{sub_space.module_name}_parity_bit", Reg(UInt(int(self._cfg.data_width/8), sub_space.parity_init_value), self.clk, rst))
                    parity_bit += parity_when
                else:                                   
                    parity_bit = self.set(f"{sub_space.module_name}_parity_bit", Wire(UInt(int(self._cfg.data_width/8), sub_space.parity_init_value)))
                    parity_bit += parity_bit.attribute

                # generate parity check 
                parity_check_bit = self.set(f"{sub_space.module_name}_parity_check_bit", Wire(UInt(int(self._cfg.data_width/8))))
                check_data       = self.set(f"{sub_space.module_name}_parity_check_wdata", Wire(UInt(self._cfg.data_width)))
                check_data_list  = getattr(sub_space, f'parity_field_data_list')(self)
                check_data += Combine(*check_data_list)
                check_list = [ SelfXor(data[i*8+7:i*8]) for i in range(int(self._cfg.data_width/8)) ]
                check_list.reverse()
                parity_check_bit += Combine(*check_list)
                parity_check_err = self.set(f"{sub_space.module_name}_parity_check_err", Wire(UInt(1)))
                parity_check_err += NotEqual(parity_check_bit, parity_bit)
                # hardware
                parity_hw_check_err = self.set(f"{sub_space.module_name}_parity_hw_check_err", Output(UInt(1)))
                parity_hw_check_err += parity_check_err
                # software
                parity_check_err_mux.when(Equal(self.rreq_addr,UInt(self._cfg.bus_width,start_address,'hex'))).then(parity_check_err)

        if hasattr(self, f"parity_sw_check_err"): 
            parity_check_err_mux.otherwise(UInt(1,0))  
            parity_sw_check_err = getattr(self, f"parity_sw_check_err")
            parity_sw_check_err += parity_check_err_mux


        ##########################################################################################################
        #  Register Level Interface 
        ##########################################################################################################
        if get_sw_readable(self._cfg.sub_space_list):
            rack_dat_read_mux.otherwise(UInt(self._cfg.data_width,2**(self._cfg.data_width)-2,'hex'))
            self.rack_data += rack_dat_read_mux

            if (not is_apb3) or apb3_has_rack_hsk:
                if not is_apb3:
                    self.rack_vld += UInt(1,1)
                else:
                    rack_read_mux.otherwise(UInt(1,0))
                    self.rack_vld  += rack_read_mux
        else:
            self.rack_data += UInt(self._cfg.data_width,0)
            if (not is_apb3) and apb3_has_rack_hsk:  self.rack_vld += UInt(1,0)

        if not is_apb3:
            if get_sw_writeable(self._cfg.sub_space_list):
                wreq_rdy_mux.otherwise(UInt(1,0))
                self.wreq_rdy  += wreq_rdy_mux
            else:
                self.wreq_rdy  += UInt(1,0)



        


                