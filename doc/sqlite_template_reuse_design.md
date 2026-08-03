# SQLite 模板复用设计

状态：已实施并完成 v1/v2 语义一致性验证

目标 schema：v2

决策日期：2026-08-03

## 1. 决策摘要

Address Planner 的 Viewer 数据库采用“逻辑实例树 + 物理模板 DAG”：

1. AddressSpace、RegSpace/Bank 和 Register 的每次逻辑出现仍保留一条轻量实例记录。
2. 实例记录保存父子关系、顺序、实例名和已计算的绝对地址。
3. 节点定义、Register Field Layout 和重复字符串通过内容寻址的模板表复用。
4. Viewer 仍按 `parent_id` 展开节点，不在显示时临场计算绝对地址。
5. 第一版不实现“纯虚拟 Bank”；数据库尺寸和真实复用率证明有必要后再升级。
6. schema v2 已成为默认输出；迁移期可显式传入
   `schema_version=SCHEMA_VERSION_V1` 生成旧布局。
7. Viewer 在 Worker/Store 内提供 v1/v2 adapter，React 和交互层保持同一业务接口。

本设计只改变 Viewer 报告的物理存储，不改变现有 Python DSL、`deepcopy` 实例化、RTL 生成或头文件生成语义。

## 2. 对象模型事实

`AddressSpace.add()` 和 `RegSpace.add()` 都会先复制传入的子树，再修改副本根节点的名称、父节点和偏移。因此用户建模时已经存在明确的“定义 -> 实例”语义，但最终树中的 Python 对象身份互不相同。

结论：

- 不能使用 `id(node)` 或原型对象身份作为模板 ID。
- 必须在报告生成时，对最终树自底向上计算稳定内容 Hash。
- 逻辑实例树仍必须无环；只有物理定义层允许多个实例共享同一模板。
- 绝对地址是父链和局部偏移的派生值，不属于可复用定义。

## 3. 数据分层

### 3.1 逻辑实例

`node_occurrences` 每个可显示 AddressSpace、Bank 或 Register 保留一行，至少包含：

```text
id
parent_id
template_id
sort_order
name_text_id
start_addr
end_addr
```

主要用途：

- `WHERE parent_id = ?` 按需展开；
- 名称和绝对地址索引；
- 稳定的报告内节点 ID 和 React key；
- 搜索结果的祖先定位。

绝对地址在 Python writer 遍历最终 `deepcopy` 树时计算一次并写入数据库。Viewer 只读取该值，不递归重算。

### 3.2 节点模板

`node_templates` 保存可共享的 Viewer 可见节点定义：

```text
content_hash
kind
size_bytes
description_text_id
child_count
field_count
```

自身的实例名、父节点、绝对地址、全局路径和数据库 ID 不得进入模板 Hash。

### 3.3 子布局

`template_children` 表达一个父模板中有序的子槽位：

```text
parent_template_id
sort_order
child_template_id
relative_addr
child_local_name
```

子节点的局部名称和相对偏移是父模板中的 placement edge，不是子模板自身的固有身份。

`MultiPortOption` 可以允许同父节点下同地址多个视图，所以槽位必须保留 `sort_order`，不能使用名称或偏移作为唯一键。

既有 fluent DSL 和 MultiPort 模型还可能把逻辑子节点放到父节点名义 size 之外；v1/JSON
一直保留并显示这类 placement。v2 为保证语义兼容，只验证 occurrence 与模板 edge 的
名称、顺序、相对/绝对地址一致，不额外引入“子范围必须被父范围包含”的新规则。

### 3.4 Field Layout

Register Field 不按 Register 实例重复写入。Register occurrence 通过 template 间接引用 Field Layout：

```text
register occurrence
    -> register template
        -> template_fields
            -> field_defs
```

Field 可见语义包括：

```text
name
lsb/width
external
software access
hardware access
default value
description
```

Field 逻辑 ID 由 `(register_occurrence_id, field_sort_order)` 组成，不使用共享模板 ID 作为页面行 ID。

### 3.5 字符串与 Viewer 投影

重复名称和描述可进入 `texts` 字符串池。

