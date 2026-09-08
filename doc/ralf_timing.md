# RALF 地址兼容与 SoC 生成耗时定位

此改动基于 `main@1638f36`。`@'h0x20000`、`@'H0X20000`、
`32'h0x2_0000` 会先归一化为现有 `'h...` 格式；普通 `0xfb4`、
`0xb10`、二进制、十进制以及旧版 `add_ralf(sub_space=...)` 继续支持。
性能优化本身不修改输入 RALF、地址分配、输出模板或默认生成选项。
非性能部分按现场 v3p4 的完整 diff 照片对齐：恢复 `add_ralf()` 的
AddressSpace/RegSpace 对象输入兼容，恢复四个头模板的空格、空白行和文件末尾状态，
包括全局 Verilog 宏名的 60 列对齐。`reg_waiver.j2` 按用户明确要求保留，
它是相对于现场 v3p4 有意增加的功能。照片不能证明不可见字符逐字节一致；
整包兼容性仍需在内网使用同一输入比较生成结果。

## 三档开关

| 档位 | 含义 | 是否增加时间信息 |
|---|---|---|
| 1（默认） | 关闭计时 | 不增加时间日志、进度或汇总，保留原有生成日志 |
| 2 | 粗粒度 | 每个 RALF、import_inst 加载的 PY、整体生成和总脚本耗时 |
| 3 | 细粒度 | 第 2 档再展开内部工序；高频复制/模板操作累计后汇总 |

统一使用 `--timing-level 1/2/3`。没有 CLI 开关时读取
`ADDRESS_PLANNER_TIMING_LEVEL`，都没有设置时入口默认第 1 档。
第 1 档不预先导入 planner，让原脚本保留自己的初始化输出顺序。
`--timing-detail off/coarse/detailed` 仍作为 1/2/3 的兼容别名，不能同时指定两种 CLI 开关。

直接运行原脚本时，也可在首次 import 前设置同一个环境变量：

```sh
env ADDRESS_PLANNER_TIMING_LEVEL=1 python3 ./cmn_reg_addrmap.py
env ADDRESS_PLANNER_TIMING_LEVEL=2 python3 ./cmn_reg_addrmap.py
env ADDRESS_PLANNER_TIMING_LEVEL=3 python3 ./cmn_reg_addrmap.py
```

显式 LEVEL 优先于旧的 `ADDRESS_PLANNER_TIMING` / `ADDRESS_PLANNER_TIMING_DETAIL`。
原脚本直接启动时没有入口的 script.total，若要总脚本统计使用下述入口工具。

## 内网运行（第 2 档示例）

先按现有 module 配好 Python/UHDL。`ADDRESS_PLANNER_ROOT` 指向本次修复后的
工程根目录；`UHDL_ROOT` 必须包含 `uhdl/__init__.py`。
以下入口会使用它所在的 Address Planner，并保留当前工作目录、脚本参数和退出码。

在原来运行 `cmn_reg_addrmap.py` 的工作目录执行，csh/tcsh 示例：

```csh
python3 -u "$ADDRESS_PLANNER_ROOT/tools/profile_addrmap.py" --timing-level 2 ./cmn_reg_addrmap.py >& addrmap_timing.log
echo $status
```

Bash 示例：

```bash
python3 -u "$ADDRESS_PLANNER_ROOT/tools/profile_addrmap.py" --timing-level 2 ./cmn_reg_addrmap.py >addrmap_timing.log 2>&1
echo $?
```

另一个终端观察进度：

```sh
tail -f addrmap_timing.log
```

也可以保持原命令，只在 **首次 import 前** 设置 `ADDRESS_PLANNER_TIMING=1`。
未设置时计时默认关闭；这种方式没有入口的 `script.total` 包围计时。
总脚本计时不包含 Python 启动及入口预先加载 Address Planner 依赖的时间。

计时输出写入 stderr，每条立即 flush，机器可读记录为 `[addr-planner-timing]` 加 JSON。
退出时会额外打印 `[addr-planner-time-summary]` 可读汇总表，标注中文阶段含义，
所有耗时以秒的小数显示。例如 `5.2e-05` 在表中显示为 `0.000052` 秒（52 微秒）。
查看 `total(s)` 了解每个阶段的累计时间；查看按降序排列的 `self(s)` 定位自身热点。
`max(s)` 是该阶段单次调用的最大耗时，`calls` 是调用次数，`errors` 是失败次数。
包含 UTC 时间、PID、阶段、对象/文件、状态、实际耗时 `wall_s`、进程 CPU 时间
`cpu_s`；正常退出或 Python 异常退出时还输出 `summary`。强制杀进程可能没有
结束或汇总记录，但已打印的 `start` 可以帮助判断当时正在执行哪个阶段。

