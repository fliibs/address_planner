//[UHDL]Content Start [md5:e518c8e57bf154e1fe4da5d9383afa6e]
module RegSpaceBase_cfg_reg_bank_tables (
	input             clk                        ,
	input             rst_n                      ,
	input      [15:0] rreq_addr                  ,
	input             rreq_vld                   ,
	output            rreq_rdy                   ,
	output reg [31:0] rack_data                  ,
	output reg        rack_vld                   ,
	input             rack_rdy                   ,
	input      [15:0] wreq_addr                  ,
	input      [31:0] wreq_data                  ,
	input             wreq_vld                   ,
	output reg        wreq_rdy                   ,
	input             internal_reg_field0_wdat   ,
	input             internal_reg_field0_wvld   ,
	output            internal_reg_field0_wrdy   ,
	output            internal_reg_field0_rdat   ,
	output            internal_reg_field0_rvld   ,
	input             internal_reg_field0_rrdy   ,
	input      [1:0]  internal_reg_field1_wdat   ,
	input             internal_reg_field1_wvld   ,
	output            internal_reg_field1_wrdy   ,
	output     [1:0]  internal_reg_field1_rdat   ,
	output            internal_reg_field1_rvld   ,
	input             internal_reg_field1_rrdy   ,
	input             internal_reg_field2_wdat   ,
	input             internal_reg_field2_wvld   ,
	output            internal_reg_field2_wrdy   ,
	output            internal_reg_field2_rdat   ,
	output            internal_reg_field2_rvld   ,
	input             internal_reg_field2_rrdy   ,
	output     [2:0]  internal_reg_field3_rdat   ,
	output            internal_reg_field3_rvld   ,
	input             internal_reg_field3_rrdy   ,
	input             external_reg_sw_field0_rdat,
	output            external_reg_sw_field0_rvld,
	input             external_reg_sw_field0_rrdy,
	output            external_reg_sw_field0_wdat,
	output            external_reg_sw_field0_wvld,
	input             external_reg_sw_field0_wrdy,
	input             external_reg_sw_field1_rdat,
	output            external_reg_sw_field1_rvld,
	input             external_reg_sw_field1_rrdy,
	output            external_reg_sw_field1_wdat,
	output            external_reg_sw_field1_wvld,
	input             external_reg_sw_field1_wrdy,
	input      [2:0]  external_reg_sw_field2_rdat,
	output            external_reg_sw_field2_rvld,
	input             external_reg_sw_field2_rrdy,
	output     [2:0]  external_reg_sw_field2_wdat,
	output            external_reg_sw_field2_wvld,
	input             external_reg_sw_field2_wrdy,
	input      [3:0]  external_reg_sw_field3_rdat,
	output            external_reg_sw_field3_rvld,
	input             external_reg_sw_field3_rrdy,
	output     [3:0]  external_reg_sw_field3_wdat,
	output            external_reg_sw_field3_wvld,
	input             external_reg_sw_field3_wrdy);

	//Wire define for this module.
	wire [31:0] internal_reg_rdat  ;
	wire [0:0]  internal_reg_rrdy  ;
	wire [0:0]  internal_reg_rvld  ;
	wire [31:0] internal_reg_wdat  ;
	wire [0:0]  internal_reg_wrdy  ;
	wire [0:0]  internal_reg_wvld  ;
	reg  [0:0]  internal_reg_field0;
	reg  [1:0]  internal_reg_field1;
	reg  [0:0]  internal_reg_field2;
	reg  [2:0]  internal_reg_field3;
	wire [31:0] external_reg_rdat  ;
	wire [0:0]  external_reg_rrdy  ;
	wire [0:0]  external_reg_rvld  ;
	wire [31:0] external_reg_wdat  ;
	wire [0:0]  external_reg_wrdy  ;
	wire [0:0]  external_reg_wvld  ;

	//Wire define for sub module.

	//Wire define for Inout.

	//Wire sub module connect to this module and inter module connect.
	assign rreq_rdy = (rack_rdy && rack_vld);
	
	always @(*) begin
	    if((rreq_addr == 16'h20)) rack_data = internal_reg_rdat;
	    else if((rreq_addr == 16'h60)) rack_data = external_reg_rdat;
	    else rack_data = 32'h0;
	end
	
	always @(*) begin
	    if((rreq_addr == 16'h20)) rack_vld = internal_reg_rrdy;
	    else if((rreq_addr == 16'h60)) rack_vld = external_reg_rrdy;
	    else rack_vld = 1'h0;
	end
	
	always @(*) begin
	    if((wreq_addr == 16'h20)) wreq_rdy = internal_reg_wrdy;
	    else if((wreq_addr == 16'h60)) wreq_rdy = external_reg_wrdy;
	    else wreq_rdy = 1'h0;
	end
	
	assign internal_reg_rdat = {internal_reg_field0, 2'h0, internal_reg_field2, 2'h0, internal_reg_field3, 23'h0};
	
	assign internal_reg_rrdy = 1'h1;
	
	assign internal_reg_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'h20));
	
	assign internal_reg_wdat = wreq_data[31:0];
	
	assign internal_reg_wrdy = 1'h1;
	
	assign internal_reg_wvld = (wreq_vld && (wreq_addr == 16'h20));
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) internal_reg_field0 <= 1'h0;
	    else begin
	        if(internal_reg_field0_wvld) internal_reg_field0 <= internal_reg_field0_wdat;
	    end
	end
	
	assign internal_reg_field0_wrdy = 1'h1;
	
	assign internal_reg_field0_rdat = internal_reg_field0;
	
	assign internal_reg_field0_rvld = 1'h1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) internal_reg_field1 <= 2'h0;
	    else begin
	        if(internal_reg_field1_wvld) internal_reg_field1 <= internal_reg_field1_wdat;
	        else if(internal_reg_wvld) internal_reg_field1 <= internal_reg_wdat[2:1];
	    end
	end
	
	assign internal_reg_field1_wrdy = 1'h1;
	
	assign internal_reg_field1_rdat = internal_reg_field1;
	
	assign internal_reg_field1_rvld = 1'h1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) internal_reg_field2 <= 1'h0;
	    else begin
	        if(internal_reg_field2_wvld) internal_reg_field2 <= internal_reg_field2_wdat;
	        else if(internal_reg_wvld) internal_reg_field2 <= internal_reg_wdat[3:3];
	    end
	end
	
	assign internal_reg_field2_wrdy = 1'h1;
	
	assign internal_reg_field2_rdat = internal_reg_field2;
	
	assign internal_reg_field2_rvld = 1'h1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) internal_reg_field3 <= 3'h0;
	    else begin
	        if(internal_reg_wvld) internal_reg_field3 <= internal_reg_wdat[8:6];
	    end
	end
	
	assign internal_reg_field3_rdat = internal_reg_field3;
	
	assign internal_reg_field3_rvld = 1'h1;
	
	assign external_reg_rdat = {1'h0, external_reg_sw_field0_rdat, 1'h0, external_reg_sw_field1_rdat, 3'h0, external_reg_sw_field2_rdat, 1'h0, external_reg_sw_field3_rdat, 17'h0};
	
	assign external_reg_rrdy = 1'h1;
	
	assign external_reg_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 16'h60));
	
	assign external_reg_wdat = wreq_data[31:0];
	
	assign external_reg_wrdy = 1'h1;
	
	assign external_reg_wvld = (wreq_vld && (wreq_addr == 16'h60));
	
	assign external_reg_sw_field0_rvld = external_reg_rvld;
	
	assign external_reg_sw_field0_wdat = external_reg_wdat[1:1];
	
	assign external_reg_sw_field0_wvld = external_reg_wvld;
	
	assign external_reg_sw_field1_rvld = external_reg_rvld;
	
	assign external_reg_sw_field1_wdat = external_reg_wdat[3:3];
	
	assign external_reg_sw_field1_wvld = external_reg_wvld;
	
	assign external_reg_sw_field2_rvld = external_reg_rvld;
	
	assign external_reg_sw_field2_wdat = external_reg_wdat[9:7];
	
	assign external_reg_sw_field2_wvld = external_reg_wvld;
	
	assign external_reg_sw_field3_rvld = external_reg_rvld;
	
	assign external_reg_sw_field3_wdat = external_reg_wdat[14:11];
	
	assign external_reg_sw_field3_wvld = external_reg_wvld;
	

	//Wire this module connect to sub module.

	//module inst.

endmodule
//[UHDL]Content End [md5:e518c8e57bf154e1fe4da5d9383afa6e]

