//[UHDL]Content Start [md5:e560fd3f30589360658521e92ed9a9b0]
module RegSpaceBase_cfg_sw_no_read (
	input             clk                ,
	input             rst_n              ,
	input      [15:0] rreq_addr          ,
	input             rreq_vld           ,
	output            rreq_rdy           ,
	output     [31:0] rack_data          ,
	output            rack_vld           ,
	input             rack_rdy           ,
	input      [15:0] wreq_addr          ,
	input      [31:0] wreq_data          ,
	input             wreq_vld           ,
	output reg        wreq_rdy           ,
	output            reg0_sw_field1_wdat,
	output            reg0_sw_field1_wvld,
	input             reg0_sw_field1_wrdy,
	input      [1:0]  reg0_field2_wdat   ,
	input             reg0_field2_wvld   ,
	output            reg0_field2_wrdy   ,
	output     [1:0]  reg0_field2_rdat   ,
	output            reg0_field2_rvld   ,
	input             reg0_field2_rrdy   ,
	input      [2:0]  reg0_field3_wdat   ,
	input             reg0_field3_wvld   ,
	output            reg0_field3_wrdy   ,
	output     [2:0]  reg0_field3_rdat   ,
	output            reg0_field3_rvld   ,
	input             reg0_field3_rrdy   ,
	input      [3:0]  reg0_field4_wdat   ,
	input             reg0_field4_wvld   ,
	output            reg0_field4_wrdy   ,
	output     [3:0]  reg0_field4_rdat   ,
	output            reg0_field4_rvld   ,
	input             reg0_field4_rrdy   ,
	output            reg1_sw_field1_wdat,
	output            reg1_sw_field1_wvld,
	input             reg1_sw_field1_wrdy,
	input      [1:0]  reg1_field2_wdat   ,
	input             reg1_field2_wvld   ,
	output            reg1_field2_wrdy   ,
	output     [1:0]  reg1_field2_rdat   ,
	output            reg1_field2_rvld   ,
	input             reg1_field2_rrdy   ,
	input      [2:0]  reg1_field3_wdat   ,
	input             reg1_field3_wvld   ,
	output            reg1_field3_wrdy   ,
	output     [2:0]  reg1_field3_rdat   ,
	output            reg1_field3_rvld   ,
	input             reg1_field3_rrdy   ,
	input      [3:0]  reg1_field4_wdat   ,
	input             reg1_field4_wvld   ,
	output            reg1_field4_wrdy   ,
	output     [3:0]  reg1_field4_rdat   ,
	output            reg1_field4_rvld   ,
	input             reg1_field4_rrdy   );

	//Wire define for this module.
	wire [31:0] reg0_wdat  ;
	wire [0:0]  reg0_wrdy  ;
	wire [0:0]  reg0_wvld  ;
	reg  [1:0]  reg0_field2;
	reg  [2:0]  reg0_field3;
	reg  [3:0]  reg0_field4;
	wire [31:0] reg1_wdat  ;
	wire [0:0]  reg1_wrdy  ;
	wire [0:0]  reg1_wvld  ;
	reg  [1:0]  reg1_field2;
	reg  [2:0]  reg1_field3;
	reg  [3:0]  reg1_field4;

	//Wire define for sub module.

	//Wire define for Inout.

	//Wire sub module connect to this module and inter module connect.
	assign rreq_rdy = 1'b0;
	
	assign rack_data = 32'b0;
	
	assign rack_vld = 1'b0;
	
	always @(*) begin
	    if((wreq_addr == 16'b0)) wreq_rdy = reg0_wrdy;
	    else if((wreq_addr == 16'b100000)) wreq_rdy = reg1_wrdy;
	    else wreq_rdy = 1'b0;
	end
	
	assign reg0_wdat = wreq_data[31:0];
	
	assign reg0_wrdy = 1'b1;
	
	assign reg0_wvld = (wreq_vld && (wreq_addr == 16'b0));
	
	assign reg0_sw_field1_wdat = reg0_wdat[0:0];
	
	assign reg0_sw_field1_wvld = reg0_wvld;
	
	assign reg0_field2_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field2 <= 2'b0;
	    else begin
	        if(reg0_field2_wvld) reg0_field2 <= reg0_field2_wdat;
	        else if(reg0_wvld) reg0_field2 <= reg0_wdat[3:2];
	    end
	end
	
	assign reg0_field2_rdat = reg0_field2;
	
	assign reg0_field2_rvld = 1'b1;
	
	assign reg0_field3_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field3 <= 3'b0;
	    else begin
	        if(reg0_field3_wvld) reg0_field3 <= reg0_field3_wdat;
	        else if(reg0_wvld) reg0_field3 <= reg0_wdat[6:4];
	    end
	end
	
	assign reg0_field3_rdat = reg0_field3;
	
	assign reg0_field3_rvld = 1'b1;
	
	assign reg0_field4_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field4 <= 4'b0;
	    else begin
	        if(reg0_field4_wvld) reg0_field4 <= reg0_field4_wdat;
	        else if(reg0_wvld) reg0_field4 <= reg0_wdat[11:8];
	    end
	end
	
	assign reg0_field4_rdat = reg0_field4;
	
	assign reg0_field4_rvld = 1'b1;
	
	assign reg1_wdat = wreq_data[31:0];
	
	assign reg1_wrdy = 1'b1;
	
	assign reg1_wvld = (wreq_vld && (wreq_addr == 16'b100000));
	
	assign reg1_sw_field1_wdat = reg1_wdat[0:0];
	
	assign reg1_sw_field1_wvld = reg1_wvld;
	
	assign reg1_field2_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field2 <= 2'b0;
	    else begin
	        if(reg1_field2_wvld) reg1_field2 <= reg1_field2_wdat;
	        else if(reg1_wvld) reg1_field2 <= reg1_wdat[3:2];
	    end
	end
	
	assign reg1_field2_rdat = reg1_field2;
	
	assign reg1_field2_rvld = 1'b1;
	
	assign reg1_field3_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field3 <= 3'b0;
	    else begin
	        if(reg1_field3_wvld) reg1_field3 <= reg1_field3_wdat;
	        else if(reg1_wvld) reg1_field3 <= reg1_wdat[6:4];
	    end
	end
	
	assign reg1_field3_rdat = reg1_field3;
	
	assign reg1_field3_rvld = 1'b1;
	
	assign reg1_field4_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field4 <= 4'b0;
	    else begin
	        if(reg1_field4_wvld) reg1_field4 <= reg1_field4_wdat;
	        else if(reg1_wvld) reg1_field4 <= reg1_wdat[11:8];
	    end
	end
	
	assign reg1_field4_rdat = reg1_field4;
	
	assign reg1_field4_rvld = 1'b1;
	

	//Wire this module connect to sub module.

	//module inst.

endmodule
//[UHDL]Content End [md5:e560fd3f30589360658521e92ed9a9b0]

