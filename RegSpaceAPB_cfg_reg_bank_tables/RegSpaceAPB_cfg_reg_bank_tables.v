//[UHDL]Content Start [md5:27c780fd21d22b65512aafca4e1aedc9]
module RegSpaceAPB_cfg_reg_bank_tables (
	input         clk                     ,
	input         rst_n                   ,
	input  [15:0] p_addr                  ,
	input  [2:0]  p_prot                  ,
	input         p_sel                   ,
	input         p_enable                ,
	input         p_write                 ,
	input  [31:0] p_wdata                 ,
	input  [3:0]  p_strb                  ,
	output        p_ready                 ,
	output [31:0] p_rdata                 ,
	output        p_slverr                ,
	input         D_rs_reg0_field0_wdat   ,
	input         D_rs_reg0_field0_wvld   ,
	output        D_rs_reg0_field0_wrdy   ,
	output        D_rs_reg0_field0_rdat   ,
	output        D_rs_reg0_field0_rvld   ,
	input         D_rs_reg0_field0_rrdy   ,
	input         D_rs_reg0_field1_wdat   ,
	input         D_rs_reg0_field1_wvld   ,
	output        D_rs_reg0_field1_wrdy   ,
	output        D_rs_reg0_field1_rdat   ,
	output        D_rs_reg0_field1_rvld   ,
	input         D_rs_reg0_field1_rrdy   ,
	input         D_rs_reg0_field2_wdat   ,
	input         D_rs_reg0_field2_wvld   ,
	output        D_rs_reg0_field2_wrdy   ,
	output        D_rs_reg0_field2_rdat   ,
	output        D_rs_reg0_field2_rvld   ,
	input         D_rs_reg0_field2_rrdy   ,
	input         D_rs_reg1_sw_field3_rdat,
	output        D_rs_reg1_sw_field3_rvld,
	input         D_rs_reg1_sw_field3_rrdy,
	output        D_rs_reg1_sw_field3_wdat,
	output        D_rs_reg1_sw_field3_wvld,
	input         D_rs_reg1_sw_field3_wrdy,
	input         D_rs_reg1_sw_field4_rdat,
	output        D_rs_reg1_sw_field4_rvld,
	input         D_rs_reg1_sw_field4_rrdy,
	output        D_rs_reg1_sw_field4_wdat,
	output        D_rs_reg1_sw_field4_wvld,
	input         D_rs_reg1_sw_field4_wrdy,
	input         D_rs_reg1_sw_field5_rdat,
	output        D_rs_reg1_sw_field5_rvld,
	input         D_rs_reg1_sw_field5_rrdy,
	output        D_rs_reg1_sw_field5_wdat,
	output        D_rs_reg1_sw_field5_wvld,
	input         D_rs_reg1_sw_field5_wrdy);

	//Wire define for this module.
	reg  [0:0]  p_ready_r;
	wire [0:0]  p_rready ;
	wire [0:0]  p_wready ;
	reg  [31:0] p_rdata_r;

	//Wire define for sub module.
	wire        rs_clk      ;
	wire        rs_rst_n    ;
	wire [15:0] rs_rreq_addr;
	wire        rs_rreq_vld ;
	wire        rs_rreq_rdy ;
	wire [31:0] rs_rack_data;
	wire        rs_rack_vld ;
	wire        rs_rack_rdy ;
	wire [15:0] rs_wreq_addr;
	wire [31:0] rs_wreq_data;
	wire        rs_wreq_vld ;
	wire        rs_wreq_rdy ;

	//Wire define for Inout.

	//Wire sub module connect to this module and inter module connect.
	assign p_ready = p_ready_r;
	
	assign p_rdata = p_rdata_r;
	
	assign p_slverr = 1'b0;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) p_ready_r <= 1'b0;
	    else begin
	        if((p_rready || p_wready)) p_ready_r <= 1'b1;
	        else p_ready_r <= 1'b0;
	    end
	end
	
	assign p_rready = (rs_rreq_vld && rs_rreq_rdy);
	
	assign p_wready = rs_wreq_rdy;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) p_rdata_r <= 32'b0;
	    else begin
	        if((rs_rreq_vld && rs_rreq_rdy)) p_rdata_r <= rs_rack_data;
	        else p_rdata_r <= 32'b0;
	    end
	end
	

	//Wire this module connect to sub module.
	assign rs_clk = clk;
	
	assign rs_rst_n = rst_n;
	
	assign rs_rreq_addr = p_addr;
	
	assign rs_rreq_vld = ((!p_write) && p_sel);
	
	assign rs_rack_rdy = ((!p_write) && p_sel && p_enable);
	
	assign rs_wreq_addr = p_addr;
	
	assign rs_wreq_data = {(p_wdata[7:0] & {p_strb[0:0], p_strb[0:0], p_strb[0:0], p_strb[0:0], p_strb[0:0], p_strb[0:0], p_strb[0:0], p_strb[0:0]}), (p_wdata[15:8] & {p_strb[1:1], p_strb[1:1], p_strb[1:1], p_strb[1:1], p_strb[1:1], p_strb[1:1], p_strb[1:1], p_strb[1:1]}), (p_wdata[23:16] & {p_strb[2:2], p_strb[2:2], p_strb[2:2], p_strb[2:2], p_strb[2:2], p_strb[2:2], p_strb[2:2], p_strb[2:2]}), (p_wdata[31:24] & {p_strb[3:3], p_strb[3:3], p_strb[3:3], p_strb[3:3], p_strb[3:3], p_strb[3:3], p_strb[3:3], p_strb[3:3]})};
	
	assign rs_wreq_vld = (p_write && p_sel && p_enable);
	

	//module inst.
	RegSpaceBase_cfg_reg_bank_tables rs (
		.clk(rs_clk),
		.rst_n(rs_rst_n),
		.rreq_addr(rs_rreq_addr),
		.rreq_vld(rs_rreq_vld),
		.rreq_rdy(rs_rreq_rdy),
		.rack_data(rs_rack_data),
		.rack_vld(rs_rack_vld),
		.rack_rdy(rs_rack_rdy),
		.wreq_addr(rs_wreq_addr),
		.wreq_data(rs_wreq_data),
		.wreq_vld(rs_wreq_vld),
		.wreq_rdy(rs_wreq_rdy),
		.reg0_field0_wdat(D_rs_reg0_field0_wdat),
		.reg0_field0_wvld(D_rs_reg0_field0_wvld),
		.reg0_field0_wrdy(D_rs_reg0_field0_wrdy),
		.reg0_field0_rdat(D_rs_reg0_field0_rdat),
		.reg0_field0_rvld(D_rs_reg0_field0_rvld),
		.reg0_field0_rrdy(D_rs_reg0_field0_rrdy),
		.reg0_field1_wdat(D_rs_reg0_field1_wdat),
		.reg0_field1_wvld(D_rs_reg0_field1_wvld),
		.reg0_field1_wrdy(D_rs_reg0_field1_wrdy),
		.reg0_field1_rdat(D_rs_reg0_field1_rdat),
		.reg0_field1_rvld(D_rs_reg0_field1_rvld),
		.reg0_field1_rrdy(D_rs_reg0_field1_rrdy),
		.reg0_field2_wdat(D_rs_reg0_field2_wdat),
		.reg0_field2_wvld(D_rs_reg0_field2_wvld),
		.reg0_field2_wrdy(D_rs_reg0_field2_wrdy),
		.reg0_field2_rdat(D_rs_reg0_field2_rdat),
		.reg0_field2_rvld(D_rs_reg0_field2_rvld),
		.reg0_field2_rrdy(D_rs_reg0_field2_rrdy),
		.reg1_sw_field3_rdat(D_rs_reg1_sw_field3_rdat),
		.reg1_sw_field3_rvld(D_rs_reg1_sw_field3_rvld),
		.reg1_sw_field3_rrdy(D_rs_reg1_sw_field3_rrdy),
		.reg1_sw_field3_wdat(D_rs_reg1_sw_field3_wdat),
		.reg1_sw_field3_wvld(D_rs_reg1_sw_field3_wvld),
		.reg1_sw_field3_wrdy(D_rs_reg1_sw_field3_wrdy),
		.reg1_sw_field4_rdat(D_rs_reg1_sw_field4_rdat),
		.reg1_sw_field4_rvld(D_rs_reg1_sw_field4_rvld),
		.reg1_sw_field4_rrdy(D_rs_reg1_sw_field4_rrdy),
		.reg1_sw_field4_wdat(D_rs_reg1_sw_field4_wdat),
		.reg1_sw_field4_wvld(D_rs_reg1_sw_field4_wvld),
		.reg1_sw_field4_wrdy(D_rs_reg1_sw_field4_wrdy),
		.reg1_sw_field5_rdat(D_rs_reg1_sw_field5_rdat),
		.reg1_sw_field5_rvld(D_rs_reg1_sw_field5_rvld),
		.reg1_sw_field5_rrdy(D_rs_reg1_sw_field5_rrdy),
		.reg1_sw_field5_wdat(D_rs_reg1_sw_field5_wdat),
		.reg1_sw_field5_wvld(D_rs_reg1_sw_field5_wvld),
		.reg1_sw_field5_wrdy(D_rs_reg1_sw_field5_wrdy));

endmodule
//[UHDL]Content End [md5:27c780fd21d22b65512aafca4e1aedc9]

