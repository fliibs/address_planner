module fanout #(
    parameter WIDTH=4 
)(
    input  vld,
    output rdy,
    
    output [WIDTH-1:0] v_vld,
    input  [WIDTH-1:0] v_rdy
);

    assign v_vld = {WIDTH{vld}};
    assign rdy = |v_rdy;


endmodule 