## 第 2 档只看三段过程和总时间

第 2 档 `coarse` 模式不对读取、预处理、Tcl、根选择、对象复制、模板等细工序
读取时钟或登记统计，也不逐寄存器/字段打印。

| 阶段 | 测量范围 |
|---|---|
| `python.file` | `import_inst()` 加载并执行一个 Python 文件，取回指定模型；含其中的下层导入 |
| `add_ralf` | 单个 RALF 从导入到挂接模型的完整过程，记录输入文件名和目标模型 |
| `generate` / `regspace.generate` | 地址图或寄存器产物的完整生成过程；粗模式避免重复记录基类 generate |
| `script.total` | SoC Python 总入口的整体耗时 |

进度行以 `[addr-planner-stage]` 开头，中文说明“开始/完成/失败”、对象、所属 PY、
总耗时、自身耗时。相同 `#编号` 配对开始和结束，`parent` 标记所属上层过程。
例如：`soc.py -> subsystem.py -> ip.py -> ip.ralf` 会保留对应的嵌套关系。
读取和执行 Python 是同一过程；不把执行模块时的建模时间误写成纯文件读取时间。

使用汇总工具可以单独看到每个 PY 的次数、累计耗时和自身耗时。同一个 IP PY
重复导入时会累计次数。PY 的自身时间扣除已计时子过程，仍包含本文件组装、
复制、校验及其他未单独计时的工作，不能等同于纯 Python CPU 时间。

自动逐文件记录覆盖原入口和仓库的 `import_inst()` 路径；普通 Python import、
用户自行写的 exec/importlib 加载器不会被全局跟踪，其时间包含在外层过程。

定位到某一段慢之后再开启详细模式：

```sh
python3 -u "$ADDRESS_PLANNER_ROOT/tools/profile_addrmap.py" --timing-level 3 ./cmn_reg_addrmap.py > detailed.log 2>&1
```

不用入口工具时，在首次 import 前设置 `ADDRESS_PLANNER_TIMING=1` 和
`ADDRESS_PLANNER_TIMING_DETAIL=detailed`；未指定粒度即 coarse。
详细模式才测 RALF 内部、上层挂接、各报告、SQLite/HTML、模板等阶段。

每个阶段的汇总包含调用次数、错误次数、累计耗时、单次最大值。
详细模式下，细粒度拷贝/模板操作只做累计，不逐个寄存器打印，也不保存每个对象的历史。
汇总按 `self_wall_s` 降序排列。`wall_s` 是包含子阶段的时间，**不能把各行相加**；
`self_wall_s` 扣除了已计时子阶段，但仍包括未单独埋点的工作。
CPU 时间来自当前 Python 进程；明显小于实际耗时时，应结合 I/O、调度、网络盘
以及子进程判断，不能仅据此认定为磁盘瓶颈。这是当前串行生成流程的诊断工具。

如果大段时间落在尚未细分的阶段，可对缩小输入启用函数级统计：

```sh
python3 -u "$ADDRESS_PLANNER_ROOT/tools/profile_addrmap.py" --timing-level 3 --profile addrmap.pstats ./cmn_reg_addrmap.py
python3 -c 'import pstats; pstats.Stats("addrmap.pstats").strip_dirs().sort_stats("cumulative").print_stats(40)'
```

`cProfile` 有明显额外开销，不用它的运行时间作为生产性能基线。

## 本次已测出的热点与优化

旧 `build_subspace_recur()` 每处理一个兄弟寄存器，都先 `deepcopy(father)`，
复制此前已构建的整个子树。单个 bank 寄存器增加时，这部分成本接近平方增长。
字段递归也存在同类重复拷贝。

新实现保留公开辅助函数的“复制输入、返回独立对象”契约，在递归内部使用自己
拥有的副本。`AddressSpace.add()`、`RegSpace.add()` 的复制与合法性检查保留。
没有引入跨文件缓存或共享可变寄存器对象。

