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
      })
    }, []
  )
  useEffect(
    () => {
      window.addEventListener('resize', onResize)
    }, []
  )
  console.log(document.documentElement.clientHeight)
  return size
}

function useTableSize() {
  const [tableSize, setTableSize] = useState({
    width: document.documentElement.clientWidth - 20,
    height: (document.documentElement.clientHeight - 50) / 2 -110
  });

  const onResize = useCallback(
    () => {
      setTableSize({
        width: document.documentElement.clientWidth - 20,
        height: (document.documentElement.clientHeight - 50) / 2  -110
      })
    }, []
  )
  useEffect(
    () => {
      window.addEventListener('resize', onResize)
    }, []
  )
  console.log(document.documentElement.clientHeight)
  return tableSize
}

export default function App() {
  const [newData, setnewData] = useState(fakeData);
  const [newInput, setnewInput] = useState(fakeData);
  const [regName, setregName] = useState("null");
  const size = useWinSize();
  const tableSize = useTableSize();

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
        <div key="c" data-grid={{ x: 0, y: 0, w: 12, h: 1 }}>
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
                        console.log();
                      }
                    }
                  })}
                  dataSource={newInput}
                  pagination={false}
                  scroll={{ x: '100%', y: tableSize.height }}
                />
              </Layout>
            </Col>
          </Row>
        </div>
        <div key="d" data-grid={{ x: 0, y: 0, w: 12, h: 1 }}>
          <Row>
            <Col className="gutter-row" span={24}>
              <Layout>
                <Divider orientation="left">Reg info: {regName}</Divider>
                <Table
                  columns={field_column}
                  dataSource={newData}
                  scroll={{ x: '100%', y: tableSize.height }}
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