//[UHDL]Content Start [md5:0812e37c77c7cdbfc05122521b3557f3]
module RegSpaceAPB_cfg_reg_bank_A (
	input         clk     ,
	input         rst_n   ,
	input  [15:0] p_addr  ,
	input  [2:0]  p_prot  ,
	input         p_sel   ,
	input         p_enable,
	input         p_write ,
	input  [31:0] p_wdata ,
	input  [3:0]  p_strb  ,
	output        p_ready ,
	output [31:0] p_rdata ,
	output        p_slverr);

	//Wire define for this module.
	reg  [0:0]  p_ready_r;
	wire [0:0]  p_rready ;
	wire [0:0]  p_wready ;
	reg  [31:0] p_rdata_r;

	//Wire define for sub module.
	wire        rs_clk                   ;
	wire        rs_rst_n                 ;
	wire [15:0] rs_rreq_addr             ;
	wire        rs_rreq_vld              ;
	wire        rs_rreq_rdy              ;
	wire [31:0] rs_rack_data             ;
	wire        rs_rack_vld              ;
	wire        rs_rack_rdy              ;
	wire [15:0] rs_wreq_addr             ;
	wire [31:0] rs_wreq_data             ;
	wire        rs_wreq_vld              ;
	wire        rs_wreq_rdy              ;
	wire        rs_reg_bank_A_field0_wdat;
	wire        rs_reg_bank_A_field0_wvld;
	wire        rs_reg_bank_A_field0_wrdy;
	wire        rs_reg_bank_A_field0_rdat;
	wire        rs_reg_bank_A_field0_rvld;
	wire        rs_reg_bank_A_field0_rrdy;
	wire        rs_reg_bank_A_field1_wdat;
	wire        rs_reg_bank_A_field1_wvld;
	wire        rs_reg_bank_A_field1_wrdy;
	wire        rs_reg_bank_A_field1_rdat;
	wire        rs_reg_bank_A_field1_rvld;
	wire        rs_reg_bank_A_field1_rrdy;
	wire        rs_reg_bank_A_field3_rdat;
	wire        rs_reg_bank_A_field3_rvld;
	wire        rs_reg_bank_A_field3_rrdy;
	wire        rs_reg_bank_A_field4_rdat;
	wire        rs_reg_bank_A_field4_rvld;
	wire        rs_reg_bank_A_field4_rrdy;

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
	
	assign p_rready = (rreq_vld && rs_rreq_rdy);
	
	assign p_wready = rs_wreq_rdy;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) p_rdata_r <= 32'b0;
	    else begin
	        if((rreq_vld && rs_rreq_rdy)) p_rdata_r <= rs_rack_data;
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
	RegSpaceBase_cfg_reg_bank_A rs (
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
		.reg_bank_A_field0_wdat(rs_reg_bank_A_field0_wdat),
		.reg_bank_A_field0_wvld(rs_reg_bank_A_field0_wvld),
		.reg_bank_A_field0_wrdy(rs_reg_bank_A_field0_wrdy),
		.reg_bank_A_field0_rdat(rs_reg_bank_A_field0_rdat),
		.reg_bank_A_field0_rvld(rs_reg_bank_A_field0_rvld),
		.reg_bank_A_field0_rrdy(rs_reg_bank_A_field0_rrdy),
		.reg_bank_A_field1_wdat(rs_reg_bank_A_field1_wdat),
		.reg_bank_A_field1_wvld(rs_reg_bank_A_field1_wvld),
		.reg_bank_A_field1_wrdy(rs_reg_bank_A_field1_wrdy),
		.reg_bank_A_field1_rdat(rs_reg_bank_A_field1_rdat),
		.reg_bank_A_field1_rvld(rs_reg_bank_A_field1_rvld),
		.reg_bank_A_field1_rrdy(rs_reg_bank_A_field1_rrdy),
		.reg_bank_A_field3_rdat(rs_reg_bank_A_field3_rdat),
		.reg_bank_A_field3_rvld(rs_reg_bank_A_field3_rvld),
		.reg_bank_A_field3_rrdy(rs_reg_bank_A_field3_rrdy),
		.reg_bank_A_field4_rdat(rs_reg_bank_A_field4_rdat),
		.reg_bank_A_field4_rvld(rs_reg_bank_A_field4_rvld),
		.reg_bank_A_field4_rrdy(rs_reg_bank_A_field4_rrdy));

endmodule
//[UHDL]Content End [md5:0812e37c77c7cdbfc05122521b3557f3]

