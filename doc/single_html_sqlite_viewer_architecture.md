# Address Planner 单 HTML SQLite Viewer 架构

状态：已实现并完成端到端验证（2026-08-03）

适用项目：`address_planner`（报告生成端）、`apv_html`（浏览器 Viewer）

不适用项目：Electron 版 `ap_viewer`

schema v2 的已确认模板复用方案见
[`sqlite_template_reuse_design.md`](sqlite_template_reuse_design.md)。v2 保留轻量逻辑实例树，
并将 Node 定义与 Field Layout 内容寻址为可共享模板 DAG。

## 1. 决策摘要

Address Planner 的浏览报告采用以下架构：

1. 报告交付物必须是一个可离线打开的 HTML 文件，不依赖网络、服务端或外部数据文件。
2. 生成端不再把完整递归 JSON 作为 Viewer 的运行时数据源，而是生成规范化的 SQLite 数据库。
3. SQLite 数据库经 gzip 压缩和 Base64 编码后嵌入 HTML；SQLite WASM、JavaScript 和 CSS 也全部嵌入同一 HTML。
4. HTML 启动时将数据库解压到 SQLite WASM 内存，但不把全库记录转换为 JavaScript 对象。
5. Viewer 初始只查询根节点；用户展开某个 AddressSpace 时，才按 `parent_id` 查询它的直接子节点；点击 Register 时，才查询对应 Fields。
6. React 只持有当前展开路径和有限缓存中的查询结果，不维护完整递归对象树。
7. 大型同级节点列表必须分页或虚拟化，不能一次性创建全部 DOM。

本方案中的“动态加载”是应用层的按需查询和按需对象化：未展开节点不会进入 JavaScript 对象树和 React 渲染树。简单版本仍会在启动时把完整 SQLite 文件解压到 WASM 内存；只有实际数据证明数据库本体内存也不可接受时，才升级为分页 VFS。

## 2. 背景与问题

当前 `apv_html` 通过以下方式静态导入数据：

```js
import bankData from './data.json';
```

完整递归 JSON 会在构建时进入 JavaScript bundle，并在页面启动时整体解析。该方式存在以下问题：

- 生成目录、Viewer 源码和构建产物可能保存多份相同数据。
- JSON 重复保存属性名，原始体积较大。
- 页面启动时创建完整 JavaScript 对象树，内存开销远高于文件本身。
- Ant Design Table 接收完整 `children` 树；即使节点未展开，也已经完成数据加载和对象创建。
- `pagination={false}` 和普通滚动区域不能控制超大同级列表的 DOM/React 开销。
- 数据与 UI 编译绑定，每次数据变化都需要重新编译 Viewer 源码。

## 3. 目标与非目标

### 3.1 目标

- 只交付一个 `.html` 文件，支持在无网络环境下使用。
- 支持通过 `file://` 双击打开，不要求启动本地 HTTP 服务。
- 未展开 AddressSpace 的记录不转换为 JavaScript 对象，也不进入 React 状态。
- 未点击 Register 的 Fields 不查询、不对象化、不渲染。
- 支持按名称、地址、类型搜索和后续扩展复杂查询。
- 数据库结构有明确版本，可被生成端和 Viewer 双方校验。
- 保留 64 位地址精度，不经过 JavaScript `Number` 导致精度损失。
- 构建结果可校验、可测试，并能与旧 JSON 报告做语义一致性比较。

### 3.2 非目标

- 第一阶段不实现 SQLite Page 级的按需解压。
- 第一阶段不引入服务端、Electron、Tauri 或本地守护进程。
- Viewer 不修改数据库；嵌入数据库是只读报告快照。
- 不将 IndexedDB/OPFS 作为正常运行依赖，也不在用户机器上产生持久化数据库。
- 不要求继续把大型 `data.json` 嵌入或提交到 `apv_html` 仓库。

## 4. 总体架构

```mermaid
flowchart LR
    A["Address Planner 对象模型"] --> B["SQLite Report Writer"]
    B --> C["规范化 SQLite 数据库"]
    C --> D["完整性校验与 VACUUM"]
    D --> E["确定性 gzip + Base64"]
    F["apv_html Viewer Template"] --> G["Single HTML Packager"]
    H["SQLite WASM"] --> G
    E --> G
    G --> I["单个 Address Map HTML"]
    I --> J["浏览器启动：初始化 WASM 与数据库"]
    J --> K["只查询根节点"]
    K --> L["展开 AddressSpace：查询直接子节点"]
    L --> M["点击 Register：查询 Fields"]
```

