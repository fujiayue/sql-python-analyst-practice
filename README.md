# SQL/Python 数据分析师一周自测题库

这是一个面向数据分析师/运营 BI 机考准备的本地自测题库，用 7 天训练营的方式快速恢复 SQL、Python/pandas、数据质量排查和业务结论表达能力。

项目完全离线运行：内置共享中心工单模拟数据，SQL 使用 DuckDB 执行，Python 题通过 `solve(...)` 自动评分。适合在一周内集中练习“读题、查数、写代码、看反馈、复盘错题”的上机能力。

## 日常启动

平时只需要双击：

```text
start-trainer.cmd
```

它会自动启动后端、前端，并打开浏览器到：

```text
http://127.0.0.1:5173
```

如果是第一次运行，它会自动安装本地依赖，可能需要几分钟。

如果想在桌面生成带自定义图标的快捷方式：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\create-desktop-shortcut.ps1
```

> 说明：仓库里也有 `scripts/build-launcher.ps1` 可以构建 exe 启动器，但当前机器的 Windows 应用控制策略会拦截本地生成的未签名 exe。所以默认使用 `start-trainer.cmd`，双击体验更稳定。

## 功能

- 7 天训练路径：首页展示每日主题、任务数、完成率和错题数。
- 152 道训练题：覆盖 SQL 基础、SQL 进阶、pandas、运营效率案例、数据质量排查和限时模拟。
- 题库页区分未开始、已通过、待复盘题目，并支持按状态筛选。
- SQL 练习：DuckDB 本地执行，自动比较列名、行数、排序和数值结果。
- Python/pandas 练习：提交 `solve(...)`，后端用独立临时进程限时执行。
- 错题本：失败提交自动记录，题目通过后回填最终通过版本。
- 业务结论：离线规则检查是否写出发现、原因假设、建议动作和关键指标。

## 训练内容

- Day 1：SQL 基础聚合与条件统计。
- Day 2：JOIN、CTE、窗口函数、排名、环比和累计。
- Day 3：Python/pandas 清洗、汇总和数据质量检查。
- Day 4：pandas 分析、透视、排序、Top N、滚动窗口和环比。
- Day 5：共享中心运营效率综合案例。
- Day 6：脏数据、异常值、枚举值、日期和连接后行数校验。
- Day 7：限时模拟，练习从指标计算到业务建议输出。

## 开发命令

第一次安装依赖：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

启动后端：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
```

另开一个终端启动前端：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```

运行后端测试：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test-backend.ps1
```

如果 PowerShell 拦截 `npm.ps1`，脚本内部会使用 `cmd /c npm ...`。
