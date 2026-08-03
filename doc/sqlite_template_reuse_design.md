# SQLite 模板复用设计

状态：已确认，待实施

目标 schema：v2

决策日期：2026-08-03

## 1. 决策摘要

Address Planner 的 Viewer 数据库采用“逻辑实例树 + 物理模板 DAG”：

1. AddressSpace、RegSpace/Bank 和 Register 的每次逻辑出现仍保留一条轻量实例记录。
2. 实例记录保存父子关系、顺序、实例名和已计算的绝对地址。
3. 节点定义、Register Field Layout 和重复字符串通过内容寻址的模板表复用。
4. Viewer 仍按 `parent_id` 展开节点，不在显示时临场计算绝对地址。
5. 第一版不实现“纯虚拟 Bank”；数据库尺寸和真实复用率证明有必要后再升级。

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
name
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

`node_templates` 保存可共享的节点定义，例如：

```text
content_hash
kind
size_bytes
description
Register width/type/parity/reset-domain
RegSpace bus width/software interface
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

### 3.4 Field Layout

Register Field 不按 Register 实例重复写入。Register occurrence 通过 template 间接引用 Field Layout：

```text
register occurrence
    -> register template
        -> template_fields
            -> field_defs
```

Field 可见语义至少包括：

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

v2 定义为 Viewer 可见语义投影；当前 Viewer 不读取的 `node_attributes` 不再写入报告。如果将来需要完整模型归档，应建立独立格式，不应让未显示属性无限扩张 Viewer 数据库。

## 4. 内容寻址

模板使用带版本域分隔的稳定 SHA-256：

```text
H(
  schema/domain version,
  kind,
  size and visible semantic attributes,
  description,
  ordered(child local name, relative offset, child template hash),
  ordered(field visible semantics)
)
```

编码约束：

- 字符串使用 UTF-8 和明确长度前缀；
- 整数使用固定宽度大端编码；
- 子节点顺序沿用当前 `(bit_offset, original insertion order)`；
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

50 Bank / 10,000 Register / 80,000 Field 合成基准中：

| 方案 | SQLite | gzip |
| --- | ---: | ---: |
| 当前 schema v1 | 12,316,672 B | 1,940,404 B |
| 模板 DAG + 10,051 条轻量 occurrence | 913,408 B | 224,313 B |
| 纯虚拟 Bank 子树 | 61,440 B | 7,119 B |

该基准是高重复理想样例，不作为真实项目体积承诺。

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

## 9. 实施顺序

1. 对真实模型生成只读复用率报告：Field Layout、Node Template、完整子树和字符串。
2. 以 feature flag 新增 schema v2 writer，不原地修改 v1 数据库。
3. Viewer Store 同时支持 v1/v2，保持业务接口不变。
4. 将 v2 完整展开为逻辑树，与旧 JSON/v1 逐 Node、Field 做语义对比。
5. 补充深层树、同地址 MultiPort、单子节差异、64 位地址和 Hash 稳定性测试。
6. 在真实项目上记录原始/gzip/单 HTML 尺寸与启动峰值内存，再切换默认 schema。
