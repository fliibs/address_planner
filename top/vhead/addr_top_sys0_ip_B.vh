//==========================================================
// Definition of address space TOP_SYS0_IP_B
//==========================================================

`ifndef     ADDR_TOP_SYS0_IP_B
    `define ADDR_TOP_SYS0_IP_B                                       0x100000
    `define SIZE_TOP_SYS0_IP_B                                       0x1000
    `define OFFSET_TOP_SYS0_IP_B                                     0x100000
`endif

//==========================================================
// Sub address space definition of TOP_SYS0_IP_B
//==========================================================

`ifndef     ADDR_TOP_SYS0_IP_B_MEM
    `define ADDR_TOP_SYS0_IP_B_MEM                                       0x0
    `define SIZE_TOP_SYS0_IP_B_MEM                                       0x800
    `define OFFSET_TOP_SYS0_IP_B_MEM                                     0x0
`endif

`ifndef     ADDR_TOP_SYS0_IP_B_REG
    `define ADDR_TOP_SYS0_IP_B_REG                                       0x800
    `define SIZE_TOP_SYS0_IP_B_REG                                       0x400
    `define OFFSET_TOP_SYS0_IP_B_REG                                     0x800
`endif