本机 Python 3.10 合成单 bank、每寄存器一个 32-bit 字段的单次 A/B 结果
（关闭阶段打印和 cProfile；仅测 RALF 导入，非全 SoC 生成）：

| 寄存器数 | 旧构建算法 | 优化后 |
|---:|---:|---:|
| 100 | 0.203 s | 0.039 s |
| 200 | 0.850 s | 0.179 s |
| 400 | 3.242 s | 0.155 s |
| 800 | 14.610 s | 0.324 s |

小样例受 GC/调度波动影响，以上不是多次统计的中位数。
四组地址/字段语义 SHA-256 一致。另用内置 RALF 与嵌套 system/block、memory、
寄存器数组、多字段、重复导入样例，对比旧/新构建算法的 34 个输出文件：
HTML、JSON、RALF、C/Verilog 头文件均逐字节相同。对比的新地址字面量在旧算法
上也应用了相同的归一化，以单独检验构建算法的影响。

复现扩展规模实验：

```sh
python3 "$ADDRESS_PLANNER_ROOT/tools/benchmark_ralf_import.py" --registers 100 200 400 800
```

**尚不能把内网 2–3h → 8h 的回退归因于这个热点，也不能承诺全流程提速倍数。**
需要用同一输入、机器、文件系统和生成选项，记录旧/新 commit、Python/UHDL
版本、RALF 数量与总大小，分别跑出分阶段日志。优先看耗时是在导入还是输出；
若 `template.load`、`report_sqlite` 或文件输出占主导，再针对该阶段优化。

## 模板重复编译优化（2026-09-08 补充）

100 个 bank、每个 8 个寄存器的合成样例中，原实现调用模板加载 502 次，
每次创建新的 Jinja Environment 并重新编译。带 cProfile 的定位运行里，
该阶段占 6.788 / 9.038 秒；这些带 profiler 的数值仅用于定位。

现在使用最多 64 项的进程内字节码缓存。仍为每次渲染创建独立环境，避免
head_type 等变量串到下一次渲染；每次读取源文件并由 Jinja 校验内容摘要，
源码修改会触发重新编译，不依赖 mtime。不缓存模型、渲染结果，不写磁盘缓存。

关闭计时和 cProfile、顺序进行三轮开关 A/B（包含同一脚本的导入、模型构建和
生成，均开启 JSON，生成 HTML/RALF/C/Verilog 等 308 个文件）：

| 缓存 | 三轮耗时（秒） | 中位数 |
|---|---|---|
| 关闭 | 4.262 / 3.957 / 3.717 | 3.957 |
| 开启 | 1.281 / 1.208 / 1.198 | 1.208 |

三轮每轮的 308 个文件均逐字节一致。此样例约 3.28 倍提速，不能作为真实 SoC
的收益承诺。缓存开关在 import 时读取，独立隔离此项优化时可运行：

```sh
env ADDRESS_PLANNER_TEMPLATE_CACHE=0 python3 your_map.py
env ADDRESS_PLANNER_TEMPLATE_CACHE=1 python3 your_map.py
```

两次使用独立输出目录，否则会覆盖对比结果。此开关不关闭 RALF 构建优化。

## 从日志提取热点

```sh
python3 "$ADDRESS_PLANNER_ROOT/tools/summarize_addrmap_timing.py" addrmap_timing.log --top 20
python3 "$ADDRESS_PLANNER_ROOT/tools/summarize_addrmap_timing.py" addrmap_timing.log --json > timing-summary.json
```

工具按 self 耗时排序，列出最慢的已完成操作和没有 end 的阶段。可用于尚未
完成或异常截断的日志；没有汇总时会明确说明，不把部分耗时当成全程耗时。
不要将包含子调用的 wall 时间相加。长日志按行读取，不保留所有对象事件。

## 导入内网后与 v3p4 对比

本包用于独立目录试用；现有 v3p4 保留，比较通过后再决定使用。
本包不包含 UHDL、内网 RALF 或 Python 第三方依赖，沿用现场同一套环境。

1. 记录两边源码版本/目录、Python/UHDL 版本及命令。固定同一输入、生成选项、
   机器和存储位置；分别使用独立输出目录，检查脚本内是否还有绝对输出路径。
