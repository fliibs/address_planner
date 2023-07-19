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
            fields: [
              {
                key: 10,
                name: 'field1',
                description: 'func3'
              },
              {
                key: 12,
                name: 'field2',
                description: 'func4'
              }
            ]
          },
          {
            key: 6,
            type: 'reg',
            name: 'reg2',
            start_addr: '0x05',
            end_addr: '0x8',
            size: '4B',
            fields: [
              {
                key: 11,
                name: 'field3',
                description: 'func3'
              },
              {
                key: 14,
                name: 'field4',
                description: 'func4'
              }
            ],
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


export default function App () {
  const [newData, setnewData] = useState(fakeData);

  const selectObj = (obj) => {
    if (obj.type == 'reg') {
      // let reg_id = obj.key;
      // console.log("reg_id",reg_id);
      // let reg_obj = bank_data.find(o => o.key === reg_id);
      // console.log("reg_obj",reg_obj);
      // let reg_info = reg_obj.fields;
      // console.log(reg_info);
      // console.log(reg_info.fields);
      const new_reg_data_display = obj.fields;
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