v2 定义为 Viewer 可见语义投影；当前 Viewer 不读取的 `node_attributes`
已从 v2 schema 删除，不再写入报告，也不参与模板 Hash。v1 仍保留原表以保证旧布局
兼容。如果将来需要完整模型归档，应建立独立格式，不应让未显示属性无限扩张 Viewer
数据库。

### 3.6 已实施的物理表

v2 由以下七张表组成：

| 表 | 职责 |
| --- | --- |
| `metadata` | schema、生成器版本、逻辑计数和复用统计 |
| `texts` | 唯一 UTF-8 字符串池 |
| `node_templates` | 内容寻址的 Node 可见定义 |
| `field_defs` | 内容寻址的 Field 可见定义 |
| `template_children` | 父模板内有序的子 placement edge |
| `template_fields` | Register 模板内有序的 Field 引用 |
| `node_occurrences` | 完整逻辑树、实例名和绝对地址 |

为控制固定存储开销，v2 只建立两个经查询契约证明需要的二级索引：

```sql
CREATE INDEX idx_occurrences_parent_order
ON node_occurrences(parent_id, sort_order, id);

CREATE INDEX idx_occurrences_address
ON node_occurrences(start_addr, end_addr, id);
```

模板边和 Field 布局的主键已经覆盖它们的有序查找，不再增加反向索引；名称搜索目前
仍按 `texts.value` 做受 `LIMIT` 约束的查询，避免为了不能被 `%LIKE%` 使用的列额外付出
索引空间。

## 4. 内容寻址

模板使用带版本域分隔的稳定 SHA-256：

```text
H(
  schema/domain version,
  kind,
  size,
  description,
  ordered(child local name, relative offset, child template hash),
  ordered(field definition hash)
)
```

编码约束：

- 字符串使用 UTF-8 和明确长度前缀；
- 整数使用固定 8 字节大端编码；
- 子节点顺序沿用当前 `(bit_offset, original insertion order)`；
- Field 先按其完整可见语义独立计算 Hash；Node canonical record 只嵌入直接子模板和
  Field 定义的 32 字节 Hash，不递归复制整棵子树的 canonical bytes；
- 不对 Python repr、对象 ID 或 SQLite surrogate ID 做 Hash；
- Hash 相同后仍比较 canonical record，不只依赖碰撞概率。

只合并严格等价的可见语义，不做模糊相似匹配。一个 Bank 只有一个 Register 不同时，Bank 模板会分裂，但未变的 Register 和 Field Layout 仍可继续共享。

## 5. 查询契约

Viewer Store 的业务接口保持不变：

```text
metadata
roots
children
fields
findByName
findByAddress
```

关键行为：

- `children(parent_occurrence_id)` 查 `node_occurrences.parent_id`；
- `fields(register_occurrence_id)` 先解析 `template_id`，再查共享 Field Layout；
- 名称和地址搜索面向 occurrence，否则重复安装的 Bank 只会返回一条模板结果；
- 节点行使用 `n:<occurrence_id>`，Field 行使用 `f:<register_occurrence_id>:<field_order>`。

schema v2 不应迫使 React 组件知道 SQLite 表结构；兼容性改动限定在 Worker/Store adapter 内。

## 6. 交叉引用边界

`lock_list` 和 `magic_list` 存在实例放置时追加、按当前 Bank 兄弟名解析的语义，不能直接进入独立 Register 核心模板。

决策：

- Viewer v2 不显示它们，因此不写入 Viewer 数据库。
- 将来如需显示，必须在完整实例树中先解析为稳定相对路径，再写入独立 `cross_refs` 或 `instance_overrides`；不保存未解析的裸名称字符串。

## 7. 尺寸决策

当前 50 Bank / 10,000 Register / 80,000 Field 合成基准中：

| 产物 / schema | 原始字节 | 确定性 gzip |
| --- | ---: | ---: |
| 旧递归 JSON | 36,647,975 B | 597,714 B |
| schema v1 | 12,316,672 B | 1,940,404 B |
| schema v2：模板 DAG + occurrence | 876,544 B | 292,409 B |

