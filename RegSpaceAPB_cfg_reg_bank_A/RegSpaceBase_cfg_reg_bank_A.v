//[UHDL]Content Start [md5:64eebb0de2a411c18d9ca4d014ed74d0]
module RegSpaceBase_cfg_reg_bank_A (
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
	input             reg0_sw_field0_rdat,
	output            reg0_sw_field0_rvld,
	input             reg0_sw_field0_rrdy,
	output            reg0_sw_field0_wdat,
	output            reg0_sw_field0_wvld,
	input             reg0_sw_field0_wrdy,
	input             reg0_sw_field1_rdat,
	output            reg0_sw_field1_rvld,
	input             reg0_sw_field1_rrdy,
	output            reg0_sw_field1_wdat,
	output            reg0_sw_field1_wvld,
	input             reg0_sw_field1_wrdy,
	input             reg0_sw_field2_rdat,
	output            reg0_sw_field2_rvld,
	input             reg0_sw_field2_rrdy,
	output            reg0_sw_field2_wdat,
	output            reg0_sw_field2_wvld,
	input             reg0_sw_field2_wrdy,
	output            reg0_field3_rdat   ,
	output            reg0_field3_rvld   ,
	input             reg0_field3_rrdy   ,
	input             reg0_field4_wdat   ,
	input             reg0_field4_wvld   ,
	output            reg0_field4_wrdy   ,
	input             reg0_field5_wdat   ,
	input             reg0_field5_wvld   ,
	output            reg0_field5_wrdy   ,
	output            reg0_field5_rdat   ,
	output            reg0_field5_rvld   ,
	input             reg0_field5_rrdy   ,
	input      [1:0]  reg0_field6_wdat   ,
	input             reg0_field6_wvld   ,
	output            reg0_field6_wrdy   ,
	output     [1:0]  reg0_field6_rdat   ,
	output            reg0_field6_rvld   ,
	input             reg0_field6_rrdy   ,
	input             reg1_sw_field0_rdat,
	output            reg1_sw_field0_rvld,
	input             reg1_sw_field0_rrdy,
	output            reg1_sw_field0_wdat,
	output            reg1_sw_field0_wvld,
	input             reg1_sw_field0_wrdy,
	input             reg1_sw_field1_rdat,
	output            reg1_sw_field1_rvld,
	input             reg1_sw_field1_rrdy,
	output            reg1_sw_field1_wdat,
	output            reg1_sw_field1_wvld,
	input             reg1_sw_field1_wrdy,
	input             reg1_sw_field2_rdat,
	output            reg1_sw_field2_rvld,
	input             reg1_sw_field2_rrdy,
	output            reg1_sw_field2_wdat,
	output            reg1_sw_field2_wvld,
	input             reg1_sw_field2_wrdy,
	output            reg1_field3_rdat   ,
	output            reg1_field3_rvld   ,
	input             reg1_field3_rrdy   ,
	input             reg1_field4_wdat   ,
	input             reg1_field4_wvld   ,
	output            reg1_field4_wrdy   ,
	input             reg1_field5_wdat   ,
	input             reg1_field5_wvld   ,
	output            reg1_field5_wrdy   ,
	output            reg1_field5_rdat   ,
	output            reg1_field5_rvld   ,
	input             reg1_field5_rrdy   ,
	input      [1:0]  reg1_field6_wdat   ,
	input             reg1_field6_wvld   ,
	output            reg1_field6_wrdy   ,
	output     [1:0]  reg1_field6_rdat   ,
	output            reg1_field6_rvld   ,
	input             reg1_field6_rrdy   );

	//Wire define for this module.
	wire [31:0] reg0_rdat  ;
	wire [0:0]  reg0_rrdy  ;
	wire [0:0]  reg0_rvld  ;
	wire [31:0] reg0_wdat  ;
	wire [0:0]  reg0_wrdy  ;
	wire [0:0]  reg0_wvld  ;
	reg  [0:0]  reg0_field3;
	reg  [0:0]  reg0_field4;
	reg  [0:0]  reg0_field5;
	reg  [1:0]  reg0_field6;
	wire [31:0] reg1_rdat  ;
	wire [0:0]  reg1_rrdy  ;
	wire [0:0]  reg1_rvld  ;
	wire [31:0] reg1_wdat  ;
	wire [0:0]  reg1_wrdy  ;
	wire [0:0]  reg1_wvld  ;
	reg  [0:0]  reg1_field3;
	reg  [0:0]  reg1_field4;
	reg  [0:0]  reg1_field5;
	reg  [1:0]  reg1_field6;

	//Wire define for sub module.

	//Wire define for Inout.

	//Wire sub module connect to this module and inter module connect.
	assign rreq_rdy = (rack_rdy && rack_vld);
	
	always @(*) begin
	    if((rreq_addr == 16'b0)) rack_data = reg0_rdat;
	    else if((rreq_addr == 16'b1)) rack_data = reg1_rdat;
	    else rack_data = 32'b0;
	end
	
	always @(*) begin
	    if((rreq_addr == 16'b0)) rack_vld = reg0_rrdy;
	    else if((rreq_addr == 16'b1)) rack_vld = reg1_rrdy;
	    else rack_vld = 1'b0;
	end
	
	always @(*) begin
	    if((wreq_addr == 16'b0)) wreq_rdy = reg0_wrdy;
	    else if((wreq_addr == 16'b1)) wreq_rdy = reg1_wrdy;
	    else wreq_rdy = 1'b0;
	end
	
	assign reg0_rdat = {reg0_sw_field0_rdat, 2'b0, reg0_sw_field1_rdat, 1'b0, reg0_sw_field2_rdat, 1'b0, reg0_field3, 1'b0, reg0_field4, 1'b0, reg0_field5, 1'b0, reg0_field6, 17'b0};
	
	assign reg0_rrdy = 1'b1;
	
	assign reg0_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'b0));
	
	assign reg0_wdat = wreq_data[31:0];
	
	assign reg0_wrdy = 1'b1;
	
	assign reg0_wvld = (wreq_vld && (wreq_addr == 16'b0));
	
	assign reg0_sw_field0_rvld = reg0_rvld;
	
	assign reg0_sw_field0_wdat = reg0_wdat[0:0];
	
	assign reg0_sw_field0_wvld = reg0_wvld;
	
	assign reg0_sw_field1_rvld = reg0_rvld;
	
	assign reg0_sw_field1_wdat = reg0_wdat[3:3];
	
	assign reg0_sw_field1_wvld = reg0_wvld;
	
	assign reg0_sw_field2_rvld = reg0_rvld;
	
	assign reg0_sw_field2_wdat = reg0_wdat[5:5];
	
	assign reg0_sw_field2_wvld = reg0_wvld;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field3 <= 1'b0;
	    else begin
	        if(reg0_wvld) reg0_field3 <= reg0_wdat[7:7];
	    end
	end
	
	assign reg0_field3_rdat = reg0_field3;
	
	assign reg0_field3_rvld = 1'b1;
	
	assign reg0_field4_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field4 <= 1'b0;
	    else begin
	        if(reg0_field4_wvld) reg0_field4 <= reg0_field4_wdat;
	        else if(reg0_wvld) reg0_field4 <= reg0_wdat[9:9];
	    end
	end
	
	assign reg0_field5_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field5 <= 1'b0;
	    else begin
	        if(reg0_field5_wvld) reg0_field5 <= reg0_field5_wdat;
	        else if(reg0_wvld) reg0_field5 <= reg0_wdat[11:11];
	    end
	end
	
	assign reg0_field5_rdat = reg0_field5;
	
	assign reg0_field5_rvld = 1'b1;
	
	assign reg0_field6_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field6 <= 2'b0;
	    else begin
	        if(reg0_field6_wvld) reg0_field6 <= reg0_field6_wdat;
	        else if(reg0_rvld) reg0_field6 <= 2'b0;
	    end
	end
	
	assign reg0_field6_rdat = reg0_field6;
	
	assign reg0_field6_rvld = 1'b1;
	
	assign reg1_rdat = {reg1_sw_field0_rdat, 2'b0, reg1_sw_field1_rdat, 1'b0, reg1_sw_field2_rdat, 1'b0, reg1_field3, 1'b0, reg1_field4, 1'b0, reg1_field5, 1'b0, reg1_field6, 17'b0};
	
	assign reg1_rrdy = 1'b1;
	
	assign reg1_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'b1));
	
	assign reg1_wdat = wreq_data[31:0];
	
	assign reg1_wrdy = 1'b1;
	
	assign reg1_wvld = (wreq_vld && (wreq_addr == 16'b1));
	
	assign reg1_sw_field0_rvld = reg1_rvld;
	
	assign reg1_sw_field0_wdat = reg1_wdat[0:0];
	
	assign reg1_sw_field0_wvld = reg1_wvld;
	
	assign reg1_sw_field1_rvld = reg1_rvld;
	
	assign reg1_sw_field1_wdat = reg1_wdat[3:3];
	
	assign reg1_sw_field1_wvld = reg1_wvld;
	
	assign reg1_sw_field2_rvld = reg1_rvld;
	
	assign reg1_sw_field2_wdat = reg1_wdat[5:5];
	
	assign reg1_sw_field2_wvld = reg1_wvld;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field3 <= 1'b0;
	    else begin
	        if(reg1_wvld) reg1_field3 <= reg1_wdat[7:7];
	    end
	end
	
	assign reg1_field3_rdat = reg1_field3;
	
	assign reg1_field3_rvld = 1'b1;
	
	assign reg1_field4_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field4 <= 1'b0;
	    else begin
	        if(reg1_field4_wvld) reg1_field4 <= reg1_field4_wdat;
	        else if(reg1_wvld) reg1_field4 <= reg1_wdat[9:9];
	    end
	end
	
	assign reg1_field5_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field5 <= 1'b0;
	    else begin
	        if(reg1_field5_wvld) reg1_field5 <= reg1_field5_wdat;
	        else if(reg1_wvld) reg1_field5 <= reg1_wdat[11:11];
	    end
	end
	
	assign reg1_field5_rdat = reg1_field5;
	
	assign reg1_field5_rvld = 1'b1;
	
	assign reg1_field6_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field6 <= 2'b0;
	    else begin
	        if(reg1_field6_wvld) reg1_field6 <= reg1_field6_wdat;
	        else if(reg1_rvld) reg1_field6 <= 2'b0;
	    end
	end
	
	assign reg1_field6_rdat = reg1_field6;
	
	assign reg1_field6_rvld = 1'b1;
	

	//Wire this module connect to sub module.

	//module inst.

endmodule
//[UHDL]Content End [md5:64eebb0de2a411c18d9ca4d014ed74d0]