### 4.1 组件职责

`address_planner`：

- 将当前对象模型规范化写入 SQLite。
- 保证 ID、层级、地址、字段和排序的正确性。
- 校验数据库并生成单 HTML。
- 管理数据库 schema 版本及兼容性测试。

`apv_html`：

- 提供不包含业务数据的 Viewer HTML 模板。
- 嵌入并初始化 SQLite WASM。
- 提供数据库访问层、React 状态管理和 UI。
- 实现展开查询、Register 查询、分页、虚拟化、缓存和搜索。

Electron 版 `address_planner/ap_viewer`：

- 不参与此方案。
- 不作为单 HTML Viewer 的依赖或交付形式。

## 5. 单 HTML 容器格式

最终 HTML 至少包含以下内容：

```html
<script id="apv-manifest" type="application/json">
{
  "containerVersion": 1,
  "schemaVersion": 1,
  "codec": "gzip+base64",
  "databaseSha256": "...",
  "databaseBytes": 123456,
  "compressedBytes": 23456
}
</script>

<script id="apv-database" type="application/octet-stream">
...Base64 encoded gzip-compressed SQLite database...
</script>

<script id="apv-sqlite-wasm" type="application/octet-stream">
...Base64 encoded SQLite WASM supplied by the Viewer template...
</script>
```

应用 JavaScript、CSS、字体和图标必须全部内嵌。不得存在运行时网络请求或相对文件引用。

### 5.1 启动流程

1. 读取并校验 `apv-manifest`。
2. Base64 解码嵌入的 SQLite WASM，并通过 Blob URL 初始化运行时。
3. 分段 Base64 解码数据库载荷，避免同时创建多个完整 Base64 副本。
4. 使用浏览器原生 `DecompressionStream('gzip')` 解压；需要覆盖不支持该 API 的目标浏览器时，启用内嵌 JS fallback。
5. 打开 SQLite 内存数据库。
6. 执行 schema、版本、完整性和哈希检查。
7. 设置只读模式并准备复用查询语句。
8. 查询根节点并渲染首屏。
9. 解码成功后清空数据库和 WASM 对应的 Base64 DOM 文本，允许浏览器回收字符串内存。

### 5.2 Worker 边界

SQLite WASM 和数据库查询优先运行在 Web Worker 中，避免数据库初始化和查询阻塞 React 主线程。Worker 源码同样内嵌在 HTML，通过 Blob URL 创建，不产生外部文件。

推荐启动序列：

1. 主线程从 HTML 提取压缩数据库并分段 Base64 解码。
2. 主线程通过 transferable `ArrayBuffer` 将压缩载荷所有权转移给 Worker，避免复制。
3. Worker 完成 gzip 解压、SQLite WASM 初始化和数据库打开。
4. 主线程立即清空对应 DOM 文本和已转移引用。
5. 主线程与 Worker 使用带 `requestId` 的消息协议调用 `AddressPlannerStore`。
6. Worker 只返回当前查询页的普通对象，不返回数据库全量数据。

消息至少包含：

```ts
type StoreRequest = {
  requestId: number;
  operation: 'roots' | 'children' | 'fields' | 'findByName' | 'findByAddress';
  parameters: unknown;
};

type StoreResponse = {
  requestId: number;
  ok: boolean;
  result?: unknown;
  error?: { code: string; message: string };
};
```

节点折叠、搜索词变化或组件卸载后，主线程必须忽略已过期 `requestId` 的返回结果。若所选 SQLite WASM 运行时支持中断查询，可进一步实现主动取消。

`file://` 下的 Blob Worker、WASM Blob URL 和 transferable buffer 必须进入端到端兼容性测试；若目标浏览器不支持其中某项，才允许回退到主线程数据库适配器，查询接口保持不变。

### 5.3 SQLite WASM 运行时要求

具体运行时由实现 PoC 选定，但必须满足：

- 能从内存中的 SQLite 字节打开只读数据库。
- SQLite WASM 二进制可完全内嵌并通过 Blob URL 初始化。
- 支持 Web Worker。
- 支持绑定参数、预编译语句、64 位整数或原始 BLOB 读取。
- 能明确 finalize statement、关闭数据库并释放 WASM 资源。
- 许可证允许随生成报告分发。
- 构建后不尝试从 CDN、npm registry 或其他网络位置读取资源。

