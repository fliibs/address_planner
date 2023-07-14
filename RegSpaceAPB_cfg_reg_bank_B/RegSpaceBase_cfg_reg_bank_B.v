//==========================================================================================================================
//Key is used to ensure the consistency of file version and content, and cannot be modified.
//Version Control is the version number written when the file is generated and cannot be modified.
//ToolMessage is used to record related information of any tool that has processed the file and cannot be manually modified.
//UserMessage is used by the user to write any information, which can be modified in any way.
//Content is the actual payload of the file.
//Parameter is the additional parameter information carried by the file and cannot be modified in any way.

//Key is generated by the hash of Version Control, Content and Parameter to ensure the consistency of the file.
//These three parts do not allow any individual modification
//==========================================================================================================================


//[UHDL]Key Start [md5:a63c922eb9705fcb9e91cca5c69f2fa5]
//Version Control Hash: 3accddf64b1dd03abeb9b0b3e5a7ba44
//Content Hash: 4da52a0ba8bf67958039532614561664
//Parameter Hash: d41d8cd98f00b204e9800998ecf8427e
//[UHDL]Key End [md5:a63c922eb9705fcb9e91cca5c69f2fa5]

//[UHDL]Version Control Start [md5:3accddf64b1dd03abeb9b0b3e5a7ba44]
//[UHDL]Version Control Version:1.0.1
//[UHDL]Version Control End [md5:3accddf64b1dd03abeb9b0b3e5a7ba44]

//[UHDL]Tool Message Start [md5:f0542ae0649391d15ee5563aa1eef78c]
//Written by UHDL in 2023-07-14 10:00:59
//[UHDL]Tool Message End [md5:f0542ae0649391d15ee5563aa1eef78c]

//[UHDL]User Message Start [md5:d41d8cd98f00b204e9800998ecf8427e]

//[UHDL]User Message End [md5:d41d8cd98f00b204e9800998ecf8427e]

