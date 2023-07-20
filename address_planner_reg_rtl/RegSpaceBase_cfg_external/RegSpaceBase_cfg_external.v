//[UHDL]Content Start [md5:76295c8d75383f2b7967c93341a70003]
module RegSpaceBase_cfg_external (
	input             clk                ,
	input             rst_n              ,
	input      [15:0] rreq_addr          ,
	input             rreq_vld           ,
	output            rreq_rdy           ,
	output reg [31:0] rack_data          ,
	output reg        rack_vld           ,
	input             rack_rdy           ,
	input      [15:0] wreq_addr          ,
	input      [31:0] wreq_data          ,
	input             wreq_vld           ,
	output reg        wreq_rdy           ,
	input             reg0_sw_field1_rdat,
	output            reg0_sw_field1_rvld,
	input             reg0_sw_field1_rrdy,
	output            reg0_sw_field1_wdat,
	output            reg0_sw_field1_wvld,
	input             reg0_sw_field1_wrdy,
	input      [1:0]  reg0_sw_field2_rdat,
	output            reg0_sw_field2_rvld,
	input             reg0_sw_field2_rrdy,
	output     [1:0]  reg0_sw_field2_wdat,
	output            reg0_sw_field2_wvld,
	input             reg0_sw_field2_wrdy,
	input      [2:0]  reg0_sw_field3_rdat,
	output            reg0_sw_field3_rvld,
	input             reg0_sw_field3_rrdy,
	output     [2:0]  reg0_sw_field3_wdat,
	output            reg0_sw_field3_wvld,
	input             reg0_sw_field3_wrdy,
	input             reg1_sw_field1_rdat,
	output            reg1_sw_field1_rvld,
	input             reg1_sw_field1_rrdy,
	output            reg1_sw_field1_wdat,
	output            reg1_sw_field1_wvld,
	input             reg1_sw_field1_wrdy,
	input      [1:0]  reg1_sw_field2_rdat,
	output            reg1_sw_field2_rvld,
	input             reg1_sw_field2_rrdy,
	output     [1:0]  reg1_sw_field2_wdat,
	output            reg1_sw_field2_wvld,
	input             reg1_sw_field2_wrdy,
	input      [2:0]  reg1_sw_field3_rdat,
	output            reg1_sw_field3_rvld,
	input             reg1_sw_field3_rrdy,
	output     [2:0]  reg1_sw_field3_wdat,
	output            reg1_sw_field3_wvld,
	input             reg1_sw_field3_wrdy);

	//Wire define for this module.
	wire [31:0] reg0_rdat;
	wire [0:0]  reg0_rrdy;
	wire [0:0]  reg0_rvld;
	wire [31:0] reg0_wdat;
	wire [0:0]  reg0_wrdy;
	wire [0:0]  reg0_wvld;
	wire [31:0] reg1_rdat;
	wire [0:0]  reg1_rrdy;
	wire [0:0]  reg1_rvld;
	wire [31:0] reg1_wdat;
	wire [0:0]  reg1_wrdy;
	wire [0:0]  reg1_wvld;

	//Wire define for sub module.

	//Wire define for Inout.

	//Wire sub module connect to this module and inter module connect.
	assign rreq_rdy = (rack_rdy && rack_vld);
	
	always @(*) begin
	    if((rreq_addr == 16'b0)) rack_data = reg0_rdat;
	    else if((rreq_addr == 16'b100000)) rack_data = reg1_rdat;
	    else rack_data = 32'b0;
	end
	
	always @(*) begin
	    if((rreq_addr == 16'b0)) rack_vld = reg0_rrdy;
	    else if((rreq_addr == 16'b100000)) rack_vld = reg1_rrdy;
	    else rack_vld = 1'b0;
	end
	
	always @(*) begin
	    if((wreq_addr == 16'b0)) wreq_rdy = reg0_wrdy;
	    else if((wreq_addr == 16'b100000)) wreq_rdy = reg1_wrdy;
	    else wreq_rdy = 1'b0;
	end
	
	assign reg0_rdat = {reg0_sw_field1_rdat, 1'b0, reg0_sw_field2_rdat, reg0_sw_field3_rdat, 25'b0};
	
	assign reg0_rrdy = 1'b1;
	
	assign reg0_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'b0));
	
	assign reg0_wdat = wreq_data[31:0];
	
	assign reg0_wrdy = 1'b1;
	
	assign reg0_wvld = (wreq_vld && (wreq_addr == 16'b0));
	
	assign reg0_sw_field1_rvld = reg0_rvld;
	
	assign reg0_sw_field1_wdat = reg0_wdat[0:0];
	
	assign reg0_sw_field1_wvld = reg0_wvld;
	
	assign reg0_sw_field2_rvld = reg0_rvld;
	
	assign reg0_sw_field2_wdat = reg0_wdat[3:2];
	
	assign reg0_sw_field2_wvld = reg0_wvld;
	
	assign reg0_sw_field3_rvld = reg0_rvld;
	
	assign reg0_sw_field3_wdat = reg0_wdat[6:4];
	
	assign reg0_sw_field3_wvld = reg0_wvld;
	
	assign reg1_rdat = {reg1_sw_field1_rdat, 1'b0, reg1_sw_field2_rdat, reg1_sw_field3_rdat, 25'b0};
	
	assign reg1_rrdy = 1'b1;
	
	assign reg1_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'b100000));
	
	assign reg1_wdat = wreq_data[31:0];
	
	assign reg1_wrdy = 1'b1;
	
	assign reg1_wvld = (wreq_vld && (wreq_addr == 16'b100000));
	
	assign reg1_sw_field1_rvld = reg1_rvld;
	
	assign reg1_sw_field1_wdat = reg1_wdat[0:0];
	
	assign reg1_sw_field1_wvld = reg1_wvld;
	
	assign reg1_sw_field2_rvld = reg1_rvld;
	
	assign reg1_sw_field2_wdat = reg1_wdat[3:2];
	
	assign reg1_sw_field2_wvld = reg1_wvld;
	
	assign reg1_sw_field3_rvld = reg1_rvld;
	
	assign reg1_sw_field3_wdat = reg1_wdat[6:4];
	
	assign reg1_sw_field3_wvld = reg1_wvld;
	

	//Wire this module connect to sub module.

	//module inst.

endmodule
//[UHDL]Content End [md5:76295c8d75383f2b7967c93341a70003]

