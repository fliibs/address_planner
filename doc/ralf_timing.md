# RALF 地址兼容与 SoC 生成耗时定位

此改动基于 `main@1638f36`。`@'h0x20000`、`@'H0X20000`、
`32'h0x2_0000` 会先归一化为现有 `'h...` 格式；普通 `0xfb4`、
`0xb10`、二进制、十进制以及旧版 `add_ralf(sub_space=...)` 继续支持。
不修改输入 RALF、地址分配、输出模板或默认生成选项。

## 内网运行

先按现有 module 配好 Python/UHDL。`ADDRESS_PLANNER_ROOT` 指向本次修复后的
工程根目录；`UHDL_ROOT` 必须包含 `uhdl/__init__.py`。
以下入口会使用它所在的 Address Planner，并保留当前工作目录、脚本参数和退出码。

在原来运行 `cmn_reg_addrmap.py` 的工作目录执行，csh/tcsh 示例：

```csh
python3 -u "$ADDRESS_PLANNER_ROOT/tools/profile_addrmap.py" ./cmn_reg_addrmap.py >& addrmap_timing.log
echo $status
```

Bash 示例：

```bash
python3 -u "$ADDRESS_PLANNER_ROOT/tools/profile_addrmap.py" ./cmn_reg_addrmap.py >addrmap_timing.log 2>&1
echo $?
```

另一个终端观察进度：

```sh
tail -f addrmap_timing.log
```

也可以保持原命令，只在 **首次 import 前** 设置 `ADDRESS_PLANNER_TIMING=1`。
未设置时计时默认关闭；这种方式没有入口的 `script.total` 包围计时。
总脚本计时不包含 Python 启动及入口预先加载 Address Planner 依赖的时间。

计时输出写入 stderr，每条立即 flush，格式为 `[addr-planner-timing]` 加 JSON。
包含 UTC 时间、PID、阶段、对象/文件、状态、实际耗时 `wall_s`、进程 CPU 时间
`cpu_s`；正常退出或 Python 异常退出时还输出 `summary`。强制杀进程可能没有
结束或汇总记录，但已打印的 `start` 可以帮助判断当时正在执行哪个阶段。

## 看哪些阶段

| 阶段 | 测量范围 |
|---|---|
| `script.total` | 原始 Python 脚本整体，包括模型构建和输出 |
| `add_ralf` / `ralf.read` / `ralf.preprocess` | 每次导入、文件读取、文本预处理 |
| `ralf.tcl_eval` | Tcl 执行 RALF 定义 |
| `ralf.select_root` / `ralf.tcl_to_python` | 根定义选择、Tcl 字典转 Python |
| `ralf.build_objects` / `ralf.deepcopy` | 地址树构建、其中的拷贝 |
| `ralf.attach` / `address.add.deepcopy` / `register.add.deepcopy` | 挂接对象及复制 |
| `generate` / `report_sqlite` / `html.package` | 总输出、SQLite 报告、压缩与 HTML 打包 |
| `json.build` / `json.write` / `docx.build` | 启用 JSON/Word 时的独立耗时 |
| `report_ralf` / `report_chead` / `report_vhead` | RALF、C 头、Verilog 头输出 |
| `template.load` / `template.render` | 模板加载编译、渲染累计成本 |

每个阶段的汇总包含调用次数、错误次数、累计耗时、单次最大值。
细粒度拷贝/模板操作只做累计，不逐个寄存器打印，也不保存每个对象的历史。
汇总按 `self_wall_s` 降序排列。`wall_s` 是包含子阶段的时间，**不能把各行相加**；
`self_wall_s` 扣除了已计时子阶段，但仍包括未单独埋点的工作。
CPU 时间来自当前 Python 进程；明显小于实际耗时时，应结合 I/O、调度、网络盘
以及子进程判断，不能仅据此认定为磁盘瓶颈。这是当前串行生成流程的诊断工具。

如果大段时间落在尚未细分的阶段，可对缩小输入启用函数级统计：

```sh
python3 -u "$ADDRESS_PLANNER_ROOT/tools/profile_addrmap.py" --profile addrmap.pstats ./cmn_reg_addrmap.py
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
