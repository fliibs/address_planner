
//==========================================================
// Definition of reg REG_BANK_TABLES_INTERNAL_REG
//==========================================================
#ifndef ADDR_REG_BANK_TABLES_INTERNAL_REG

    typedef union{
        struct {
            uint32_t field0: 1;
            uint32_t field1: 2;
            uint32_t field2: 1;
            uint32_t field3: 3;
            } bits;
        uint32_t val;
    } REG_BANK_TABLES_INTERNAL_REG;

    #define REG_BANK_TABLES_INTERNAL_REG_ADDR                                  0x100
    #define REG_BANK_TABLES_INTERNAL_REG_SIZE                                  0x1
    #define REG_BANK_TABLES_INTERNAL_REG_OFFSET                                0x20

#endif

#ifndef OFFSET_REG_BANK_TABLES_INTERNAL_REG_FIELD0
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD0_OFFSET  0
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD0_WIDTH   1
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD0_MASK    0x1
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD0_RST_VAL 0x1
#endif

#ifndef OFFSET_REG_BANK_TABLES_INTERNAL_REG_FIELD1
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD1_OFFSET  1
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD1_WIDTH   2
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD1_MASK    0x6
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD1_RST_VAL 0x6
#endif

#ifndef OFFSET_REG_BANK_TABLES_INTERNAL_REG_FIELD2
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD2_OFFSET  3
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD2_WIDTH   1
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD2_MASK    0x8
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD2_RST_VAL 0x8
#endif

#ifndef OFFSET_REG_BANK_TABLES_INTERNAL_REG_FIELD3
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD3_OFFSET  6
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD3_WIDTH   3
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD3_MASK    0x1c0
    #define REG_BANK_TABLES_INTERNAL_REG_FIELD3_RST_VAL 0x1c0
#endif


//==========================================================
// Definition of reg REG_BANK_TABLES_EXTERNAL_REG
//==========================================================
#ifndef ADDR_REG_BANK_TABLES_EXTERNAL_REG

    typedef union{
        struct {
            uint32_t field0: 1;
            uint32_t field1: 1;
            uint32_t field2: 3;
            uint32_t field3: 4;
            } bits;
        uint32_t val;
    } REG_BANK_TABLES_EXTERNAL_REG;

    #define REG_BANK_TABLES_EXTERNAL_REG_ADDR                                  0x300
    #define REG_BANK_TABLES_EXTERNAL_REG_SIZE                                  0x1
    #define REG_BANK_TABLES_EXTERNAL_REG_OFFSET                                0x60

#endif

#ifndef OFFSET_REG_BANK_TABLES_EXTERNAL_REG_FIELD0
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD0_OFFSET  1
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD0_WIDTH   1
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD0_MASK    0x2
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD0_RST_VAL 0x2
#endif

#ifndef OFFSET_REG_BANK_TABLES_EXTERNAL_REG_FIELD1
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD1_OFFSET  3
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD1_WIDTH   1
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD1_MASK    0x8
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD1_RST_VAL 0x8
#endif

#ifndef OFFSET_REG_BANK_TABLES_EXTERNAL_REG_FIELD2
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD2_OFFSET  7
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD2_WIDTH   3
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD2_MASK    0x380
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD2_RST_VAL 0x380
#endif

#ifndef OFFSET_REG_BANK_TABLES_EXTERNAL_REG_FIELD3
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD3_OFFSET  11
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD3_WIDTH   4
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD3_MASK    0x7800
    #define REG_BANK_TABLES_EXTERNAL_REG_FIELD3_RST_VAL 0x7800
#endif

