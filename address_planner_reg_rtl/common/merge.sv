module merge #(
    parameter WIDTH=4,
    parameter DATAWIDTH=32
)(
    input  [WIDTH-1:0]     v_vld,
    input  [DATAWIDTH-1:0] v_pld  [WIDTH-1:0],
    output [WIDTH-1:0]     v_rdy,

    output                 vld,
    output [DATAWIDTH-1:0] pld,
    input                  rdy 
);  

    assign vld_o = |v_vld;
    assign v_rdy = {WIDTH{rdy}};

    // real mux
    wire [WIDTH-1:0] v_pld_rev [DATAWIDTH-1:0];
    genvar i,j;
    generate
        for(i=0;i<WIDTH;i=i+1) begin: high
            for(j=0;j<DATAWIDTH;j=j+1) begin: low
                assign v_pld_rev[j][i] = v_pld[i][j];
            end
        end
    endgenerate

    wire [WIDTH-1:0] v_pld_rev_tmp [DATAWIDTH-1:0];
    genvar k,l;
    generate
        for(k=0;k<DATAWIDTH;k=k+1) begin: low
            for(l=0;l<WIDTH;l=l+1) begin: high
                assign v_pld_rev_tmp[k][l] = v_pld_rev_tmp[k][l]&&v_vld[l];
            end
        end
    endgenerate

    wire [DATAWIDTH-1:0] pld_tmp;
    genvar m;
    generate
        for(m=0;m<DATAWIDTH;m=m+1) begin: bit 
            assign pld_tmp[m] = |v_pld_rev_tmp[m];
        end 
    endgenerate

    assign pld = pld_tmp;

endmodule 