PoC 应至少比较候选运行时的最终 HTML 增量、初始化峰值内存、`file://` 兼容性和 Worker 集成难度，再冻结依赖和版本。

### 5.4 明确的内存边界

简单架构的稳定态内存近似为：

```text
SQLite WASM 运行时
+ 一份未压缩 SQLite 数据库
+ SQLite Page Cache
+ 当前展开节点的 JavaScript 查询结果
+ 当前可见的 React/DOM 数据
+ 有上限的查询结果缓存
```

它消除了“全量数据库记录对应的 JavaScript 对象树”，但没有消除“一份完整 SQLite 数据库”。

## 6. SQLite 数据模型

### 6.1 元数据表

```sql
CREATE TABLE metadata (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

必需键：

| 键 | 含义 |
|---|---|
| `schema_version` | 数据库 schema 版本 |
| `generator_version` | Address Planner 生成器版本 |
| `viewer_min_version` | 最低兼容 Viewer 版本 |
| `model_name` | 报告模型名 |
| `root_count` | 根节点数量 |
| `node_count` | 节点总数 |
| `field_count` | Field 总数 |

不得写入当前时间等不稳定信息，除非明确要求，否则相同模型应尽可能生成相同字节结果。

### 6.2 节点表

AddressSpace、RegSpace、Memory 和 Register 统一存入 `nodes`，通过 `kind` 区分：

```sql
CREATE TABLE nodes (
    id            INTEGER PRIMARY KEY,
    parent_id     INTEGER REFERENCES nodes(id),
    kind          INTEGER NOT NULL,
    sort_order    INTEGER NOT NULL,
    name          TEXT NOT NULL,
    start_addr    BLOB NOT NULL CHECK(length(start_addr) = 8),
    end_addr      BLOB NOT NULL CHECK(length(end_addr) = 8),
    size_bytes    BLOB NOT NULL CHECK(length(size_bytes) = 8),
    description   TEXT NOT NULL DEFAULT '',
    child_count   INTEGER NOT NULL DEFAULT 0,
    field_count   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX idx_nodes_parent_order
ON nodes(parent_id, sort_order, id);

CREATE INDEX idx_nodes_parent_address
ON nodes(parent_id, start_addr, id);

CREATE INDEX idx_nodes_name
ON nodes(name);
```

`kind` 使用整数枚举，第一版建议：

| 值 | 类型 |
|---:|---|
| 1 | AddressSpace/System |
| 2 | RegSpace/Bank |
| 3 | Memory（预留；当前对象模型没有可可靠识别的独立 Memory 类型） |
| 4 | Register |

第一版 Writer 不根据“无子节点”等启发式规则猜测 Memory；普通对象仍写为
AddressSpace。只有对象模型引入明确 Memory 类型或标记并补齐契约测试后，才会
生成 `kind = 3`。

地址使用固定 8 字节大端无符号整数 BLOB：

- 完整覆盖 `0` 到 `2^64 - 1`。
- 避免 JavaScript `Number` 的 53 位精度限制。
- 同长度大端 BLOB 的 SQLite 排序与无符号数值顺序一致。
- Viewer 适配层将其转换为 JavaScript `BigInt`，展示时再格式化为十六进制。

### 6.3 Field 表

```sql
CREATE TABLE fields (
    id             INTEGER PRIMARY KEY,
    register_id    INTEGER NOT NULL REFERENCES nodes(id),
    sort_order     INTEGER NOT NULL,
    name           TEXT NOT NULL,
    lsb            INTEGER NOT NULL,
    msb            INTEGER NOT NULL,
    external       INTEGER NOT NULL DEFAULT 0,
    sw_access      INTEGER NOT NULL,
    hw_access      INTEGER NOT NULL,
    default_value  BLOB,
    description    TEXT NOT NULL DEFAULT '',
    CHECK(lsb >= 0),
    CHECK(msb >= lsb),
    CHECK(external IN (0, 1))
);

CREATE INDEX idx_fields_register_order
ON fields(register_id, sort_order, id);
```

`sw_access` 和 `hw_access` 使用稳定整数枚举，具体值由共享 schema 常量定义。禁止由 Python 和 JavaScript 各自维护互不校验的枚举副本。

`default_value` 使用最小必要的大端 BLOB，避免超出 JavaScript 安全整数范围。空值表示未定义，不等同于数值 0。

### 6.4 可选属性

第一版遇到不能稳定映射到固定列的属性时，使用扩展表，不把 JSON 重新塞回主表：

```sql
CREATE TABLE node_attributes (
    node_id  INTEGER NOT NULL REFERENCES nodes(id),
    key      TEXT NOT NULL,
    value    TEXT NOT NULL,
    PRIMARY KEY(node_id, key)
);
```

高频、需要过滤或排序的属性后续应升级为正式列；低频展示属性可保留在扩展表。

## 7. ID、层级与排序规则

- ID 由生成器确定，必须在单份报告内唯一。
- 第一版采用按规范遍历顺序分配的整数 ID，禁止使用 Python 对象地址或随机 UUID。
- `parent_id IS NULL` 表示根节点。
- 每个节点只保存父引用，不递归保存 `children`。
- `child_count` 和 `field_count` 用于 UI 判断是否显示展开按钮，不需要额外查询。
- `sort_order` 必须由生成器明确写入，Viewer 不依赖 SQLite 未定义的自然行顺序。
- 同一父节点下的最终稳定顺序为 `(sort_order, id)`。

## 8. 查询协议

Viewer 不允许组件直接拼接 SQL。所有查询通过 `AddressPlannerStore`：

```ts
interface AddressPlannerStore {
  getMetadata(): Promise<ReportMetadata>;
  getRoots(cursor?: PageCursor): Promise<NodePage>;
  getChildren(parentId: number, cursor?: PageCursor): Promise<NodePage>;
  getFields(registerId: number, cursor?: PageCursor): Promise<FieldPage>;
  findByName(query: string, limit: number): Promise<NodeSummary[]>;
  findByAddress(address: bigint, limit: number): Promise<NodeSummary[]>;
  dispose(): void;
}
```

### 8.1 根节点查询

```sql
SELECT id, kind, sort_order, name, start_addr, end_addr,
       size_bytes, description, child_count, field_count
FROM nodes
WHERE parent_id IS NULL
ORDER BY sort_order, id
LIMIT ?;
```

### 8.2 展开 AddressSpace

只查询直接子节点：

```sql
SELECT id, parent_id, kind, sort_order, name, start_addr, end_addr,
       size_bytes, description, child_count, field_count
FROM nodes
WHERE parent_id = ?
  AND (sort_order > ? OR (sort_order = ? AND id > ?))
ORDER BY sort_order, id
LIMIT ?;
```

使用基于 `(sort_order, id)` 的游标分页，避免超大父节点使用高 `OFFSET` 时逐渐变慢。

默认页大小建议为 200，允许用户切换到 100/500/1000；硬上限建议为 2000。实际默认值应通过基准测试确认。

### 8.3 点击 Register

```sql
SELECT id, register_id, sort_order, name, lsb, msb, external,
       sw_access, hw_access, default_value, description
FROM fields
WHERE register_id = ?
ORDER BY sort_order, id
LIMIT ?;
```

### 8.4 地址查询

固定 8 字节大端 BLOB 可以用于地址范围比较：

```sql
SELECT id, parent_id, kind, name, start_addr, end_addr
FROM nodes
WHERE start_addr <= ? AND end_addr >= ?
ORDER BY size_bytes, id
LIMIT ?;
```

两个参数都是同一地址的 8 字节大端编码。需要通过真实数据检查查询计划；如果全局地址搜索成为热点，可增加专用地址索引或辅助表。

## 9. React 数据和渲染模型

### 9.1 禁止完整嵌套树

React 状态不得保存从根开始的完整递归 `children`。推荐结构：

```ts
type ViewerState = {
  expandedIds: Set<number>;
  selectedRegisterId?: number;
  nodesById: Map<number, NodeSummary>;
  childPagesByParent: Map<number, NodePageState>;
  fieldPagesByRegister: Map<number, FieldPageState>;
};
```

`childPagesByParent` 只包含已展开或缓存的父节点结果。折叠节点不要求立即删除，但必须受缓存预算约束。

### 9.2 可见行计算

- 根据 `expandedIds` 和已加载的直接子节点生成可见扁平行列表。
- Table 不接收包含全量递归 `children` 的对象。
- 展开图标由 `child_count > 0` 决定。
- 首次展开显示 loading 状态；查询成功后插入直接子节点。
- 查询失败在对应节点行内显示可重试错误，不让整个 Viewer 白屏。

### 9.3 虚拟化与分页

- 左侧节点表使用真正的行虚拟化，而不只是 `scroll.y`。
- 单个父节点子项超过默认页大小时显示“加载更多”或分页控制。
- 右侧 Field 表同样支持虚拟化；Field 数量较小时可以一次查询全部，但仍保留上限。
- React `key` 使用数据库 `id`，不得使用数组下标。

## 10. 查询结果缓存

缓存目标是减少反复展开的 SQL 和对象创建，不是复制整个数据库。

推荐策略：

- 根节点常驻。
- 当前展开路径常驻。
- 子节点结果使用 LRU。
- 初始建议最多缓存 32 个父节点结果，另设估算字节上限。
- Field 结果单独使用较小 LRU，例如最近 16 个 Register。
- 超过任一上限即淘汰最久未使用且当前未展开的数据。
- 折叠节点仍可保留缓存；内存压力或超过预算时再释放。
- 缓存被淘汰后重新展开，重新执行 SQLite 查询。

缓存上限必须集中配置，并在开发模式显示命中率、条目数和估算内存，便于真实模型调优。

## 11. 生成和打包流程

### 11.1 SQLite 生成

Python 生成端使用标准库 `sqlite3`，在临时目录中完成：

1. 创建数据库并设置 schema 版本。
2. 在单个事务中按确定顺序写入节点和 Fields。
3. 创建索引。
4. 校验计数、层级、地址和引用关系。
5. 执行 `PRAGMA integrity_check`，必须得到 `ok`。
6. 执行 `PRAGMA foreign_key_check`，结果必须为空。
7. 执行 `ANALYZE`；只有基准证明有益时才保留统计表。
8. 执行 `VACUUM`，删除构建过程留下的空闲页。
9. 关闭数据库后计算 SHA-256。

构建用数据库建议：

```sql
PRAGMA journal_mode = OFF;
PRAGMA synchronous = OFF;
PRAGMA temp_store = MEMORY;
PRAGMA foreign_keys = ON;
```

这些设置只用于离线生成临时报告数据库，不能复制到需要事务持久性的通用数据库代码。

### 11.2 压缩

- 使用 gzip 压缩整个 SQLite 文件。
- gzip 时间戳固定为 0，避免同一输入产生不同输出。
- Base64 使用标准字母表且不插入不必要空白。
- manifest 同时记录未压缩和压缩字节数、数据库 SHA-256。

### 11.3 Viewer 模板

`viewer/apv_html` build-time submodule 的 CI 构建出一个无业务数据的模板，例如：

```text
dist/address-planner-viewer.template.html
```

模板对生成端暴露两个明确占位符：

```text
__APV_MANIFEST__
__APV_DATABASE_GZIP_BASE64__
```

SQLite WASM 和 Worker runtime 由 `apv_html` 构建过程提前嵌入模板，
不属于每份报告需要再次注入的数据占位符。

`address_planner` 必须随 Python 包分发由
`tools/sync_viewer_template.py` 校验并固定的 Viewer 模板。普通
`AddressSpace.generate()` 直接使用该模板，不在用户生成报告时执行
`npm install`、初始化 Viewer submodule 或在线下载资源。

`viewer-template.lock.json` 同时锁定 submodule commit、产物大小、SHA-256 和
容器/schema 兼容版本。CI 必须从 submodule 重建模板，并通过
`python tools/sync_viewer_template.py --check` 确认 gitlink、lock、构建产物和
vendored 模板四者一致。

最终输出建议命名：

```text
<output>/html/<model_name>_address_map.html
```

### 11.4 原子发布

- 所有内容先写入同目录临时文件。
- 完成 HTML 结构、载荷哈希和数据库校验后再原子替换目标文件。
- 任一步失败时不得留下看似成功的半成品报告。

## 12. 数据库运行时安全与生命周期

打开数据库后执行：

```sql
PRAGMA query_only = ON;
PRAGMA foreign_keys = ON;
```

要求：

- 所有用户输入通过绑定参数进入预编译语句，禁止字符串拼 SQL。
- schema 版本不兼容时显示明确错误，不尝试猜测列含义。
- 数据库 SHA-256 不匹配时终止打开并提示报告损坏。
- 数据库和预编译语句由 Worker 独占，React 组件不得直接持有运行时对象。
- React 卸载或页面关闭时 finalize statements、关闭数据库并释放 WASM 资源。
- 搜索输入做 debounce，并设置结果数和执行时间保护。

## 13. 兼容与迁移

第一阶段保留现有 JSON 产物，新增 SQLite 单 HTML 目标，用于一致性验证：

```text
旧：<output>/html/data.json
新：<output>/html/<model_name>_address_map.html
```

迁移步骤：

1. 建立 SQLite schema 和 Python writer。
2. 使用固定 fixture 同时生成 JSON 与 SQLite。
3. 对根节点、所有 parent-child 关系、Register Fields、地址和访问类型做全量语义比较。
4. 完成 Viewer 查询层和基础展开交互。
5. 加入单 HTML 离线打包。
6. 加入大型模型基准、分页、虚拟化和 LRU。
7. 验证稳定后，将 JSON Viewer 标记为 deprecated。
8. 在明确没有兼容调用者后，另行决定是否停止默认生成大型 JSON。

迁移期禁止直接删除 `report_json()`，避免破坏现有脚本和验收测试。

## 14. 测试策略

### 14.1 生成端单元测试

- 空模型、单根、多根、深层嵌套。
- 同名节点、零地址、边界地址和最大 64 位无符号地址。
- Register 无 Field、多个 Field、默认值为空或超出 53 位。
- 每种 `sw_access`/`hw_access` 枚举。
- `child_count`、`field_count` 与实际查询一致。
- `(parent_id, sort_order, id)` 顺序稳定。
- SQLite `integrity_check` 通过。

### 14.2 契约测试

- Python 侧 schema 常量与 Viewer 侧 schema 常量一致。
- Viewer 拒绝未知大版本 schema。
- 固定 fixture 的 SQLite 查询结果与旧 JSON 语义一致。
- 生成报告不依赖网络。

### 14.3 Viewer 测试

- 首屏只查询 roots。
- 未展开节点不调用 `getChildren()`。
- 首次展开只查询直接子节点。
- 点击 Register 才调用 `getFields()`。
- 折叠、再次展开和 LRU 淘汰行为正确。
- 超大同级节点列表能分页并保持稳定顺序。
- 查询错误、数据库损坏和版本不兼容有可理解提示。

### 14.4 端到端测试

- 生成的唯一交付物为一个 HTML。
- 在无网络、`file://` 环境打开成功。
- 浏览器开发者工具 Network 面板没有外部请求。
- 展开结果和地址/Field 信息正确。
- 文件名和路径包含空格、中文时仍可打开。

## 15. 性能基准与验收指标

必须准备小、中、大三档固定模型，记录以下指标：

- 原始递归 JSON 大小。
- SQLite 文件大小。
- gzip 后数据库大小和最终 HTML 大小。
- 首次可交互时间。
- Base64 解码、gzip 解压、WASM 初始化和数据库打开耗时。
- 主线程长任务数量和最长阻塞时间。
- 根节点查询、AddressSpace 展开、Register Field 查询的 P50/P95。
- 初始 JS Heap、展开典型路径后的 JS Heap、WASM Memory。
- 可见行数、DOM 节点数和滚动帧率。
- LRU 缓存命中率和淘汰次数。

架构级验收条件：

1. JS 对象和 React 状态规模与“已展开/缓存的记录数”相关，不与全库记录数线性增长。
2. 未展开节点不会出现在 React 状态或查询结果缓存中。
3. 稳定态只保留一份可查询 SQLite 数据库，不保留完整解码缓冲区和 Base64 DOM 文本副本。
4. 任一单次 UI 查询均有明确 `LIMIT`，不存在无界全表结果集。
5. 普通滚动不会一次创建全部行 DOM。

具体毫秒和 MB 阈值必须基于真实最大模型及目标机器测量后冻结，不能只使用当前 10 KB 示例数据得出。

## 16. 风险与应对

### 16.1 启动时数据库整体解压

风险：数据库本身非常大时，WASM 内存和启动峰值仍然较高。

应对：

- 首先依靠 SQLite 规范化和 gzip 降低存储体积。
- 解码后及时清空 Base64 DOM 内容和中间缓冲区。
- 使用真实最大模型测量峰值。
- 只有超过目标设备预算时，升级为 SQLite Page 分块 + 只读 VFS；上层 `AddressPlannerStore` 接口保持不变。

### 16.2 单 HTML 体积限制

风险：某些邮件、文档系统或浏览器对超大单文件处理较差。

应对：记录最终 HTML 大小并在生成时给出阈值告警；该风险不能通过运行时逻辑完全消除。

### 16.3 SQLite/WASM 兼容性

风险：WASM 初始化、Blob URL 或 gzip API 在目标浏览器上的能力不同。

应对：冻结支持的浏览器版本；在 CI 中用目标 Chrome/Edge 离线打开；必要时内嵌 gzip fallback。

### 16.4 查询索引不足

风险：搜索或地址范围查询可能退化为全表扫描。

应对：对所有正式查询运行 `EXPLAIN QUERY PLAN` 契约测试，并用大型 fixture 验证；不为尚不存在的查询提前增加大量索引。

## 17. 分阶段实现计划

### Phase 1：数据库契约

- 固化 schema、枚举和 64 位编码。
- 实现 Python SQLite writer。
- 实现旧 JSON 与 SQLite 语义一致性测试。

### Phase 2：Viewer 数据访问层

- 在 `apv_html` 集成 SQLite WASM。
- 实现 Worker 消息协议、`AddressPlannerStore` 和预编译查询。
- 用普通 `.sqlite` fixture 完成根、展开和 Field 查询测试。

### Phase 3：按需 React UI

- 移除 `import data.json`。
- 改为扁平可见行模型。
- 加入节点 loading/error 状态、游标分页和虚拟化。
- 加入有上限的 LRU。

### Phase 4：单 HTML 打包

- 内嵌 JS、CSS、SQLite WASM 和 gzip 数据库。
- 实现离线初始化、哈希和 schema 校验。
- 清理中间字符串/缓冲区，验证 `file://`。

### Phase 5：集成和基准

- `address_planner` 调用固定 Viewer 模板生成最终 HTML。
- 增加小、中、大模型基准和端到端测试。
- 根据真实数据调整索引、分页、缓存和告警阈值。

### Phase 6：可选升级

仅当完整 SQLite 数据库常驻 WASM 超出目标内存预算时：

- 将数据库按 SQLite Page 独立压缩嵌入。
- 实现只读分页 VFS 和 Page LRU Cache。
- 保持 schema、SQL 和 `AddressPlannerStore` 不变。

## 18. 已确认的关键决策

| 项目 | 决策 |
|---|---|
| 交付形式 | 单个离线 HTML |
| 数据模型 | 规范化 SQLite，不使用递归 JSON 作为 Viewer 主数据源 |
| 应用加载粒度 | 每次展开一个 AddressSpace，只查询直接子节点 |
| Register 数据 | 点击时查询 Fields |
| SQLite 物理加载 | 第一阶段完整解压到 WASM 内存 |
| UI 状态 | 只保留展开路径和有限缓存 |
| 大列表 | 游标分页 + 虚拟化 |
| 地址精度 | 8 字节大端无符号 BLOB + JavaScript BigInt |
| 压缩 | 整库确定性 gzip，再 Base64 嵌入 |
| 运行方式 | `file://` 离线打开，无服务端、无网络请求 |
| 桌面框架 | 不采用 Electron |
| 后续扩展 | 内存不达标时升级分页 VFS，不改上层查询接口 |

## 19. 实现与验证记录

本方案第一阶段已在 `address_planner` 和 `apv_html` 两个仓库实现：

- `address_planner` 默认继续生成兼容用 `data.json`，同时生成 SQLite 驱动的
  `<model_name>_address_map.html`；普通调用不需要传 Viewer 模板路径。
- SQLite Writer、单 HTML Packager 和内置 Viewer 模板都随 Python 包交付；
  中间 SQLite 仅在调用者显式请求时保留。
- `apv_html` 使用 `sql.js 1.14.1` + Web Worker；数据库、WASM、Worker、JS、CSS、
  gzip fallback 和第三方许可声明均嵌入最终 HTML。
- Viewer 初始只查询根节点，展开时查询直接子节点，点击 Register 时查询 Fields；
  使用游标 `LIMIT`、虚拟表格和最多 32 个父节点的 LRU 缓存。
- Viewer 保留默认左右等宽的 `Bank Info / Reg Info` 视觉结构，使用低对比度
  Fog Sage 灰绿色层级；画布、空表体、普通表面、层级行和抬升表头均有明确且不含
  纯白的层次。Register 整行均可选择，四个较长的
  Address/Access 表头分两行显示。中间“信号总线”分隔线和两张表的每个列边界均可
  拖动，横向滚动条固定在各自面板底部。顶部使用紧凑的 `Address Planner v1.2.2`
  仪器铭牌；`v1.2.2` 是仓库当前最高正式发布标签。标题右侧常驻显示 Nodes、Fields 和
  Database 三项紧凑读数；前两项来自 SQLite metadata，Database 是 manifest 中经过校验的
  未压缩 SQLite 字节数，不表示 gzip 载荷或最终 HTML 大小。报告名称、schema 等调试信息
  不常驻显示；数据库和首屏根节点加载完成后仍通过无障碍 live region 宣告 ready，但不占用
  视觉空间。
- 中间分隔线采用像素边界而非百分比边缘区：Bank 和 Reg 各自至少保留 320 px；到达最小
  宽度后继续向边缘拖动 28 px 才吸附为完全收起。原面板仍保留状态但不可交互，页面边缘
  保留 10 px 可聚焦、可拖动的恢复轨道，轨道不再显示无实际作用的 `< >` 箭头；从边缘
  向内拖过 332 px 即可恢复。键盘也可完成收起和恢复；列宽、展开状态、滚动位置和所选
  Register 不因面板收起而重置。窄视口下最小宽度自动降为可用宽度的一半。
- `Bank Info` 和 `Reg Info` 标题栏各自提供统一的 28 px 可视列按钮，弹出菜单可连续
  显示或隐藏本表可选列；两张表的 `Name` 均始终保留，并提供 `Show all` 快速恢复入口。
  Bank 的 `End Address` 与 Reg 的 `External` 默认隐藏，为其他列让出首屏空间。隐藏列会
  真正退出 Table columns 和总宽度计算，但保留原拖动宽度，恢复后不会重置用户设置；
  两侧按钮以中性状态点独立提示当前存在隐藏列。所有列仍可拖动，最小列宽由 60 px
  降至 32 px。每次列显隐后，最后一个可见列作为流动列填满剩余空间；此前各列严格
  保持用户设置的像素宽度，不再随面板整体宽度按比例伸缩。流动列仍保留首选最小宽度，
  面板不足时继续触发横向滚动。
- 节点表纵向滚动时，会在表体顶部保留当前可见层级的直接父行；该上下文行独立于被
  虚拟列表回收的原始 DOM，并与当前可见列、列宽和横向滚动实时同步。只固定一行直接
  父级，避免递归层级较深时祖先栈挤占有效视口。固定行按当前 Ant Table 的真实总宽度
  和列伸缩结果布局，并使用不透明背景覆盖下层内容，面板变宽后也不会错列或透出数据行。
  固定父行复用普通树行的无边框线性展开按钮；按钮可聚焦，并支持鼠标点击、Enter 和
  Space 折叠当前父节点，而不是仅作为不可操作的上下文图标。通过固定行折叠时，虚拟
  列表会先锚定到仍存活的前一行，清除旧滚动偏移；折叠后的真实父行会立即回到表格可视区。

  Bank 层级展开/合并采用 180 ms 的箭头旋转、淡入淡出和轻微纵向位移动画；系统启用
  reduced-motion 时自动取消动画。节点和 Field 数据行的实测高度均为 39 px，在不改变
  面板、虚拟滚动和底部滚动条布局的前提下提高纵向信息密度。
- 实际 Chrome `file://` 测试会在打开页面前删除同目录兼容 JSON，且未启用
  `--allow-file-access-from-files`。测试验证无外部请求、无严重控制台错误，并逐层检查
  根节点、Bank、Register 和 Field 的按需出现顺序。

最终大型固定基准包含 50 个 Bank、10,000 个 Register、80,000 个 Field；全量比较
10,051 个节点和 80,000 个 Field 后语义一致性为 PASS：

| 产物 | 字节数 | 相对原始 JSON |
|---|---:|---:|
| 旧递归 JSON | 36,647,975 | 基准 |
| SQLite | 12,316,672 | 减少 66.39% |
| JSON 的确定性 gzip | 597,714 | — |
| SQLite 的确定性 gzip | 1,940,404 | 比 gzip JSON 大 224.64% |
| Viewer 空模板 | 1,933,898 | — |
| 最终单 HTML | 4,521,259 | 比原始 JSON 减少 87.66% |

重复键很多的 JSON 对 gzip 极其友好，因此“压缩数据库载荷”不保证比“压缩 JSON”小；
SQLite 的主要收益是原始持久化体积、索引查询、精确类型和避免全量 JavaScript 对象化。
很小的模型还会受到 SQLite 页和 schema 的固定开销影响，例如 6,618 字节 JSON 的
测试 fixture 对应 45,056 字节 SQLite。是否停止默认生成兼容 JSON，应在确认下游没有
依赖后另行决定。

可复现尺寸报告位于
`build/sqlite_size_benchmark_final/size_report.json`。最终验证结果为：Viewer 单测 11 项
通过，Python 单元/示例/浏览器集成测试 32 项通过，兼容性与清单测试 15 项通过。
