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


//[UHDL]Key Start [md5:657e1bc4c895f5399b20a5925f0ec634]
//Version Control Hash: 3accddf64b1dd03abeb9b0b3e5a7ba44
//Content Hash: 257802550174a54699dfb01b64440d98
//Parameter Hash: d41d8cd98f00b204e9800998ecf8427e
//[UHDL]Key End [md5:657e1bc4c895f5399b20a5925f0ec634]

//[UHDL]Version Control Start [md5:3accddf64b1dd03abeb9b0b3e5a7ba44]
//[UHDL]Version Control Version:1.0.1
//[UHDL]Version Control End [md5:3accddf64b1dd03abeb9b0b3e5a7ba44]

//[UHDL]Tool Message Start [md5:1cb60800d9deb8242456d9b4ed777943]
//Written by UHDL in 2023-07-17 11:17:28
//[UHDL]Tool Message End [md5:1cb60800d9deb8242456d9b4ed777943]

//[UHDL]User Message Start [md5:d41d8cd98f00b204e9800998ecf8427e]

//[UHDL]User Message End [md5:d41d8cd98f00b204e9800998ecf8427e]

//[UHDL]Content Start [md5:257802550174a54699dfb01b64440d98]
module RegSpaceBase_cfg_sw_no_read (
	input             clk                ,
	input             rst_n              ,
	input      [31:0] rreq_addr          ,
	input             rreq_vld           ,
	output            rreq_rdy           ,
	output     [31:0] rack_data          ,
	output            rack_vld           ,
	input             rack_rdy           ,
	input      [31:0] wreq_addr          ,
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
	    if((wreq_addr == 32'b0)) wreq_rdy = reg0_wrdy;
	    else if((wreq_addr == 32'b100000)) wreq_rdy = reg1_wrdy;
	    else wreq_rdy = 1'b0;
	end
	
	assign reg0_wdat = wreq_data;
	
	assign reg0_wrdy = 1'b1;
	
	assign reg0_wvld = (wreq_vld && (wreq_addr == 32'b0));
	
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
	
	assign reg1_wdat = wreq_data;
	
	assign reg1_wrdy = 1'b1;
	
	assign reg1_wvld = (wreq_vld && (wreq_addr == 32'b100000));
	
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
//[UHDL]Content End [md5:257802550174a54699dfb01b64440d98]

//[UHDL]Parameter Start [md5:d41d8cd98f00b204e9800998ecf8427e]

//[UHDL]Parameter End [md5:d41d8cd98f00b204e9800998ecf8427e]

