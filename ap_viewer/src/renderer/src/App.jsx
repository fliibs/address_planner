import React, { useState, useCallback, useEffect } from 'react';
import { Layout, Space, Divider, Table, Row, Col, FloatButton } from 'antd';
import GridLayout from "react-grid-layout";
import { UploadOutlined } from '@ant-design/icons';
import "../../../node_modules/react-grid-layout/css/styles.css";
import "../../../node_modules/react-resizable/css/styles.css";

let bank_column = [
  {
    "title": "Name",
    "dataIndex": "name",
    "key": "name",
    "width": "30%"
  },
  {
    "title": "Start_addr",
    "dataIndex": "start_addr",
    "key": "start_addr",
    "width": "15%"
  },
  {
    "title": "End_addr",
    "dataIndex": "end_addr",
    "key": "end_addr",
    "width": "15%"
  },
  {
    "title": "Size",
    "dataIndex": "size",
    "key": "size",
    "width": "15%",
  },
  {
    "title": "Description",
    "dataIndex": "description",
    "width": "25%",
    "key": "description"
  }
]
let field_column = [
  {
    "title": "Name",
    "dataIndex": "name",
    "key": "name",
    "width": "20%"
  },
  {
    "title": "Position",
    "dataIndex": "Position",
    "key": "Position",
    "width": "20%"
  },
  {
    "title": "External",
    "dataIndex": "External",
    "key": "External",
    "width": "10%"
  },
  {
    "title": "Software Access",
    "dataIndex": "Software Access",
    "key": "Software Access",
    "width": "15%"
  },
  {
    "title": "Hardware Access",
    "dataIndex": "Hardware Access",
    "key": "Hardware Access",
    "width": "15%"
  },
  {
    "title": "Description",
    "dataIndex": "description",
    "key": "description",
    "width": "20%"
  }
]
let fakeData = [
  {
    key: 0,
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

function useWinSize() {
  const [size, setSize] = useState({
    width: document.documentElement.clientWidth - 20,
    height: (document.documentElement.clientHeight - 50) / 2
  });

  const onResize = useCallback(
    () => {
      setSize({
        width: document.documentElement.clientWidth - 20,
        height: (document.documentElement.clientHeight - 50) / 2
      });
    }, []
  )
  useEffect(
    () => {
      window.addEventListener('resize', onResize)
    }, []
  )
  return size
}
class TableHeight {
  constructor() {
      this.bank_height = 100;
      this.reg_height = 100;
  }
  updateHeight() {
    const bank_grid = document.getElementById("bank_grid");
    const reg_grid = document.getElementById("reg_grid");
    console.log(reg_grid.offsetHeight)
    setTableHeight({
      bank_height: bank_grid.offsetHeight - 54.8-26-32,
      reg_height: reg_grid.offsetHeight - 54.8-26-32
    })
  }
}
function useTableHeight() {

  const [tableHeight, setTableHeight] = useState({
    bank_height: 100-40,
    reg_height: 100-40
  });

  const onResize = useCallback(
    () => {
      const bank_grid = document.getElementById("bank_grid");
      const reg_grid = document.getElementById("reg_grid");
      console.log(reg_grid.offsetHeight)
      setTableHeight({
        bank_height: bank_grid.offsetHeight - 54.8-26-32,
        reg_height: reg_grid.offsetHeight - 54.8-26-32
      })
    }, []
  )
  useEffect(
    () => {
      window.addEventListener('resize', onResize)
    }, []
  )
  return tableHeight
}

export default function App() {
  const [newData, setnewData] = useState(fakeData);
  const [newInput, setnewInput] = useState(fakeData);
  const [regName, setregName] = useState("null");
  const size = useWinSize();
  const tableHeight = useTableHeight();

  window.electronAPI.onUpdateData((_event, data) => {
    setnewInput(data);
  })

  const selectObj = (obj) => {
    if (obj.type == 'reg') {
      const new_reg_data_display = obj.fields;
      const new_reg_name_display = obj.name;
      setregName(new_reg_name_display);
      setnewData(new_reg_data_display);
    }
  };

  return (
    <>
      <FloatButton
        icon={<UploadOutlined />}
        type="default"
        style={{
          right: 94,
        }}
        onClick={() => window.electronAPI.readJson(1)}
      />

      <GridLayout className="layout" cols={12} rowHeight={size.height} width={size.width}>
        <div id="bank_grid" key="c" data-grid={{ x: 0, y: 0, w: 12, h: 1 }}>
          <Row>
            <Col className="gutter-row" span={24} >
              <Layout>
                <Divider orientation="left">Bank info</Divider>

                <Table
                  columns={bank_column}
                  onRow={(record) => ({
                    onClick: () => {
                      if (record.type == 'reg') {
                        console.log(record);
                        selectObj(record);
                      }
                    }
                  })}
                  dataSource={newInput}
                  pagination={false}
                  // scroll={{ x: '100%', y: tableSize.height }}
                  scroll={{ x: '100%', y: tableHeight.bank_height }}

                />
              </Layout>
            </Col>
          </Row>
        </div>
        <div id="reg_grid" key="d" data-grid={{ x: 0, y: 0, w: 12, h: 1 }}>
          <Row>
            <Col className="gutter-row" span={24}>
              <Layout>
                <Divider orientation="left">Reg info: {regName}</Divider>
                <Table
                  columns={field_column}
                  dataSource={newData}
                  scroll={{ x: '100%', y: tableHeight.reg_height }}
                  pagination={false}
                />
              </Layout>
            </Col>
          </Row>
        </div>
      </GridLayout>

    </>
  );
};