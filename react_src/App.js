import React, { useState } from 'react';
import {Layout, Space, Switch, Table } from 'antd';
const bank_colum = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: 'Start_addr',
    dataIndex: 'start_addr',
    key: 'start_addr',
    width: '12%',
  },
  {
    title: 'End_addr',
    dataIndex: 'end_addr',
    width: '12%',
    key: 'end_addr',
  },
  {
    title: 'Size',
    dataIndex: 'size',
    width: '15%',
    key: 'size',
  },
];

const bank_data = [
  {
    key: 1,
    type: 'sys',
    name: 'SYS1',
    start_addr: '0x00',
    end_addr: '0x32',
    size: '32B',
    children: [
      {
        key: 2,
        type: 'ip',
        name: 'IP1',
        start_addr: '0x00',
        end_addr: '0x19',
        size: '16B',
        children: [
          {
            key: 5,
            type: 'reg',
            name: 'reg1',
            start_addr: '0x00',
            end_addr: '0x4',
            size: '4B',
          },
          {
            key: 6,
            type: 'reg',
            name: 'reg2',
            start_addr: '0x05',
            end_addr: '0x8',
            size: '4B',
          },
        ],
      },
      {
        key: 3,
        type: 'ip',
        name: 'IP2',
        start_addr: '0x20',
        end_addr: '0x32',
        size: '16B',
      },
    ],
  },
  {
    key: 4,
    type: 'sys',
    name: 'SYS2',
    start_addr: '0x33',
    end_addr: '0x64',
    size: '32B',
  },
];

const fakeData = [
  {
    key:0,
    name: 'null',
    fields: [
      {
        key: 1,
        name: 'null',
        description: 'null'
      },
    ]
  },
];

const reg_colum = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: 'Description',
    dataIndex: 'description',
    key: 'description',
    width: '12%',
  },
 
];

const reg_data = [
  {
    key:5,
    name: 'reg1',
    fields: [
      {
        key: 1,
        name: 'field1',
        description: 'func1'
      },
      {
        key: 2,
        name: 'field2',
        description: 'func2'
      }
    ]
  },
  {
    key:6,
    name: 'reg2',
    fields: [
      {
        key: 3,
        name: 'field3',
        description: 'func3'
      },
      {
        key: 4,
        name: 'field4',
        description: 'func4'
      }
    ]
  }
]

const columns = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: 'Age',
    dataIndex: 'age',
    key: 'age',
    width: '12%',
  },
  {
    title: 'Address',
    dataIndex: 'address',
    width: '30%',
    key: 'address',
  },
];


const data = [
  {
    key: 1,
    name: 'John Brown sr.',
    age: 60,
    address: 'New York No. 1 Lake Park',
    children: [
      {
        key: 11,
        name: 'John Brown',
        age: 42,
        address: 'New York No. 2 Lake Park',
      },
      {
        key: 12,
        name: 'John Brown jr.',
        age: 30,
        address: 'New York No. 3 Lake Park',
        children: [
          {
            key: 121,
            name: 'Jimmy Brown',
            age: 16,
            address: 'New York No. 3 Lake Park',
          },
        ],
      },
      {
        key: 13,
        name: 'Jim Green sr.',
        age: 72,
        address: 'London No. 1 Lake Park',
        children: [
          {
            key: 131,
            name: 'Jim Green',
            age: 42,
            address: 'London No. 2 Lake Park',
            children: [
              {
                key: 1311,
                name: 'Jim Green jr.',
                age: 25,
                address: 'London No. 3 Lake Park',
              },
              {
                key: 1312,
                name: 'Jimmy Green sr.',
                age: 18,
                address: 'London No. 4 Lake Park',
              },
            ],
          },
        ],
      },
    ],
  },
  {
    key: 2,
    name: 'Joe Black',
    age: 32,
    address: 'Sydney No. 1 Lake Park',
  },
];

// // rowSelection objects indicates the need for row selection
// const rowSelection = {
//   onChange: (selectedRowKeys, selectedRows) => {
//     console.log(`selectedRowKeys: ${selectedRowKeys}`, 'selectedRows: ', selectedRows);
//   },
//   onSelect: (record, selected, selectedRows) => {
//     console.log(record, selected, selectedRows);
//   },
//   onSelectAll: (selected, selectedRows, changeRows) => {
//     console.log(selected, selectedRows, changeRows);
//   },
// };


export default function App () {
  const [newData, setnewData] = useState(fakeData);

  const selectObj = (obj) => {
    if (obj.type == 'reg') {
      let reg_id = obj.key;
      let reg_info = reg_data.find(o => o.key === reg_id);
      console.log(reg_info);
      console.log(reg_info.fields);
      const new_reg_data_display = reg_info.fields;
      setnewData(new_reg_data_display);
      console.log('select data:',new_reg_data_display);
    }
  };
  return (
    <>
      <Space
        align="center"
        style={{
          marginBottom: 16,
        }}
      >
        {/* CheckStrictly: <Switch checked={checkStrictly} onChange={setCheckStrictly} /> */}
      </Space>
      <Layout>
      <Table
        columns={bank_colum}
        onRow={(record) => ({
          onClick: ()=>{
            if(record.type =='reg') {
              console.log(record);
              selectObj(record);
            }
          }
        })}
        dataSource={bank_data}
      />
      </Layout>
      <Layout>
      <Table
        columns={reg_colum}
       
        dataSource={newData}
      />
      </Layout>
    </>
  );
};