2. v3p4 按原命令运行，测试版用上面的 profile_addrmap.py 包围原入口。
   全程性能比较使用两边相同的 `/usr/bin/time -v` 外层测量，均关闭 cProfile；
   它包含 Python 启动时间，并提供最大 RSS。先不要同时跑两边以免互相争抢资源。
3. 确认两边正常退出、生成选项一致，再逐文件比较。示例：

```sh
diff -qr /path/to/v3p4_output /path/to/test_output > output-diff.log
```

   退出 0 表示目录相同；1 表示有差异；大于 1 表示比较失败。不要忽略 `.h`、
   `.vh`、RALF、CSV 或 waiver 的空格/顺序差异。新增、缺失文件也需检查。
   HTML/SQLite 若不同，需要检查数据和页面行为，不能只看文件大小认定等价。
4. 保留两边完整生成日志、time 输出、output-diff.log 和测试版 timing-summary.json。
   真实 SoC 的耗时瓶颈和输出兼容性以这次内网结果为准。

Bash 的完整测试版调用示例（在原生成入口的工作目录执行）：

```bash
export ADDRESS_PLANNER_ROOT=/path/to/address_planner_performance_trial
# UHDL_ROOT 使用与现场 v3p4 相同的设置
/usr/bin/time -v python3 -u "$ADDRESS_PLANNER_ROOT/tools/profile_addrmap.py" --timing-level 2 \
    ./cmn_reg_addrmap.py > addrmap_timing.log 2>&1
rc=$?
echo "exit_code=$rc"
python3 "$ADDRESS_PLANNER_ROOT/tools/summarize_addrmap_timing.py" addrmap_timing.log --top 20
```

本地验证：86 项 case 通过，包含对象输入的两种类型和两种参数名；
缓存源码变更检测、跨调用变量隔离和容量限制通过；
原重构的两项 selftest 对 reserved 命名/SV 位序的要求仍与恢复的内网格式冲突，
未宣称全量 selftest 通过，也未验证内网 SpyGlass waiver 的实际告警匹配。

## 记录时间本身的开销

同一 `soc.py -> subsystem.py -> ip.py -> ip.ralf` 输入，共 16 个 IP、2048 个寄存器。
关闭、粗粒度、详细三种模式各执行 5 次，轮换顺序，未开 cProfile，日志写入本机
/home 文件系统。15 次运行中，每次 28 个生成文件均逐字节一致。

| 模式 | 进程总耗时中位数 | 生成过程中位数 | 完整日志大小中位数 | 计时记录数 |
|---|---:|---:|---:|---:|
| 关闭计时 | 2.244 s | 1.849 s | 29,004 B | 0 |
| 粗粒度（第 2 档） | 2.268 s | 1.888 s | 87,037 B | 75 |
| 详细模式 | 2.366 s | 1.966 s | 368,729 B | 504 |

粗粒度的进程总耗时中位数增加约 1.1%，生成过程增加约 2.1%；详细模式分别
增加约 5.4% / 6.3%。短样例存在调度、GC、文件系统缓存波动，不作为固定开销保证。
每次日志末尾额外记录 write+flush 的累计耗时；本例粗粒度中位数 0.004759 秒、
145 次写入，详细模式 0.026103 秒、978 次写入。该计数截至统计行之前，
不包含格式化和计时记账；评估总开销使用上述关闭/开启计时的完整 A/B 结果。
完整日志大小包含生成器原本已有的输出，不能全部算作新增计时日志。

这些是本地磁盘结果，不代表内网网络盘表现。应保留现场生成日志末尾的
logging_overhead；需要定量测量时，在同一输入、机器和输出存储位置分别关闭/
开启粗计时，顺序运行并比较外层 time -v，不同时运行两份任务。

## 原先 8 小时能降到多久

尚无真实 SoC 阶段占比，不能直接用合成样例倍数除以 8 小时。
条件估算为 `新耗时 = 8h × [(1 - p) + p / s]`，其中 p 是旧运行中受此次优化
影响的耗时比例，s 是这些部分在实际输入上的加速倍数；此公式暂不计日志开销。
例如假设 s=3：p=50% 时约 5 小时 20 分，p=80% 时约 3 小时 44 分。
这两项是条件推算，不是实测预测。若主要耗时在未优化的 I/O、RTL/外部工具等，
全程可能仍接近 8 小时。先用粗粒度（第 2 档）确定 RALF 导入、PY 集成还是最终生成
占主导，再只对那个瓶颈进行细化和估计。
