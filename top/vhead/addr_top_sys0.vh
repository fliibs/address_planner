//==========================================================
// Definition of address space TOP_SYS0
//==========================================================

`ifndef     ADDR_TOP_SYS0
    `define ADDR_TOP_SYS0                                       0x0
    `define SIZE_TOP_SYS0                                       0x300000
    `define OFFSET_TOP_SYS0                                     0x0
`endif

//==========================================================
// Sub address space definition of TOP_SYS0
//==========================================================

`ifndef     ADDR_TOP_SYS0_IP_A
    `define ADDR_TOP_SYS0_IP_A                                       0x0
    `define SIZE_TOP_SYS0_IP_A                                       0x1000
    `define OFFSET_TOP_SYS0_IP_A                                     0x0
`endif

`ifndef     ADDR_TOP_SYS0_IP_B
    `define ADDR_TOP_SYS0_IP_B                                       0x100000
    `define SIZE_TOP_SYS0_IP_B                                       0x1000
    `define OFFSET_TOP_SYS0_IP_B                                     0x100000
`endif

`ifndef     ADDR_TOP_SYS0_IP_C
    `define ADDR_TOP_SYS0_IP_C                                       0x200000
    `define SIZE_TOP_SYS0_IP_C                                       0x2000
    `define OFFSET_TOP_SYS0_IP_C                                     0x200000
`endif