这次测量中，v2 相比 v1 原始 SQLite 减少约 92.88%，gzip 载荷减少约
84.93%；相比原始 JSON 减少约 97.61%。这里的 292,409 B 是最终 packager 使用相同
确定性 gzip 路径得到的实际载荷；数值仍可能随 SQLite 版本和索引调整变化，以上是当前
实现测量，不是尺寸承诺。

逻辑到物理复用统计为：

- 10,051 个逻辑 Node 映射为 3 个 `node_templates`；
- 80,000 个逻辑 Field 映射为 8 个 `field_defs`；
- Node/Field 名称和描述进一步由 `texts` 去重。

该基准是严格重复率很高的理想样例，主要验证实现上限和 v1/v2 语义一致性；真实收益
取决于模板严格相等的比例。

同一基准中 v2 生成耗时 1.230 s，v1 为 1.437 s；当前 v2 并未以去重换取更慢的生成，
但时间同样只代表本次环境。Viewer 空模板为 1,940,870 B，打包后的 v2 单 HTML 为
2,330,900 B。

在“当前 SQLite 为 1 GiB，每个 Bank 平均有两个严格相同实例，不假设其他复用”的估算中：

| 方案 | 原始 SQLite 估算 |
| --- | ---: |
| 当前 schema v1 | 1,024 MiB |
| 模板 DAG + 轻量 occurrence | 约 445 MiB |
| 纯虚拟 Bank | 约 388 MiB |

推荐方案已获得纯虚拟 Bank 约 91% 的总节省收益，同时保留直接索引、稳定 ID 和简单分页。因此纯虚拟 Bank 不进入 v2 首版。

## 8. 非目标与后续升级

v2 首版不包含：

- 纯虚拟 Bank 子树；
- 通用 KV 式实例 override；
- 模糊相似子树合并；
- 修改 Address Planner DSL 以共享可变 Python 对象；
- SQLite Page/VFS 级按需解压。

要区分“存储复用”和“整库内存”：推荐方案能大幅缩小数据库，但当去重后 SQLite 仍达到数百 MiB 时，单 HTML 启动时整库解压仍可能超出浏览器内存边界。该情况应优先引入分块压缩和 SQLite Page/VFS 按需加载，而不是先实现纯虚拟 Bank。

## 9. 实施与兼容状态

已完成：

1. Python writer 同时保留 schema v1 和 v2；`SCHEMA_VERSION` 现指向 v2，
   `write_sqlite_report(..., schema_version=SCHEMA_VERSION_V1)` 可显式生成旧布局。
2. `AddressSpace.report_sqlite()`、`report_single_html()` 透传 `schema_version`；
   `generate()` 通过 `sqlite_schema_version` 暴露同一兼容开关。
3. Writer 自底向上构建 Field 定义和 Node 模板，用 canonical bytes + SHA-256
   内容寻址；强制 Hash 碰撞测试确认不同 canonical record 不会被误合并。
4. v2 写入完整 occurrence 树和绝对地址，验证外键、DAG 无环、placement、自身地址范围、
   顺序、计数、孤儿记录、内容 Hash 和 64 位值。
5. Viewer Worker 在初始化时按 schema 选择 v1/v2 SQL adapter，Store 的
   `metadata`、`roots`、`children`、`fields`、`findByName` 和 `findByAddress`
   契约保持不变。
6. 固定 fixture 和大型基准均将 v2 投影与 JSON/v1 逐 Node、Field 比较；还覆盖
   同地址 MultiPort、深拷贝 Bank 不同基址、单 Field 差异、64 位地址和确定性输出。
7. `apv_html` 继续作为 `viewer/apv_html` build-time submodule 管理。Viewer 变更先在
   独立仓库提交，再更新 submodule gitlink，并用 `tools/sync_viewer_template.py` 同步
   vendored 单 HTML 模板与 `viewer-template.lock.json`；普通报告生成不依赖 Node.js。

后续仅需在真实最大项目和目标浏览器上持续记录单 HTML 尺寸、启动峰值内存与查询
P95；达到内存边界时再按第 8 节升级 Page/VFS，不改变 Store 接口。