//[UHDL]Content Start [md5:4da52a0ba8bf67958039532614561664]
module RegSpaceBase_cfg_reg_bank_B (
	input             clk             ,
	input             rst_n           ,
	input      [31:0] rreq_addr       ,
	input             rreq_vld        ,
	output            rreq_rdy        ,
	output reg [31:0] rack_data       ,
	output reg        rack_vld        ,
	input             rack_rdy        ,
	input      [31:0] wreq_addr       ,
	input      [31:0] wreq_data       ,
	input             wreq_vld        ,
	output reg        p_wready        ,
	input             reg0_field0_wdat,
	input             reg0_field0_wvld,
	output            reg0_field0_wrdy,
	output            reg0_field0_rdat,
	output            reg0_field0_rvld,
	input             reg0_field0_rrdy,
	input             reg0_field1_wdat,
	input             reg0_field1_wvld,
	output            reg0_field1_wrdy,
	output            reg0_field1_rdat,
	output            reg0_field1_rvld,
	input             reg0_field1_rrdy,
	input             reg0_field2_wdat,
	input             reg0_field2_wvld,
	output            reg0_field2_wrdy,
	output            reg0_field2_rdat,
	output            reg0_field2_rvld,
	input             reg0_field2_rrdy,
	output            reg0_field3_rdat,
	output            reg0_field3_rvld,
	input             reg0_field3_rrdy,
	input             reg0_field4_wdat,
	input             reg0_field4_wvld,
	output            reg0_field4_wrdy,
	input             reg0_field5_wdat,
	input             reg0_field5_wvld,
	output            reg0_field5_wrdy,
	output            reg0_field5_rdat,
	output            reg0_field5_rvld,
	input             reg0_field5_rrdy,
	input      [1:0]  reg0_field6_wdat,
	input             reg0_field6_wvld,
	output            reg0_field6_wrdy,
	output     [1:0]  reg0_field6_rdat,
	output            reg0_field6_rvld,
	input             reg0_field6_rrdy,
	input             reg1_field0_wdat,
	input             reg1_field0_wvld,
	output            reg1_field0_wrdy,
	output            reg1_field0_rdat,
	output            reg1_field0_rvld,
	input             reg1_field0_rrdy,
	input             reg1_field1_wdat,
	input             reg1_field1_wvld,
	output            reg1_field1_wrdy,
	output            reg1_field1_rdat,
	output            reg1_field1_rvld,
	input             reg1_field1_rrdy,
	input             reg1_field2_wdat,
	input             reg1_field2_wvld,
	output            reg1_field2_wrdy,
	output            reg1_field2_rdat,
	output            reg1_field2_rvld,
	input             reg1_field2_rrdy,
	output            reg1_field3_rdat,
	output            reg1_field3_rvld,
	input             reg1_field3_rrdy,
	input             reg1_field4_wdat,
	input             reg1_field4_wvld,
	output            reg1_field4_wrdy,
	input             reg1_field5_wdat,
	input             reg1_field5_wvld,
	output            reg1_field5_wrdy,
	output            reg1_field5_rdat,
	output            reg1_field5_rvld,
	input             reg1_field5_rrdy,
	input      [1:0]  reg1_field6_wdat,
	input             reg1_field6_wvld,
	output            reg1_field6_wrdy,
	output     [1:0]  reg1_field6_rdat,
	output            reg1_field6_rvld,
	input             reg1_field6_rrdy);

	//Wire define for this module.
	wire [31:0] reg0_rdat  ;
	wire [0:0]  reg0_rrdy  ;
	wire [0:0]  reg0_rvld  ;
	wire [31:0] reg0_wdat  ;
	wire [0:0]  reg0_wrdy  ;
	wire [0:0]  reg0_wvld  ;
	reg  [0:0]  reg0_field0;
	reg  [0:0]  reg0_field1;
	reg  [0:0]  reg0_field2;
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
	reg  [0:0]  reg1_field0;
	reg  [0:0]  reg1_field1;
	reg  [0:0]  reg1_field2;
	reg  [0:0]  reg1_field3;
	reg  [0:0]  reg1_field4;
	reg  [0:0]  reg1_field5;
	reg  [1:0]  reg1_field6;

	//Wire define for sub module.

	//Wire define for Inout.

	//Wire sub module connect to this module and inter module connect.
	assign rreq_rdy = (rack_rdy && rack_vld);
	
	always @(*) begin
	    if((rreq_addr == 32'b0)) rack_data = reg0_rdat;
	    else if((rreq_addr == 32'b1)) rack_data = reg1_rdat;
	    else rack_data = 32'b0;
	end
	
	always @(*) begin
	    if((rreq_vld && (rreq_addr == 32'b0))) rack_vld = reg0_rrdy;
	    else if((rreq_vld && (rreq_addr == 32'b1))) rack_vld = reg1_rrdy;
	    else rack_vld = 1'b0;
	end
	
	always @(*) begin
	    if((wreq_addr == 32'b0)) p_wready = reg0_wrdy;
	    else if((wreq_addr == 32'b1)) p_wready = reg1_wrdy;
	    else p_wready = 1'b0;
	end
	
	assign reg0_rdat = {reg0_field0, 2'b0, 1'b0, 1'b0, reg0_field2, 1'b0, reg0_field3, 1'b0, reg0_field4, 1'b0, reg0_field5, 1'b0, reg0_field6, 17'b0};
	
	assign reg0_rrdy = 1'b1;
	
	assign reg0_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 32'b0));
	
	assign reg0_wdat = wreq_data;
	
	assign reg0_wrdy = 1'b1;
	
	assign reg0_wvld = (wreq_vld && (wreq_addr == 32'b0));
	
	assign reg0_field0_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field0 <= 1'b0;
	    else begin
	        if(reg0_field0_wvld) reg0_field0 <= reg0_field0_wdat;
	    end
	end
	
	assign reg0_field0_rdat = reg0_field0;
	
	assign reg0_field0_rvld = 1'b1;
	
	assign reg0_field1_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field1 <= 1'b0;
	    else begin
	        if(reg0_field1_wvld) reg0_field1 <= reg0_field1_wdat;
	        else if(reg0_wvld) reg0_field1 <= reg0_wdat[3:3];
	    end
	end
	
	assign reg0_field1_rdat = reg0_field1;
	
	assign reg0_field1_rvld = 1'b1;
	
	assign reg0_field2_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg0_field2 <= 1'b0;
	    else begin
	        if(reg0_field2_wvld) reg0_field2 <= reg0_field2_wdat;
	        else if(reg0_wvld) reg0_field2 <= reg0_wdat[5:5];
	    end
	end
	
	assign reg0_field2_rdat = reg0_field2;
	
	assign reg0_field2_rvld = 1'b1;
	
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
	        else if(reg0_wvld) reg0_field6 <= reg0_wdat[14:13];
	        else if(reg0_rvld) reg0_field6 <= 2'b0;
	    end
	end
	
	assign reg0_field6_rdat = reg0_field6;
	
	assign reg0_field6_rvld = 1'b1;
	
	assign reg1_rdat = {reg1_field0, 2'b0, 1'b0, 1'b0, reg1_field2, 1'b0, reg1_field3, 1'b0, reg1_field4, 1'b0, reg1_field5, 1'b0, reg1_field6, 17'b0};
	
	assign reg1_rrdy = 1'b1;
	
	assign reg1_rvld = ((rack_rdy && rack_vld) && (rreq_addr == 32'b1));
	
	assign reg1_wdat = wreq_data;
	
	assign reg1_wrdy = 1'b1;
	
	assign reg1_wvld = (wreq_vld && (wreq_addr == 32'b1));
	
	assign reg1_field0_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field0 <= 1'b0;
	    else begin
	        if(reg1_field0_wvld) reg1_field0 <= reg1_field0_wdat;
	    end
	end
	
	assign reg1_field0_rdat = reg1_field0;
	
	assign reg1_field0_rvld = 1'b1;
	
	assign reg1_field1_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field1 <= 1'b0;
	    else begin
	        if(reg1_field1_wvld) reg1_field1 <= reg1_field1_wdat;
	        else if(reg1_wvld) reg1_field1 <= reg1_wdat[3:3];
	    end
	end
	
	assign reg1_field1_rdat = reg1_field1;
	
	assign reg1_field1_rvld = 1'b1;
	
	assign reg1_field2_wrdy = 1'b1;
	
	always @(posedge clk or negedge rst_n) begin
	    if(~rst_n) reg1_field2 <= 1'b0;
	    else begin
	        if(reg1_field2_wvld) reg1_field2 <= reg1_field2_wdat;
	        else if(reg1_wvld) reg1_field2 <= reg1_wdat[5:5];
	    end
	end
	
	assign reg1_field2_rdat = reg1_field2;
	
	assign reg1_field2_rvld = 1'b1;
	
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
	        else if(reg1_wvld) reg1_field6 <= reg1_wdat[14:13];
	        else if(reg1_rvld) reg1_field6 <= 2'b0;
	    end
	end
	
	assign reg1_field6_rdat = reg1_field6;
	
	assign reg1_field6_rvld = 1'b1;
	

	//Wire this module connect to sub module.

	//module inst.

endmodule
//[UHDL]Content End [md5:4da52a0ba8bf67958039532614561664]

//[UHDL]Parameter Start [md5:d41d8cd98f00b204e9800998ecf8427e]

//[UHDL]Parameter End [md5:d41d8cd98f00b204e9800998ecf8427e]

