//[UHDL]Content Start [md5:2b51d440e99b1e3fce0867615656f15a]
module RegSpaceBase_cfg_reg_bank_A (
	input             clk                   ,
	input             rst_n                 ,
	input      [15:0] rreq_addr             ,
	input             rreq_vld              ,
	output            rreq_rdy              ,
	output reg [31:0] rack_data             ,
	output reg        rack_vld              ,
	input             rack_rdy              ,
	input      [15:0] wreq_addr             ,
	input      [31:0] wreq_data             ,
	input             wreq_vld              ,
	output reg        wreq_rdy              ,
	input             reg_bank_A_field0_wdat,
	input             reg_bank_A_field0_wvld,
	output            reg_bank_A_field0_wrdy,
	output            reg_bank_A_field0_rdat,
	output            reg_bank_A_field0_rvld,
	input             reg_bank_A_field0_rrdy,
	input             reg_bank_A_field1_wdat,
	input             reg_bank_A_field1_wvld,
	output            reg_bank_A_field1_wrdy,
	output            reg_bank_A_field1_rdat,
	output            reg_bank_A_field1_rvld,
	input             reg_bank_A_field1_rrdy,
	output            reg_bank_A_field3_rdat,
	output            reg_bank_A_field3_rvld,
	input             reg_bank_A_field3_rrdy,
	output            reg_bank_A_field4_rdat,
	output            reg_bank_A_field4_rvld,
	input             reg_bank_A_field4_rrdy);

	//Wire define for this module.
	wire [31:0] reg_bank_A_rdat  ;
	wire [0:0]  reg_bank_A_rrdy  ;
	wire [0:0]  reg_bank_A_rvld  ;
	wire [31:0] reg_bank_A_wdat  ;
	wire [0:0]  reg_bank_A_wrdy  ;
	wire [0:0]  reg_bank_A_wvld  ;
	reg  [0:0]  reg_bank_A_field0;
	reg  [0:0]  reg_bank_A_field1;
	reg  [0:0]  reg_bank_A_field3;
	reg  [0:0]  reg_bank_A_field4;

	//Wire define for sub module.

	//Wire define for Inout.

	//Wire sub module connect to this module and inter module connect.
	assign rreq_rdy = (rack_rdy && rack_vld);
	
	always @(*) begin
	    if((rreq_addr == 16'b0)) rack_data = reg_bank_A_rdat;
	    else if((rreq_addr == 16'b1)) rack_data = reg_bank_A_rdat;
	    else rack_data = 32'b0;
	end
	
	always @(*) begin
	    if((rreq_addr == 16'b0)) rack_vld = reg_bank_A_rrdy;
	    else if((rreq_addr == 16'b1)) rack_vld = reg_bank_A_rrdy;
	    else rack_vld = 1'b0;
	end
	
	always @(*) begin
	    if((wreq_addr == 16'b0)) wreq_rdy = reg_bank_A_wrdy;
	    else if((wreq_addr == 16'b1)) wreq_rdy = reg_bank_A_wrdy;
	    else wreq_rdy = 1'b0;
	end
	
	assign reg_bank_A_rdat = {reg_bank_A_field3, 2'b0, reg_bank_A_field4, 28'b0};
	
	assign reg_bank_A_rrdy = 1'b1;
	
	assign reg_bank_A_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'b1));
	
	assign reg_bank_A_wdat = wreq_data[31:0];
	
	assign reg_bank_A_wrdy = 1'b1;
	
	assign reg_bank_A_wvld = (wreq_vld && (wreq_addr == 16'b1));
	
	assign reg_bank_A_field0_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg_bank_A_field0 <= 1'b0;
	    else begin
	        if(reg_bank_A_field0_wvld) reg_bank_A_field0 <= reg_bank_A_field0_wdat;
	    end
	end
	
	assign reg_bank_A_field0_rdat = reg_bank_A_field0;
	
	assign reg_bank_A_field0_rvld = 1'b1;
	
	assign reg_bank_A_field1_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg_bank_A_field1 <= 1'b0;
	    else begin
	        if(reg_bank_A_field1_wvld) reg_bank_A_field1 <= reg_bank_A_field1_wdat;
	        else if(reg_bank_A_wvld) reg_bank_A_field1 <= reg_bank_A_wdat[3:3];
	    end
	end
	
	assign reg_bank_A_field1_rdat = reg_bank_A_field1;
	
	assign reg_bank_A_field1_rvld = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg_bank_A_field3 <= 1'b0;
	    else begin
	        if(reg_bank_A_wvld) reg_bank_A_field3 <= reg_bank_A_wdat[0:0];
	    end
	end
	
	assign reg_bank_A_field3_rdat = reg_bank_A_field3;
	
	assign reg_bank_A_field3_rvld = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg_bank_A_field4 <= 1'b0;
	    else begin
	        if(reg_bank_A_wvld) reg_bank_A_field4 <= reg_bank_A_wdat[3:3];
	    end
	end
	
	assign reg_bank_A_field4_rdat = reg_bank_A_field4;
	
	assign reg_bank_A_field4_rvld = 1'b1;
	

	//Wire this module connect to sub module.

	//module inst.

endmodule
//[UHDL]Content End [md5:2b51d440e99b1e3fce0867615656f15a]

