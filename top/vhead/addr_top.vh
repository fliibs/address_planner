//==========================================================
// Definition of address space TOP
//==========================================================

`ifndef     ADDR_TOP
    `define ADDR_TOP                                       0x0
    `define SIZE_TOP                                       0x400000
    `define OFFSET_TOP                                     0x0
`endif

//==========================================================
// Sub address space definition of TOP
//==========================================================

`ifndef     ADDR_TOP_SYS0
    `define ADDR_TOP_SYS0                                       0x0
    `define SIZE_TOP_SYS0                                       0x300000
    `define OFFSET_TOP_SYS0                                     0x0
`endif

`ifndef     ADDR_TOP_SYS1
    `define ADDR_TOP_SYS1                                       0x300000
    `define SIZE_TOP_SYS1                                       0x100000
    `define OFFSET_TOP_SYS1                                     0x300000
`endif
