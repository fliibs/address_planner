//[UHDL]Content Start [md5:66742c2f2c6bb6a7e2521cb2e7f4c7ea]
module RegSpaceBase_cfg_sw_read_clean (
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
	output            wreq_rdy           ,
	input             reg0_sw_field1_rdat,
	output            reg0_sw_field1_rvld,
	input             reg0_sw_field1_rrdy,
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
	input             reg1_sw_field1_rdat,
	output            reg1_sw_field1_rvld,
	input             reg1_sw_field1_rrdy,
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
	wire [31:0] reg0_rdat  ;
	wire [0:0]  reg0_rrdy  ;
	wire [0:0]  reg0_rvld  ;
	reg  [1:0]  reg0_field2;
	reg  [2:0]  reg0_field3;
	reg  [3:0]  reg0_field4;
	wire [31:0] reg1_rdat  ;
	wire [0:0]  reg1_rrdy  ;
	wire [0:0]  reg1_rvld  ;
	reg  [1:0]  reg1_field2;
	reg  [2:0]  reg1_field3;
	reg  [3:0]  reg1_field4;

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
	
	assign wreq_rdy = 1'b0;
	
	assign reg0_rdat = {2'b0, reg0_sw_field1_rdat, reg0_field2, reg0_field3, 1'b0, reg0_field4, 19'b0};
	
	assign reg0_rrdy = 1'b1;
	
	assign reg0_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'b0));
	
	assign reg0_sw_field1_rvld = reg0_rvld;
	
	assign reg0_field2_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field2 <= 2'b0;
	    else begin
	        if(reg0_field2_wvld) reg0_field2 <= reg0_field2_wdat;
	        else if(reg0_rvld) reg0_field2 <= 2'b0;
	    end
	end
	
	assign reg0_field2_rdat = reg0_field2;
	
	assign reg0_field2_rvld = 1'b1;
	
	assign reg0_field3_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field3 <= 3'b0;
	    else begin
	        if(reg0_field3_wvld) reg0_field3 <= reg0_field3_wdat;
	        else if(reg0_rvld) reg0_field3 <= 3'b0;
	    end
	end
	
	assign reg0_field3_rdat = reg0_field3;
	
	assign reg0_field3_rvld = 1'b1;
	
	assign reg0_field4_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field4 <= 4'b0;
	    else begin
	        if(reg0_field4_wvld) reg0_field4 <= reg0_field4_wdat;
	        else if(reg0_rvld) reg0_field4 <= 4'b0;
	    end
	end
	
	assign reg0_field4_rdat = reg0_field4;
	
	assign reg0_field4_rvld = 1'b1;
	
	assign reg1_rdat = {2'b0, reg1_sw_field1_rdat, reg1_field2, reg1_field3, 1'b0, reg1_field4, 19'b0};
	
	assign reg1_rrdy = 1'b1;
	
	assign reg1_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'b100000));
	
	assign reg1_sw_field1_rvld = reg1_rvld;
	
	assign reg1_field2_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field2 <= 2'b0;
	    else begin
	        if(reg1_field2_wvld) reg1_field2 <= reg1_field2_wdat;
	        else if(reg1_rvld) reg1_field2 <= 2'b0;
	    end
	end
	
	assign reg1_field2_rdat = reg1_field2;
	
	assign reg1_field2_rvld = 1'b1;
	
	assign reg1_field3_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field3 <= 3'b0;
	    else begin
	        if(reg1_field3_wvld) reg1_field3 <= reg1_field3_wdat;
	        else if(reg1_rvld) reg1_field3 <= 3'b0;
	    end
	end
	
	assign reg1_field3_rdat = reg1_field3;
	
	assign reg1_field3_rvld = 1'b1;
	
	assign reg1_field4_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field4 <= 4'b0;
	    else begin
	        if(reg1_field4_wvld) reg1_field4 <= reg1_field4_wdat;
	        else if(reg1_rvld) reg1_field4 <= 4'b0;
	    end
	end
	
	assign reg1_field4_rdat = reg1_field4;
	
	assign reg1_field4_rvld = 1'b1;
	

	//Wire this module connect to sub module.

	//module inst.

endmodule
//[UHDL]Content End [md5:66742c2f2c6bb6a7e2521cb2e7f4c7ea]

