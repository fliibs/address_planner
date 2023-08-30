import uvm_pkg::*;
`include "uvm_macros.svh"
import yuu_apb_pkg::*;

module tb_top;
    logic v_clk;
    logic v_rst_n;

    initial begin
        v_rst_n=0;
        #100ns;
        v_rst_n=1;
    end

    initial begin
        v_clk=0;
        forever begin
          #100ns;
          v_clk=~v_clk;
        end
    end

    initial begin
        #10000ns;
        $finish;
    end
    
    initial begin
        //$fsdbDumpvars(0,tb_top,"+all");
        $fsdbDumpvars();
        $fsdbDumpfile("tb_top.fsdb");
        //$fsdbDumpflush;
    end
    
    RegSpaceAPB_cfg_reg_bank_tables u_dut();

    yuu_apb_interface yuu_apb_if();

    initial begin
      uvm_config_db#(virtual yuu_apb_interface)::set(null, "*", "vif", yuu_apb_if);
      run_test();
    end

    initial begin
        force  u_dut.clk=v_clk;                             
        force  u_dut.rst_n=v_rst_n;                          
        force  u_dut.p_addr=yuu_apb_if.master_if[0].paddr;                          
        force  u_dut.p_prot= yuu_apb_if.master_if[0].pprot;                        
        force  u_dut.p_sel= yuu_apb_if.master_if[0].psel;                          
        force  u_dut.p_enable=yuu_apb_if.master_if[0].penable;                        
        force  u_dut.p_write= yuu_apb_if.master_if[0].pwrite;                        
        force  u_dut.p_wdata= yuu_apb_if.master_if[0].pwdata;                       
        force  u_dut.p_strb= yuu_apb_if.master_if[0].pstrb;                         
        force u_dut.D_rs_internal_reg_field0_wdat=0   ;
        force u_dut.D_rs_internal_reg_field0_wvld=0   ;
        force u_dut.D_rs_internal_reg_field0_rrdy=0   ;
        force u_dut.D_rs_internal_reg_field1_wdat=0   ;
        force u_dut.D_rs_internal_reg_field1_wvld=0   ;
        force u_dut.D_rs_internal_reg_field1_rrdy=0   ;
        force u_dut.D_rs_internal_reg_field2_wdat=0   ;
        force u_dut.D_rs_internal_reg_field2_wvld=0   ;
        force u_dut.D_rs_internal_reg_field2_rrdy=0   ;
        force u_dut.D_rs_internal_reg_field3_rrdy=0   ;
        force u_dut.D_rs_external_reg_sw_field0_rdat=0;
        force u_dut.D_rs_external_reg_sw_field0_rrdy=0;
        force u_dut.D_rs_external_reg_sw_field0_wrdy=0;
        force u_dut.D_rs_external_reg_sw_field1_rdat=0;
        force u_dut.D_rs_external_reg_sw_field1_rrdy=0;
        force u_dut.D_rs_external_reg_sw_field1_wrdy=0;
        force u_dut.D_rs_external_reg_sw_field2_rdat=0;
        force u_dut.D_rs_external_reg_sw_field2_rrdy=0;
        force u_dut.D_rs_external_reg_sw_field2_wrdy=0;
        force u_dut.D_rs_external_reg_sw_field3_rdat=0;
        force u_dut.D_rs_external_reg_sw_field3_rrdy=0;
        force u_dut.D_rs_external_reg_sw_field3_wrdy=0;
                
        force yuu_apb_if.master_if[0].prdata=u_dut.p_rdata;
        force yuu_apb_if.master_if[0].pready=u_dut.p_ready;
        force yuu_apb_if.master_if[0].pslverr=u_dut.p_slverr;
    
    //	output        D_rs_internal_reg_field1_wrdy   ,
    //	output [1:0]  D_rs_internal_reg_field1_rdat   ,
    //	output        D_rs_internal_reg_field1_rvld   ,
    //	output        D_rs_internal_reg_field2_wrdy   ,
    //	output        D_rs_internal_reg_field2_rdat   ,
    //	output        D_rs_internal_reg_field2_rvld   ,
    //	output [2:0]  D_rs_internal_reg_field3_rdat   ,
    //	output        D_rs_internal_reg_field3_rvld   ,
    //	output        D_rs_external_reg_sw_field0_rvld,
    //	output        D_rs_external_reg_sw_field0_wdat,
    //	output        D_rs_external_reg_sw_field0_wvld,
    //	output        D_rs_external_reg_sw_field1_rvld,
    //	output        D_rs_external_reg_sw_field1_wdat,
    //	output        D_rs_external_reg_sw_field1_wvld,
    //	output        D_rs_external_reg_sw_field2_rvld,
    	//output [2:0]  D_rs_external_reg_sw_field2_wdat,
    	//output        D_rs_external_reg_sw_field2_wvld,
    	//output        D_rs_external_reg_sw_field3_rvld,
    	//output [3:0]  D_rs_external_reg_sw_field3_wdat,
    	//output        D_rs_external_reg_sw_field3_wvld,
    	//output        D_rs_internal_reg_field0_wrdy   ,
    	//output        D_rs_internal_reg_field0_rdat   ,
    	//output        D_rs_internal_reg_field0_rvld   ,
    end
    
    
    initial begin
      force yuu_apb_if.pclk=v_clk;
      force yuu_apb_if.preset_n=v_rst_n;
    end
endmodule 


`include  "ral_block_reg_bank_tables.sv"
`include  "yuu_apb_base_case.sv"
