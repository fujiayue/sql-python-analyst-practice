from dataclasses import asdict, dataclass
import textwrap


@dataclass(frozen=True)
class TaskSpec:
    id: str
    day: int
    title: str
    mode: str
    objective: str
    prompt: str
    datasets: tuple[str, ...]
    solution: str
    starter_code: str = ""
    sort_by: tuple[str, ...] = ()
    mysql_tip: str = ""
    timebox_minutes: int = 20
    tier: str = "core"
    difficulty: str = "基础"
    tags: tuple[str, ...] = ()

    def public_dict(self) -> dict[str, object]:
        data = asdict(self)
        is_generated = "_gen_" in self.id
        if is_generated and self.tier == "core":
            data["tier"] = "drill"
        data["datasets"] = list(self.datasets)
        data["sort_by"] = list(self.sort_by)
        data["tags"] = list(self.tags)
        data["is_generated"] = is_generated
        return data


DAY_META = {
    1: {"title": "SQL 基础恢复", "focus": "SELECT、WHERE、GROUP BY、HAVING、CASE WHEN、COUNT DISTINCT"},
    2: {"title": "SQL 进阶", "focus": "JOIN、CTE、窗口函数、环比、累计值、排名"},
    3: {"title": "pandas 基础恢复", "focus": "读取、检查、清洗、日期、groupby、agg"},
    4: {"title": "pandas 分析与可视化", "focus": "merge、pivot、Top N、pct_change、rolling"},
    5: {"title": "共享中心运营效率案例", "focus": "SLA、返工率、积压量、人效、业务建议"},
    6: {"title": "数据质量与异常诊断", "focus": "空值、重复、日期异常、枚举异常、连接校验"},
    7: {"title": "限时模拟", "focus": "读题、查数、算指标、拆解原因、写结论"},
}


def sql_task(
    task_id: str,
    day: int,
    title: str,
    objective: str,
    prompt: str,
    solution: str,
    sort_by: tuple[str, ...] = (),
    datasets: tuple[str, ...] = ("tickets",),
    mysql_tip: str = "",
    timebox_minutes: int = 15,
    tier: str = "core",
    difficulty: str = "基础",
    tags: tuple[str, ...] = (),
) -> TaskSpec:
    return TaskSpec(
        id=task_id,
        day=day,
        title=title,
        mode="sql",
        objective=objective,
        prompt=prompt,
        datasets=datasets,
        solution=textwrap.dedent(solution).strip(),
        sort_by=sort_by,
        mysql_tip=mysql_tip,
        timebox_minutes=timebox_minutes,
        tier=tier,
        difficulty=difficulty,
        tags=tags,
    )


def python_task(
    task_id: str,
    day: int,
    title: str,
    objective: str,
    prompt: str,
    solution: str,
    starter_code: str,
    sort_by: tuple[str, ...] = (),
    datasets: tuple[str, ...] = ("tickets",),
    timebox_minutes: int = 25,
    tier: str = "core",
    difficulty: str = "基础",
    tags: tuple[str, ...] = (),
) -> TaskSpec:
    return TaskSpec(
        id=task_id,
        day=day,
        title=title,
        mode="python",
        objective=objective,
        prompt=prompt,
        datasets=datasets,
        solution=textwrap.dedent(solution).strip(),
        starter_code=textwrap.dedent(starter_code).strip(),
        sort_by=sort_by,
        timebox_minutes=timebox_minutes,
        tier=tier,
        difficulty=difficulty,
        tags=tags,
    )


SQL_STARTER = "-- 在这里写 SQL。表名见下方数据预览。\nSELECT *\nFROM tickets\nLIMIT 5;"

PY_STARTER = """import pandas as pd


def solve(df: pd.DataFrame) -> pd.DataFrame:
    # 返回一个 pandas DataFrame
    return df.head()
"""

PY_TWO_TABLE_STARTER = """import pandas as pd


def solve(df: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
    # 第二个参数是题目说明里的维表
    return df.head()
"""


TASKS: list[TaskSpec] = [
    sql_task(
        "d1_sql_01_team_volume",
        1,
        "按团队统计工单量",
        "恢复 GROUP BY 手感。",
        "按 team 统计全部工单量，输出 team、ticket_cnt，按 team 升序。",
        """
        SELECT team, COUNT(*) AS ticket_cnt
        FROM tickets
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d1_sql_02_month_volume",
        1,
        "按月统计工单量",
        "练习日期截取和月度聚合。",
        "按 create_time 所在月份统计工单量，输出 month、ticket_cnt，month 格式为 YYYY-MM。",
        """
        SELECT strftime(create_time, '%Y-%m') AS month, COUNT(*) AS ticket_cnt
        FROM tickets
        GROUP BY month
        ORDER BY month
        """,
        ("month",),
        mysql_tip="MySQL 可用 DATE_FORMAT(create_time, '%Y-%m')。",
    ),
    sql_task(
        "d1_sql_03_team_sla",
        1,
        "团队 SLA 达成率",
        "练习条件聚合。",
        "只看 Closed 工单，按 team 计算 sla_rate=process_hours<=sla_hours 的比例，保留 4 位小数。",
        """
        SELECT
            team,
            ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
        FROM tickets
        WHERE status = 'Closed'
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d1_sql_04_type_avg_hours",
        1,
        "任务类型平均处理时长",
        "练习 AVG 和排序。",
        "只看 Closed 工单，按 task_type 计算平均处理小时数，输出 task_type、avg_process_hours，保留 2 位小数。",
        """
        SELECT task_type, ROUND(AVG(process_hours), 2) AS avg_process_hours
        FROM tickets
        WHERE status = 'Closed'
        GROUP BY task_type
        ORDER BY task_type
        """,
        ("task_type",),
    ),
    sql_task(
        "d1_sql_05_team_rework",
        1,
        "团队返工率",
        "练习布尔字段聚合。",
        "按 team 计算返工率 rework_rate，is_rework 为 true 记为返工，保留 4 位小数。",
        """
        SELECT team, ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4) AS rework_rate
        FROM tickets
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d1_sql_06_team_backlog",
        1,
        "团队积压量",
        "练习状态筛选。",
        "按 team 统计 status='Backlog' 的工单数，输出 team、backlog_cnt。",
        """
        SELECT team, COUNT(*) AS backlog_cnt
        FROM tickets
        WHERE status = 'Backlog'
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d1_sql_07_month_high_priority",
        1,
        "高优先级月度数量",
        "练习 CASE WHEN 计数。",
        "按月统计高优先级工单数，输出 month、high_priority_cnt。",
        """
        SELECT
            strftime(create_time, '%Y-%m') AS month,
            SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) AS high_priority_cnt
        FROM tickets
        GROUP BY month
        ORDER BY month
        """,
        ("month",),
        mysql_tip="MySQL 可用 DATE_FORMAT(create_time, '%Y-%m')。",
    ),
    sql_task(
        "d1_sql_08_priority_avg_hours",
        1,
        "优先级平均处理时长",
        "练习分组均值。",
        "只看 Closed 工单，按 priority 计算平均处理小时数，输出 priority、avg_process_hours，保留 2 位小数。",
        """
        SELECT priority, ROUND(AVG(process_hours), 2) AS avg_process_hours
        FROM tickets
        WHERE status = 'Closed'
        GROUP BY priority
        ORDER BY priority
        """,
        ("priority",),
    ),
    sql_task(
        "d1_sql_09_distinct_assignee",
        1,
        "团队处理人数",
        "练习 COUNT DISTINCT。",
        "按 team 统计不同 assignee 数量，输出 team、assignee_cnt。",
        """
        SELECT team, COUNT(DISTINCT assignee) AS assignee_cnt
        FROM tickets
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d1_sql_10_type_share",
        1,
        "任务类型占比",
        "练习占比计算。",
        "按 task_type 统计工单量和整体占比 share，share 保留 4 位小数。",
        """
        SELECT
            task_type,
            COUNT(*) AS ticket_cnt,
            ROUND(COUNT(*) * 1.0 / (SELECT COUNT(*) FROM tickets), 4) AS share
        FROM tickets
        GROUP BY task_type
        ORDER BY task_type
        """,
        ("task_type",),
    ),
    sql_task(
        "d1_sql_11_month_sla",
        1,
        "月度 SLA 达成率",
        "练习月度条件聚合。",
        "只看 Closed 工单，按月计算 SLA 达成率 sla_rate，保留 4 位小数。",
        """
        SELECT
            strftime(create_time, '%Y-%m') AS month,
            ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
        FROM tickets
        WHERE status = 'Closed'
        GROUP BY month
        ORDER BY month
        """,
        ("month",),
    ),
    sql_task(
        "d1_sql_12_low_sla_teams",
        1,
        "找出低 SLA 团队",
        "练习 HAVING。",
        "只看 Closed 工单，找出 SLA 达成率低于 0.70 的团队，输出 team、sla_rate。",
        """
        SELECT
            team,
            ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
        FROM tickets
        WHERE status = 'Closed'
        GROUP BY team
        HAVING AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END) < 0.70
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d1_sql_13_slow_by_team",
        1,
        "超长处理工单",
        "练习条件计数。",
        "按 team 统计 process_hours > 72 的工单数，输出 team、slow_ticket_cnt。",
        """
        SELECT
            team,
            SUM(CASE WHEN process_hours > 72 THEN 1 ELSE 0 END) AS slow_ticket_cnt
        FROM tickets
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d1_sql_14_month_team_avg",
        1,
        "月度团队平均时长",
        "练习多字段分组。",
        "只看 Closed 工单，按 month 和 team 计算平均处理小时数，保留 2 位小数。",
        """
        SELECT
            strftime(create_time, '%Y-%m') AS month,
            team,
            ROUND(AVG(process_hours), 2) AS avg_process_hours
        FROM tickets
        WHERE status = 'Closed'
        GROUP BY month, team
        ORDER BY month, team
        """,
        ("month", "team"),
    ),
    sql_task(
        "d1_sql_15_rework_high",
        1,
        "高优先级返工数",
        "练习复合条件。",
        "按 team 统计同时满足 priority='High' 且 is_rework=true 的工单数。",
        """
        SELECT
            team,
            SUM(CASE WHEN priority = 'High' AND is_rework THEN 1 ELSE 0 END) AS rework_high_cnt
        FROM tickets
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d1_sql_16_top_task_types",
        1,
        "Top 3 任务类型",
        "练习排序和 LIMIT。",
        "按工单量找出 Top 3 task_type，输出 task_type、ticket_cnt，按 ticket_cnt 降序、task_type 升序。",
        """
        SELECT task_type, COUNT(*) AS ticket_cnt
        FROM tickets
        GROUP BY task_type
        ORDER BY ticket_cnt DESC, task_type
        LIMIT 3
        """,
        ("ticket_cnt", "task_type"),
    ),
    sql_task(
        "d1_sql_17_close_month",
        1,
        "月度关闭量",
        "练习 close_time 口径。",
        "只看 Closed 工单，按 close_time 所在月份统计关闭量，输出 close_month、closed_cnt。",
        """
        SELECT strftime(close_time, '%Y-%m') AS close_month, COUNT(*) AS closed_cnt
        FROM tickets
        WHERE status = 'Closed'
        GROUP BY close_month
        ORDER BY close_month
        """,
        ("close_month",),
    ),
    sql_task(
        "d1_sql_18_open_by_priority",
        1,
        "未关闭工单优先级结构",
        "练习状态和优先级拆解。",
        "统计 status in ('Open','Backlog') 的工单，按 priority 输出 open_cnt。",
        """
        SELECT priority, COUNT(*) AS open_cnt
        FROM tickets
        WHERE status IN ('Open', 'Backlog')
        GROUP BY priority
        ORDER BY priority
        """,
        ("priority",),
    ),
    sql_task(
        "d1_sql_19_sla_failed_type",
        1,
        "SLA 失败任务类型",
        "练习条件筛选。",
        "只看 Closed 工单，按 task_type 统计 SLA 失败数量，输出 task_type、sla_failed_cnt。",
        """
        SELECT task_type, COUNT(*) AS sla_failed_cnt
        FROM tickets
        WHERE status = 'Closed' AND process_hours > sla_hours
        GROUP BY task_type
        ORDER BY task_type
        """,
        ("task_type",),
    ),
    sql_task(
        "d1_sql_20_team_productivity",
        1,
        "团队人均关闭量",
        "练习人效指标。",
        "按 team 计算 Closed 工单数除以不同 assignee 数，输出 team、tickets_per_assignee，保留 2 位小数。",
        """
        SELECT
            team,
            ROUND(
                SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) * 1.0 / COUNT(DISTINCT assignee),
                2
            ) AS tickets_per_assignee
        FROM tickets
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d2_sql_01_below_overall_sla",
        2,
        "低于整体 SLA 的团队",
        "练习 CTE 和整体基准。",
        "用 CTE 计算每个团队 SLA 达成率，并筛出低于整体 SLA 的团队。",
        """
        WITH team_sla AS (
            SELECT team, AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END) AS sla_rate
            FROM tickets
            WHERE status = 'Closed'
            GROUP BY team
        ),
        overall AS (
            SELECT AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END) AS overall_sla
            FROM tickets
            WHERE status = 'Closed'
        )
        SELECT team, ROUND(sla_rate, 4) AS sla_rate
        FROM team_sla, overall
        WHERE sla_rate < overall_sla
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d2_sql_02_top_type_each_team",
        2,
        "每团队最慢任务类型",
        "练习 ROW_NUMBER。",
        "只看 Closed 工单，找出每个团队平均处理时长最高的 task_type。",
        """
        WITH ranked AS (
            SELECT
                team,
                task_type,
                ROUND(AVG(process_hours), 2) AS avg_process_hours,
                ROW_NUMBER() OVER (PARTITION BY team ORDER BY AVG(process_hours) DESC, task_type) AS rn
            FROM tickets
            WHERE status = 'Closed'
            GROUP BY team, task_type
        )
        SELECT team, task_type, avg_process_hours
        FROM ranked
        WHERE rn = 1
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d2_sql_03_team_sla_rank",
        2,
        "团队 SLA 排名",
        "练习 RANK。",
        "只看 Closed 工单，计算团队 SLA 达成率并按达成率从高到低排名。",
        """
        WITH team_sla AS (
            SELECT
                team,
                ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
            FROM tickets
            WHERE status = 'Closed'
            GROUP BY team
        )
        SELECT
            team,
            sla_rate,
            RANK() OVER (ORDER BY sla_rate DESC, team) AS sla_rank
        FROM team_sla
        ORDER BY sla_rank, team
        """,
        ("sla_rank", "team"),
    ),
    sql_task(
        "d2_sql_04_month_mom",
        2,
        "月度工单环比",
        "练习 LAG。",
        "按月统计工单量，并计算相比上月的 mom_change。",
        """
        WITH monthly AS (
            SELECT strftime(create_time, '%Y-%m') AS month, COUNT(*) AS ticket_cnt
            FROM tickets
            GROUP BY month
        )
        SELECT
            month,
            ticket_cnt,
            ticket_cnt - LAG(ticket_cnt) OVER (ORDER BY month) AS mom_change
        FROM monthly
        ORDER BY month
        """,
        ("month",),
    ),
    sql_task(
        "d2_sql_05_cumulative_volume",
        2,
        "累计工单量",
        "练习 SUM OVER。",
        "按月统计工单量，并输出累计工单量 cumulative_ticket_cnt。",
        """
        WITH monthly AS (
            SELECT strftime(create_time, '%Y-%m') AS month, COUNT(*) AS ticket_cnt
            FROM tickets
            GROUP BY month
        )
        SELECT
            month,
            ticket_cnt,
            SUM(ticket_cnt) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_ticket_cnt
        FROM monthly
        ORDER BY month
        """,
        ("month",),
    ),
    sql_task(
        "d2_sql_06_join_complexity",
        2,
        "团队平均复杂度",
        "练习 JOIN 维表。",
        "连接 task_dim，按 team 计算平均 complexity，输出 team、avg_complexity，保留 2 位小数。",
        """
        SELECT
            t.team,
            ROUND(AVG(d.complexity), 2) AS avg_complexity
        FROM tickets t
        JOIN task_dim d ON t.task_type = d.task_type
        GROUP BY t.team
        ORDER BY t.team
        """,
        ("team",),
        ("tickets", "task_dim"),
    ),
    sql_task(
        "d2_sql_07_level_workload",
        2,
        "人员级别关闭量",
        "练习 JOIN 后聚合。",
        "连接 assignee_dim，只看 Closed 工单，按 level 统计关闭量 closed_cnt。",
        """
        SELECT a.level, COUNT(*) AS closed_cnt
        FROM tickets t
        JOIN assignee_dim a ON t.assignee = a.assignee
        WHERE t.status = 'Closed'
        GROUP BY a.level
        ORDER BY a.level
        """,
        ("level",),
        ("tickets", "assignee_dim"),
    ),
    sql_task(
        "d2_sql_08_running_sla",
        2,
        "月度 SLA 三期移动平均",
        "练习窗口平均。",
        "只看 Closed 工单，先算月度 SLA，再输出 3 个月移动平均 running_sla_3m，保留 4 位小数。",
        """
        WITH monthly AS (
            SELECT
                strftime(create_time, '%Y-%m') AS month,
                AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END) AS sla_rate
            FROM tickets
            WHERE status = 'Closed'
            GROUP BY month
        )
        SELECT
            month,
            ROUND(sla_rate, 4) AS sla_rate,
            ROUND(AVG(sla_rate) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 4) AS running_sla_3m
        FROM monthly
        ORDER BY month
        """,
        ("month",),
    ),
    sql_task(
        "d2_sql_09_top_assignees",
        2,
        "每团队 Top 3 处理人",
        "练习分区 Top N。",
        "只看 Closed 工单，找出每个团队关闭量 Top 3 的 assignee。",
        """
        WITH ranked AS (
            SELECT
                team,
                assignee,
                COUNT(*) AS closed_cnt,
                ROW_NUMBER() OVER (PARTITION BY team ORDER BY COUNT(*) DESC, assignee) AS rn
            FROM tickets
            WHERE status = 'Closed'
            GROUP BY team, assignee
        )
        SELECT team, assignee, closed_cnt
        FROM ranked
        WHERE rn <= 3
        ORDER BY team, closed_cnt DESC, assignee
        """,
        ("team", "closed_cnt", "assignee"),
    ),
    sql_task(
        "d2_sql_10_month_end_share",
        2,
        "月结任务占比",
        "练习 CTE 和占比。",
        "按月计算 Month-end Close 工单占比 month_end_share，保留 4 位小数。",
        """
        WITH monthly AS (
            SELECT
                strftime(create_time, '%Y-%m') AS month,
                COUNT(*) AS ticket_cnt,
                SUM(CASE WHEN task_type = 'Month-end Close' THEN 1 ELSE 0 END) AS month_end_cnt
            FROM tickets
            GROUP BY month
        )
        SELECT month, ROUND(month_end_cnt * 1.0 / ticket_cnt, 4) AS month_end_share
        FROM monthly
        ORDER BY month
        """,
        ("month",),
    ),
    sql_task(
        "d2_sql_11_next_month_sla",
        2,
        "下月 SLA 对比",
        "练习 LEAD。",
        "只看 Closed 工单，按月计算 sla_rate，并输出 next_month_sla。",
        """
        WITH monthly AS (
            SELECT
                strftime(create_time, '%Y-%m') AS month,
                ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
            FROM tickets
            WHERE status = 'Closed'
            GROUP BY month
        )
        SELECT
            month,
            sla_rate,
            LEAD(sla_rate) OVER (ORDER BY month) AS next_month_sla
        FROM monthly
        ORDER BY month
        """,
        ("month",),
    ),
    sql_task(
        "d2_sql_12_rework_rank",
        2,
        "任务类型返工率排名",
        "练习窗口排名。",
        "按 task_type 计算返工率，并用 RANK 按返工率从高到低排名。",
        """
        WITH type_rework AS (
            SELECT
                task_type,
                ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4) AS rework_rate
            FROM tickets
            GROUP BY task_type
        )
        SELECT
            task_type,
            rework_rate,
            RANK() OVER (ORDER BY rework_rate DESC, task_type) AS rework_rank
        FROM type_rework
        ORDER BY rework_rank, task_type
        """,
        ("rework_rank", "task_type"),
    ),
    sql_task(
        "d2_sql_13_high_priority_share",
        2,
        "团队高优先级占比",
        "练习分组占比。",
        "按 team 计算高优先级工单占比 high_priority_share，保留 4 位小数。",
        """
        SELECT
            team,
            ROUND(AVG(CASE WHEN priority = 'High' THEN 1.0 ELSE 0.0 END), 4) AS high_priority_share
        FROM tickets
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
    ),
    sql_task(
        "d2_sql_14_ticket_vs_team_avg",
        2,
        "工单时长偏离团队均值",
        "练习明细窗口均值。",
        "只看 Closed 工单，输出处理时长高于团队平均 30 小时以上的前 20 条工单。",
        """
        WITH scored AS (
            SELECT
                ticket_id,
                team,
                process_hours,
                ROUND(AVG(process_hours) OVER (PARTITION BY team), 2) AS team_avg_hours
            FROM tickets
            WHERE status = 'Closed'
        )
        SELECT
            ticket_id,
            team,
            process_hours,
            team_avg_hours,
            ROUND(process_hours - team_avg_hours, 2) AS diff_hours
        FROM scored
        WHERE process_hours - team_avg_hours > 30
        ORDER BY diff_hours DESC, ticket_id
        LIMIT 20
        """,
        ("diff_hours", "ticket_id"),
    ),
    sql_task(
        "d2_sql_15_category_sla",
        2,
        "任务类别 SLA",
        "练习 JOIN 后条件聚合。",
        "连接 task_dim，只看 Closed 工单，按 category 计算 SLA 达成率。",
        """
        SELECT
            d.category,
            ROUND(AVG(CASE WHEN t.process_hours <= t.sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
        FROM tickets t
        JOIN task_dim d ON t.task_type = d.task_type
        WHERE t.status = 'Closed'
        GROUP BY d.category
        ORDER BY d.category
        """,
        ("category",),
        ("tickets", "task_dim"),
    ),
    python_task(
        "d3_py_01_monthly_metrics",
        3,
        "pandas 月度指标",
        "恢复 groupby、agg、日期处理。",
        "实现 solve(df)，返回 month、ticket_cnt、avg_process_hours、sla_rate。只统计 Closed 工单，month 为 YYYY-MM，数值分别保留 2/4 位。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            data = df.copy()
            data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
            closed = data[data["status"] == "Closed"].copy()
            closed["month"] = closed["create_time"].dt.strftime("%Y-%m")
            out = (
                closed.groupby("month")
                .agg(
                    ticket_cnt=("ticket_id", "count"),
                    avg_process_hours=("process_hours", "mean"),
                    sla_rate=("process_hours", lambda s: (s <= closed.loc[s.index, "sla_hours"]).mean()),
                )
                .reset_index()
            )
            out["avg_process_hours"] = out["avg_process_hours"].round(2)
            out["sla_rate"] = out["sla_rate"].round(4)
            return out.sort_values("month").reset_index(drop=True)
        """,
        PY_STARTER,
        ("month",),
    ),
    python_task(
        "d3_py_02_team_metrics",
        3,
        "团队运营指标",
        "练习 groupby 多指标。",
        "实现 solve(df)，按 team 返回 ticket_cnt、closed_cnt、avg_process_hours、rework_rate，数值保留 2/4 位。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            data = df.copy()
            data["closed_flag"] = data["status"].eq("Closed")
            out = (
                data.groupby("team")
                .agg(
                    ticket_cnt=("ticket_id", "count"),
                    closed_cnt=("closed_flag", "sum"),
                    avg_process_hours=("process_hours", "mean"),
                    rework_rate=("is_rework", "mean"),
                )
                .reset_index()
            )
            out["avg_process_hours"] = out["avg_process_hours"].round(2)
            out["rework_rate"] = out["rework_rate"].round(4)
            return out.sort_values("team").reset_index(drop=True)
        """,
        PY_STARTER,
        ("team",),
    ),
    python_task(
        "d3_py_03_status_pivot",
        3,
        "状态透视表",
        "练习 pivot_table。",
        "实现 solve(df)，返回 team、Backlog、Closed、Open 四列，统计每队不同状态工单量，缺失填 0。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            out = (
                pd.pivot_table(df, index="team", columns="status", values="ticket_id", aggfunc="count", fill_value=0)
                .reset_index()
            )
            for col in ["Backlog", "Closed", "Open"]:
                if col not in out.columns:
                    out[col] = 0
            return out[["team", "Backlog", "Closed", "Open"]].sort_values("team").reset_index(drop=True)
        """,
        PY_STARTER,
        ("team",),
    ),
    python_task(
        "d3_py_04_clean_dirty_summary",
        3,
        "脏数据问题计数",
        "练习 duplicated、isna、日期和数值检查。",
        "使用 tickets_dirty，实现 solve(df)，返回 issue_type、issue_count，统计 duplicate_ticket_id、missing_assignee、negative_process_hours、close_before_create 四类问题。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            data = df.copy()
            data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
            data["close_time"] = pd.to_datetime(data["close_time"], errors="coerce")
            checks = [
                ("duplicate_ticket_id", int(data["ticket_id"].duplicated(keep=False).sum())),
                ("missing_assignee", int(data["assignee"].isna().sum())),
                ("negative_process_hours", int((data["process_hours"] < 0).sum())),
                ("close_before_create", int((data["close_time"] < data["create_time"]).sum())),
            ]
            return pd.DataFrame(checks, columns=["issue_type", "issue_count"])
        """,
        PY_STARTER,
        ("issue_type",),
        ("tickets_dirty",),
    ),
    python_task(
        "d4_py_01_top_assignees",
        4,
        "Top 5 处理人",
        "练习 sort_values 和 nlargest。",
        "实现 solve(df)，只看 Closed 工单，返回关闭量 Top 5 assignee、team、closed_cnt。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            closed = df[df["status"] == "Closed"].copy()
            out = closed.groupby(["assignee", "team"]).size().reset_index(name="closed_cnt")
            return out.sort_values(["closed_cnt", "assignee"], ascending=[False, True]).head(5).reset_index(drop=True)
        """,
        PY_STARTER,
        ("closed_cnt", "assignee"),
    ),
    python_task(
        "d4_py_02_month_pct_change",
        4,
        "月度工单环比",
        "练习 pct_change。",
        "实现 solve(df)，返回 month、ticket_cnt、mom_rate，mom_rate 为工单量环比增长率，保留 4 位小数。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            data = df.copy()
            data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
            data["month"] = data["create_time"].dt.strftime("%Y-%m")
            out = data.groupby("month").size().reset_index(name="ticket_cnt").sort_values("month")
            out["mom_rate"] = out["ticket_cnt"].pct_change().round(4)
            return out.reset_index(drop=True)
        """,
        PY_STARTER,
        ("month",),
    ),
    python_task(
        "d4_py_03_type_structure",
        4,
        "任务类型结构",
        "练习占比。",
        "实现 solve(df)，返回 task_type、ticket_cnt、share，share 保留 4 位小数，按 ticket_cnt 降序。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            out = df.groupby("task_type").size().reset_index(name="ticket_cnt")
            out["share"] = (out["ticket_cnt"] / out["ticket_cnt"].sum()).round(4)
            return out.sort_values(["ticket_cnt", "task_type"], ascending=[False, True]).reset_index(drop=True)
        """,
        PY_STARTER,
        ("ticket_cnt", "task_type"),
    ),
    python_task(
        "d4_py_04_rolling_volume",
        4,
        "三个月滚动工单量",
        "练习 rolling。",
        "实现 solve(df)，返回 month、ticket_cnt、rolling_3m_ticket_cnt，滚动窗口不足 3 个月也计算。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            data = df.copy()
            data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
            data["month"] = data["create_time"].dt.strftime("%Y-%m")
            out = data.groupby("month").size().reset_index(name="ticket_cnt").sort_values("month")
            out["rolling_3m_ticket_cnt"] = out["ticket_cnt"].rolling(3, min_periods=1).sum().astype(int)
            return out.reset_index(drop=True)
        """,
        PY_STARTER,
        ("month",),
    ),
    sql_task(
        "d5_sql_01_ops_kpi",
        5,
        "共享中心团队 KPI",
        "完成业务案例核心指标。",
        "按 team 输出 ticket_cnt、avg_process_hours、sla_rate、backlog_cnt、rework_rate，avg 保留 2 位，rate 保留 4 位。",
        """
        SELECT
            team,
            COUNT(*) AS ticket_cnt,
            ROUND(AVG(process_hours), 2) AS avg_process_hours,
            ROUND(AVG(CASE WHEN status = 'Closed' AND process_hours <= sla_hours THEN 1.0 WHEN status = 'Closed' THEN 0.0 ELSE NULL END), 4) AS sla_rate,
            SUM(CASE WHEN status = 'Backlog' THEN 1 ELSE 0 END) AS backlog_cnt,
            ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4) AS rework_rate
        FROM tickets
        GROUP BY team
        ORDER BY team
        """,
        ("team",),
        timebox_minutes=35,
    ),
    python_task(
        "d5_py_01_ops_kpi",
        5,
        "pandas 团队 KPI",
        "用 pandas 完成业务案例核心指标。",
        "实现 solve(df)，按 team 输出 ticket_cnt、avg_process_hours、sla_rate、backlog_cnt、rework_rate。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            data = df.copy()
            data["sla_hit"] = (data["status"].eq("Closed")) & (data["process_hours"] <= data["sla_hours"])
            data["closed_flag"] = data["status"].eq("Closed")
            data["backlog_flag"] = data["status"].eq("Backlog")
            rows = []
            for team, g in data.groupby("team"):
                closed = g[g["closed_flag"]]
                rows.append(
                    {
                        "team": team,
                        "ticket_cnt": len(g),
                        "avg_process_hours": round(g["process_hours"].mean(), 2),
                        "sla_rate": round(g.loc[g["closed_flag"], "sla_hit"].mean(), 4),
                        "backlog_cnt": int(g["backlog_flag"].sum()),
                        "rework_rate": round(g["is_rework"].mean(), 4),
                    }
                )
            return pd.DataFrame(rows).sort_values("team").reset_index(drop=True)
        """,
        PY_STARTER,
        ("team",),
        timebox_minutes=35,
    ),
    python_task(
        "d6_py_01_quality_checklist",
        6,
        "数据质量检查清单",
        "练习系统化排查。",
        "使用 tickets_dirty，实现 solve(df)，返回 issue_type、issue_count，覆盖重复主键、空值、日期异常、数值异常、枚举异常。",
        """
        import pandas as pd


        def solve(df: pd.DataFrame) -> pd.DataFrame:
            data = df.copy()
            data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
            data["close_time"] = pd.to_datetime(data["close_time"], errors="coerce")
            valid_status = {"Closed", "Open", "Backlog"}
            valid_priority = {"Low", "Medium", "High"}
            checks = [
                ("duplicate_ticket_id", int(data["ticket_id"].duplicated(keep=False).sum())),
                ("missing_key_fields", int(data[["ticket_id", "create_time", "team", "task_type"]].isna().any(axis=1).sum())),
                ("close_before_create", int((data["close_time"] < data["create_time"]).sum())),
                ("negative_process_hours", int((data["process_hours"] < 0).sum())),
                ("extreme_process_hours", int((data["process_hours"] > 240).sum())),
                ("invalid_status", int((~data["status"].isin(valid_status)).sum())),
                ("invalid_priority", int((~data["priority"].isin(valid_priority)).sum())),
            ]
            return pd.DataFrame(checks, columns=["issue_type", "issue_count"])
        """,
        PY_STARTER,
        ("issue_type",),
        ("tickets_dirty",),
        timebox_minutes=30,
    ),
    sql_task(
        "d6_sql_01_join_row_check",
        6,
        "连接后行数校验",
        "练习 JOIN 后重复计数检查。",
        "连接 assignee_dim 前后比较 tickets 行数，输出 before_rows、after_rows、row_diff。",
        """
        WITH before_count AS (
            SELECT COUNT(*) AS before_rows FROM tickets
        ),
        after_count AS (
            SELECT COUNT(*) AS after_rows
            FROM tickets t
            LEFT JOIN assignee_dim a ON t.assignee = a.assignee
        )
        SELECT before_rows, after_rows, after_rows - before_rows AS row_diff
        FROM before_count, after_count
        """,
        (),
        ("tickets", "assignee_dim"),
        timebox_minutes=20,
    ),
    sql_task(
        "d6_sql_02_dirty_enum",
        6,
        "枚举值异常",
        "练习脏数据枚举检查。",
        "使用 tickets_dirty，找出非法 status 或 priority 的行数，输出 issue_type、issue_count。",
        """
        SELECT 'invalid_status' AS issue_type, COUNT(*) AS issue_count
        FROM tickets_dirty
        WHERE status NOT IN ('Closed', 'Open', 'Backlog')
        UNION ALL
        SELECT 'invalid_priority' AS issue_type, COUNT(*) AS issue_count
        FROM tickets_dirty
        WHERE priority NOT IN ('Low', 'Medium', 'High')
        ORDER BY issue_type
        """,
        ("issue_type",),
        ("tickets_dirty",),
        timebox_minutes=20,
    ),
    sql_task(
        "d7_sql_01_mock_exam",
        7,
        "60 分钟模拟：运营异常定位",
        "完成一次从指标到拆解的限时题。",
        "按 month、team 输出 ticket_cnt、sla_rate、avg_process_hours、rework_rate。只看 Closed 工单，数值分别保留 4/2/4 位。完成后在结论区写发现、原因和建议。",
        """
        SELECT
            strftime(create_time, '%Y-%m') AS month,
            team,
            COUNT(*) AS ticket_cnt,
            ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate,
            ROUND(AVG(process_hours), 2) AS avg_process_hours,
            ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4) AS rework_rate
        FROM tickets
        WHERE status = 'Closed'
        GROUP BY month, team
        ORDER BY month, team
        """,
        ("month", "team"),
        timebox_minutes=60,
    ),
]


def _add_sprint_tasks() -> None:
    """Add hand-written, non-template tasks for the five-day sprint view."""
    TASKS.extend(
        [
            sql_task(
                "d1_sprint_sql_01_closed_denominator_kpi",
                1,
                "冲刺：团队 KPI 分母口径",
                "训练把总量、关闭量、SLA 分母和积压量拆开，避免口径混在一起。",
                "按 team 输出 total_cnt、closed_cnt、closed_sla_rate、backlog_cnt。SLA 只以 Closed 工单为分母，保留 4 位小数。",
                """
                SELECT
                    team,
                    COUNT(*) AS total_cnt,
                    SUM(CASE WHEN status = 'Closed' THEN 1 ELSE 0 END) AS closed_cnt,
                    ROUND(
                        SUM(CASE WHEN status = 'Closed' AND process_hours <= sla_hours THEN 1.0 ELSE 0.0 END)
                        / NULLIF(SUM(CASE WHEN status = 'Closed' THEN 1.0 ELSE 0.0 END), 0),
                        4
                    ) AS closed_sla_rate,
                    SUM(CASE WHEN status = 'Backlog' THEN 1 ELSE 0 END) AS backlog_cnt
                FROM tickets
                GROUP BY team
                ORDER BY team
                """,
                ("team",),
                timebox_minutes=20,
                tier="sprint",
                difficulty="核心",
                tags=("分母口径", "SLA", "积压"),
            ),
            sql_task(
                "d1_sprint_sql_02_high_priority_sla_gap",
                1,
                "冲刺：高优先级 SLA 缺口",
                "训练用业务风险视角筛选高优先级工单。",
                "只看 High 且 Closed 的工单，按 team 输出 high_closed_cnt、avg_process_hours、avg_sla_gap_hours。gap=process_hours-sla_hours，保留 2 位，按 gap 降序。",
                """
                SELECT
                    team,
                    COUNT(*) AS high_closed_cnt,
                    ROUND(AVG(process_hours), 2) AS avg_process_hours,
                    ROUND(AVG(process_hours - sla_hours), 2) AS avg_sla_gap_hours
                FROM tickets
                WHERE priority = 'High' AND status = 'Closed'
                GROUP BY team
                ORDER BY avg_sla_gap_hours DESC, team
                """,
                ("avg_sla_gap_hours", "team"),
                timebox_minutes=18,
                tier="sprint",
                difficulty="核心",
                tags=("高优先级", "SLA", "风险排序"),
            ),
            sql_task(
                "d1_sprint_sql_03_month_type_structure",
                1,
                "冲刺：月度任务结构占比",
                "训练月度结构分析，不只是统计总量。",
                "按 month、task_type 输出 ticket_cnt、month_share。month_share 为该任务类型占当月全部工单比例，保留 4 位。",
                """
                WITH base AS (
                    SELECT
                        strftime(create_time, '%Y-%m') AS month,
                        task_type,
                        COUNT(*) AS ticket_cnt
                    FROM tickets
                    GROUP BY month, task_type
                ),
                monthly AS (
                    SELECT month, SUM(ticket_cnt) AS month_total
                    FROM base
                    GROUP BY month
                )
                SELECT
                    b.month,
                    b.task_type,
                    b.ticket_cnt,
                    ROUND(b.ticket_cnt * 1.0 / m.month_total, 4) AS month_share
                FROM base b
                JOIN monthly m ON b.month = m.month
                ORDER BY b.month, b.task_type
                """,
                ("month", "task_type"),
                mysql_tip="MySQL 可用 DATE_FORMAT(create_time, '%Y-%m')。",
                timebox_minutes=22,
                tier="sprint",
                difficulty="核心",
                tags=("结构占比", "月度分析", "分母口径"),
            ),
            sql_task(
                "d2_sprint_sql_01_join_row_count_guard",
                2,
                "冲刺：JOIN 后行数校验",
                "训练每次连接维表后先确认是否重复计数。",
                "连接 assignee_dim 前后做行数校验，输出 check_name、before_rows、after_rows、row_diff。",
                """
                WITH before_join AS (
                    SELECT COUNT(*) AS before_rows
                    FROM tickets
                ),
                after_join AS (
                    SELECT COUNT(*) AS after_rows
                    FROM tickets t
                    LEFT JOIN assignee_dim a ON t.assignee = a.assignee
                )
                SELECT
                    'tickets_to_assignee_dim' AS check_name,
                    before_rows,
                    after_rows,
                    after_rows - before_rows AS row_diff
                FROM before_join
                CROSS JOIN after_join
                """,
                ("check_name",),
                datasets=("tickets", "assignee_dim"),
                timebox_minutes=15,
                tier="sprint",
                difficulty="核心",
                tags=("JOIN", "重复计数", "校验"),
            ),
            sql_task(
                "d2_sprint_sql_02_worst_month_each_team",
                2,
                "冲刺：每团队最差 SLA 月份",
                "训练窗口函数把异常月份定位出来。",
                "只看 Closed 工单，按团队找 SLA 达成率最低的月份，输出 team、month、closed_cnt、sla_rate。",
                """
                WITH monthly AS (
                    SELECT
                        team,
                        strftime(create_time, '%Y-%m') AS month,
                        COUNT(*) AS closed_cnt,
                        ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
                    FROM tickets
                    WHERE status = 'Closed'
                    GROUP BY team, month
                ),
                ranked AS (
                    SELECT
                        team,
                        month,
                        closed_cnt,
                        sla_rate,
                        ROW_NUMBER() OVER (PARTITION BY team ORDER BY sla_rate, closed_cnt DESC, month) AS rn
                    FROM monthly
                )
                SELECT team, month, closed_cnt, sla_rate
                FROM ranked
                WHERE rn = 1
                ORDER BY team
                """,
                ("team",),
                timebox_minutes=25,
                tier="sprint",
                difficulty="进阶",
                tags=("窗口函数", "异常定位", "SLA"),
            ),
            sql_task(
                "d2_sprint_sql_03_team_sla_mom_drop",
                2,
                "冲刺：团队 SLA 环比下滑",
                "训练 LAG 和环比变化，用来解释趋势恶化。",
                "只看 Closed 工单，按 month、team 输出 sla_rate、prev_sla_rate、sla_rate_change，保留 4 位。",
                """
                WITH monthly AS (
                    SELECT
                        strftime(create_time, '%Y-%m') AS month,
                        team,
                        ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
                    FROM tickets
                    WHERE status = 'Closed'
                    GROUP BY month, team
                )
                SELECT
                    month,
                    team,
                    sla_rate,
                    LAG(sla_rate) OVER (PARTITION BY team ORDER BY month) AS prev_sla_rate,
                    ROUND(sla_rate - LAG(sla_rate) OVER (PARTITION BY team ORDER BY month), 4) AS sla_rate_change
                FROM monthly
                ORDER BY month, team
                """,
                ("month", "team"),
                mysql_tip="MySQL 同样支持 LAG(...) OVER(PARTITION BY ... ORDER BY ...)。",
                timebox_minutes=25,
                tier="sprint",
                difficulty="进阶",
                tags=("LAG", "环比", "SLA"),
            ),
            python_task(
                "d3_sprint_py_01_dirty_issue_counts",
                3,
                "冲刺：脏数据问题计数",
                "训练先查质量再算指标。",
                "实现 solve(df)，输入 tickets_dirty，返回 issue_type、issue_cnt。至少检查 duplicate_ticket_id、missing_assignee、missing_create_time、negative_process_hours、close_before_create、invalid_status、invalid_priority。",
                """
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    checks = {
                        "duplicate_ticket_id": df["ticket_id"].duplicated(keep=False),
                        "missing_assignee": df["assignee"].isna(),
                        "missing_create_time": df["create_time"].isna(),
                        "negative_process_hours": df["process_hours"] < 0,
                        "close_before_create": df["close_time"].notna() & (df["close_time"] < df["create_time"]),
                        "invalid_status": ~df["status"].isin(["Closed", "Open", "Backlog"]),
                        "invalid_priority": ~df["priority"].isin(["Low", "Medium", "High"]),
                    }
                    out = pd.DataFrame(
                        {"issue_type": name, "issue_cnt": int(mask.sum())}
                        for name, mask in checks.items()
                    )
                    return out.sort_values("issue_type").reset_index(drop=True)
                """,
                PY_STARTER,
                ("issue_type",),
                datasets=("tickets_dirty",),
                timebox_minutes=25,
                tier="sprint",
                difficulty="核心",
                tags=("数据质量", "空值", "异常值"),
            ),
            python_task(
                "d3_sprint_py_02_clean_monthly_kpi",
                3,
                "冲刺：清洗后月度 KPI",
                "训练把清洗动作和指标计算串起来。",
                "实现 solve(df)，输入 tickets_dirty：先按 ticket_id 去重，剔除 create_time 缺失、负处理时长、close_time 早于 create_time、非法 status/priority；再只看 Closed，按月输出 closed_cnt、sla_rate、avg_process_hours。",
                """
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    clean = df.drop_duplicates("ticket_id").copy()
                    valid = (
                        clean["create_time"].notna()
                        & (clean["process_hours"] >= 0)
                        & (clean["status"].isin(["Closed", "Open", "Backlog"]))
                        & (clean["priority"].isin(["Low", "Medium", "High"]))
                        & (clean["close_time"].isna() | (clean["close_time"] >= clean["create_time"]))
                    )
                    clean = clean[valid].copy()
                    closed = clean[clean["status"] == "Closed"].copy()
                    closed["month"] = closed["create_time"].dt.strftime("%Y-%m")
                    closed["sla_hit"] = closed["process_hours"] <= closed["sla_hours"]
                    out = (
                        closed.groupby("month")
                        .agg(
                            closed_cnt=("ticket_id", "count"),
                            sla_rate=("sla_hit", "mean"),
                            avg_process_hours=("process_hours", "mean"),
                        )
                        .reset_index()
                    )
                    out["sla_rate"] = out["sla_rate"].round(4)
                    out["avg_process_hours"] = out["avg_process_hours"].round(2)
                    return out.sort_values("month").reset_index(drop=True)
                """,
                PY_STARTER,
                ("month",),
                datasets=("tickets_dirty",),
                timebox_minutes=35,
                tier="sprint",
                difficulty="进阶",
                tags=("清洗流程", "月度指标", "SLA"),
            ),
            python_task(
                "d4_sprint_py_01_category_kpi_after_merge",
                4,
                "冲刺：merge 后类别 KPI",
                "训练 pandas merge 后按业务类别汇总。",
                "实现 solve(df, dim)，连接 task_dim，按 category 输出 closed_cnt、sla_rate、rework_rate、avg_complexity。只看 Closed 工单，比例保留 4 位，复杂度保留 2 位。",
                """
                import pandas as pd


                def solve(df: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
                    merged = df.merge(dim, on="task_type", how="left")
                    closed = merged[merged["status"] == "Closed"].copy()
                    closed["sla_hit"] = closed["process_hours"] <= closed["sla_hours"]
                    out = (
                        closed.groupby("category")
                        .agg(
                            closed_cnt=("ticket_id", "count"),
                            sla_rate=("sla_hit", "mean"),
                            rework_rate=("is_rework", "mean"),
                            avg_complexity=("complexity", "mean"),
                        )
                        .reset_index()
                    )
                    out["sla_rate"] = out["sla_rate"].round(4)
                    out["rework_rate"] = out["rework_rate"].round(4)
                    out["avg_complexity"] = out["avg_complexity"].round(2)
                    return out.sort_values("category").reset_index(drop=True)
                """,
                PY_TWO_TABLE_STARTER,
                ("category",),
                datasets=("tickets", "task_dim"),
                timebox_minutes=30,
                tier="sprint",
                difficulty="核心",
                tags=("merge", "维表", "业务类别"),
            ),
            python_task(
                "d4_sprint_py_02_assignee_load_risk",
                4,
                "冲刺：人员负载风险",
                "训练从人员维度识别可能的容量风险。",
                "实现 solve(df)，只看 Closed 工单，按 team、assignee 输出 closed_cnt、high_share、avg_process_hours、rework_rate。比例保留 4 位，时长保留 2 位，按 team、closed_cnt 降序。",
                """
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    closed = df[df["status"] == "Closed"].copy()
                    closed["is_high"] = closed["priority"] == "High"
                    out = (
                        closed.groupby(["team", "assignee"])
                        .agg(
                            closed_cnt=("ticket_id", "count"),
                            high_share=("is_high", "mean"),
                            avg_process_hours=("process_hours", "mean"),
                            rework_rate=("is_rework", "mean"),
                        )
                        .reset_index()
                    )
                    out["high_share"] = out["high_share"].round(4)
                    out["avg_process_hours"] = out["avg_process_hours"].round(2)
                    out["rework_rate"] = out["rework_rate"].round(4)
                    return out.sort_values(["team", "closed_cnt", "assignee"], ascending=[True, False, True]).reset_index(drop=True)
                """,
                PY_STARTER,
                ("team", "closed_cnt", "assignee"),
                timebox_minutes=30,
                tier="sprint",
                difficulty="核心",
                tags=("人员负载", "排序", "风险识别"),
            ),
            python_task(
                "d4_sprint_py_03_monthly_team_spike",
                4,
                "冲刺：月度团队业务量异常",
                "训练用历史均值和标准差找异常月份。",
                "实现 solve(df)，按 month、team 统计 ticket_cnt，并计算 team 内 mean_cnt、std_cnt、is_spike。is_spike 为 ticket_cnt > mean_cnt + std_cnt。",
                """
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    work = df.copy()
                    work["month"] = work["create_time"].dt.strftime("%Y-%m")
                    monthly = work.groupby(["month", "team"]).size().reset_index(name="ticket_cnt")
                    stats = monthly.groupby("team")["ticket_cnt"].agg(mean_cnt="mean", std_cnt="std").reset_index()
                    out = monthly.merge(stats, on="team", how="left")
                    out["std_cnt"] = out["std_cnt"].fillna(0)
                    out["mean_cnt"] = out["mean_cnt"].round(2)
                    out["std_cnt"] = out["std_cnt"].round(2)
                    out["is_spike"] = out["ticket_cnt"] > (out["mean_cnt"] + out["std_cnt"])
                    return out.sort_values(["month", "team"]).reset_index(drop=True)
                """,
                PY_STARTER,
                ("month", "team"),
                timebox_minutes=35,
                tier="sprint",
                difficulty="进阶",
                tags=("异常检测", "rolling思维", "月度趋势"),
            ),
            sql_task(
                "d5_sprint_sql_01_root_cause_team_type",
                5,
                "冲刺：SLA 根因拆解到任务类型",
                "训练把团队问题继续拆到任务类型，而不是停在总指标。",
                "只看 Closed 工单，按 team、task_type 输出 closed_cnt、sla_rate、avg_process_hours、rework_rate，按 sla_rate 升序、closed_cnt 降序。",
                """
                SELECT
                    team,
                    task_type,
                    COUNT(*) AS closed_cnt,
                    ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate,
                    ROUND(AVG(process_hours), 2) AS avg_process_hours,
                    ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4) AS rework_rate
                FROM tickets
                WHERE status = 'Closed'
                GROUP BY team, task_type
                ORDER BY sla_rate, closed_cnt DESC, team, task_type
                """,
                ("sla_rate", "closed_cnt", "team", "task_type"),
                timebox_minutes=30,
                tier="sprint",
                difficulty="核心",
                tags=("根因拆解", "SLA", "返工"),
            ),
            python_task(
                "d5_sprint_py_01_ops_risk_score",
                5,
                "冲刺：团队运营风险分",
                "训练把多个指标合成一个可排序的运营风险视图。",
                "实现 solve(df)，按 team 输出 ticket_cnt、closed_cnt、sla_rate、backlog_cnt、rework_rate、risk_score。risk_score=(1-sla_rate)*50 + rework_rate*30 + backlog_cnt/ticket_cnt*20，保留 2 位。",
                """
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    work = df.copy()
                    work["is_closed"] = work["status"] == "Closed"
                    work["is_backlog"] = work["status"] == "Backlog"
                    work["sla_hit"] = work["is_closed"] & (work["process_hours"] <= work["sla_hours"])
                    out = (
                        work.groupby("team")
                        .agg(
                            ticket_cnt=("ticket_id", "count"),
                            closed_cnt=("is_closed", "sum"),
                            sla_hit_cnt=("sla_hit", "sum"),
                            backlog_cnt=("is_backlog", "sum"),
                            rework_rate=("is_rework", "mean"),
                        )
                        .reset_index()
                    )
                    out["sla_rate"] = (out["sla_hit_cnt"] / out["closed_cnt"]).round(4)
                    out["rework_rate"] = out["rework_rate"].round(4)
                    out["risk_score"] = (
                        (1 - out["sla_rate"]) * 50
                        + out["rework_rate"] * 30
                        + (out["backlog_cnt"] / out["ticket_cnt"]) * 20
                    ).round(2)
                    out = out.drop(columns=["sla_hit_cnt"])
                    return out[["team", "ticket_cnt", "closed_cnt", "sla_rate", "backlog_cnt", "rework_rate", "risk_score"]].sort_values(
                        ["risk_score", "team"], ascending=[False, True]
                    ).reset_index(drop=True)
                """,
                PY_STARTER,
                ("risk_score", "team"),
                timebox_minutes=40,
                tier="sprint",
                difficulty="进阶",
                tags=("综合KPI", "风险评分", "业务建议"),
            ),
            sql_task(
                "d6_sprint_sql_01_dirty_issue_counts",
                6,
                "冲刺：SQL 数据质量清单",
                "训练用 SQL 快速给出质量问题分布。",
                "基于 tickets_dirty 输出 issue_type、issue_cnt，检查重复主键、缺失字段、日期异常、负时长、非法枚举。",
                """
                SELECT 'duplicate_ticket_id' AS issue_type, COUNT(*) AS issue_cnt
                FROM tickets_dirty
                WHERE ticket_id IN (
                    SELECT ticket_id
                    FROM tickets_dirty
                    GROUP BY ticket_id
                    HAVING COUNT(*) > 1
                )
                UNION ALL
                SELECT 'missing_assignee', COUNT(*) FROM tickets_dirty WHERE assignee IS NULL
                UNION ALL
                SELECT 'missing_create_time', COUNT(*) FROM tickets_dirty WHERE create_time IS NULL
                UNION ALL
                SELECT 'negative_process_hours', COUNT(*) FROM tickets_dirty WHERE process_hours < 0
                UNION ALL
                SELECT 'close_before_create', COUNT(*) FROM tickets_dirty WHERE close_time < create_time
                UNION ALL
                SELECT 'invalid_status', COUNT(*) FROM tickets_dirty WHERE status NOT IN ('Closed', 'Open', 'Backlog')
                UNION ALL
                SELECT 'invalid_priority', COUNT(*) FROM tickets_dirty WHERE priority NOT IN ('Low', 'Medium', 'High')
                ORDER BY issue_type
                """,
                ("issue_type",),
                datasets=("tickets_dirty",),
                timebox_minutes=25,
                tier="sprint",
                difficulty="核心",
                tags=("数据质量", "SQL排查", "枚举异常"),
            ),
            sql_task(
                "d7_sprint_sql_01_mock_exam_team_month",
                7,
                "冲刺模拟：团队月度异常定位",
                "完成一次接近机考的指标计算，结论区写发现、原因假设和建议。",
                "只看 Closed 工单，按 month、team 输出 closed_cnt、sla_rate、avg_process_hours、rework_rate、mom_closed_change。最后在业务结论区解释最值得关注的团队月份。",
                """
                WITH monthly AS (
                    SELECT
                        strftime(create_time, '%Y-%m') AS month,
                        team,
                        COUNT(*) AS closed_cnt,
                        ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate,
                        ROUND(AVG(process_hours), 2) AS avg_process_hours,
                        ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4) AS rework_rate
                    FROM tickets
                    WHERE status = 'Closed'
                    GROUP BY month, team
                )
                SELECT
                    month,
                    team,
                    closed_cnt,
                    sla_rate,
                    avg_process_hours,
                    rework_rate,
                    closed_cnt - LAG(closed_cnt) OVER (PARTITION BY team ORDER BY month) AS mom_closed_change
                FROM monthly
                ORDER BY month, team
                """,
                ("month", "team"),
                timebox_minutes=60,
                tier="sprint",
                difficulty="模拟",
                tags=("限时模拟", "环比", "业务结论"),
            ),
            python_task(
                "d7_sprint_py_01_mock_exam_ops_case",
                7,
                "冲刺模拟：Python 运营效率小报告",
                "用 pandas 完成一次从清洗到 KPI 输出的限时模拟。",
                "实现 solve(df)，输出 team、ticket_cnt、closed_cnt、sla_rate、avg_process_hours、backlog_cnt、rework_rate。请在结论区写三句话：发现、原因假设、建议。",
                """
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    work = df.drop_duplicates("ticket_id").copy()
                    work["is_closed"] = work["status"] == "Closed"
                    work["is_backlog"] = work["status"] == "Backlog"
                    closed = work[work["is_closed"]].copy()
                    closed["sla_hit"] = closed["process_hours"] <= closed["sla_hours"]
                    base = work.groupby("team").agg(
                        ticket_cnt=("ticket_id", "count"),
                        backlog_cnt=("is_backlog", "sum"),
                        rework_rate=("is_rework", "mean"),
                    )
                    closed_kpi = closed.groupby("team").agg(
                        closed_cnt=("ticket_id", "count"),
                        sla_rate=("sla_hit", "mean"),
                        avg_process_hours=("process_hours", "mean"),
                    )
                    out = base.join(closed_kpi, how="left").reset_index()
                    out["sla_rate"] = out["sla_rate"].round(4)
                    out["avg_process_hours"] = out["avg_process_hours"].round(2)
                    out["rework_rate"] = out["rework_rate"].round(4)
                    return out[["team", "ticket_cnt", "closed_cnt", "sla_rate", "avg_process_hours", "backlog_cnt", "rework_rate"]].sort_values(
                        "team"
                    ).reset_index(drop=True)
                """,
                PY_STARTER,
                ("team",),
                timebox_minutes=60,
                tier="sprint",
                difficulty="模拟",
                tags=("限时模拟", "pandas", "综合KPI"),
            ),
        ]
    )


def _add_generated_tasks() -> None:
    group_labels = {
        "team": "团队",
        "priority": "优先级",
        "status": "状态",
        "task_type": "任务类型",
        "assignee": "处理人",
    }
    safe_names = {
        "team": "team",
        "priority": "priority",
        "status": "status",
        "task_type": "task_type",
        "assignee": "assignee",
    }

    for col in ["priority", "status", "assignee"]:
        TASKS.append(
            sql_task(
                f"d1_gen_{safe_names[col]}_ticket_count",
                1,
                f"按{group_labels[col]}统计工单量",
                "练习基础分组计数。",
                f"按 {col} 统计工单量，输出 {col}、ticket_cnt。",
                f"""
                SELECT {col}, COUNT(*) AS ticket_cnt
                FROM tickets
                GROUP BY {col}
                ORDER BY {col}
                """,
                (col,),
            )
        )
        TASKS.append(
            sql_task(
                f"d1_gen_{safe_names[col]}_closed_count",
                1,
                f"按{group_labels[col]}统计关闭量",
                "练习 WHERE 后聚合。",
                f"只看 Closed 工单，按 {col} 统计关闭量，输出 {col}、closed_cnt。",
                f"""
                SELECT {col}, COUNT(*) AS closed_cnt
                FROM tickets
                WHERE status = 'Closed'
                GROUP BY {col}
                ORDER BY {col}
                """,
                (col,),
            )
        )
        TASKS.append(
            sql_task(
                f"d1_gen_{safe_names[col]}_avg_hours",
                1,
                f"按{group_labels[col]}统计平均时长",
                "练习 AVG 与小数保留。",
                f"只看 Closed 工单，按 {col} 统计平均处理时长 avg_process_hours，保留 2 位。",
                f"""
                SELECT {col}, ROUND(AVG(process_hours), 2) AS avg_process_hours
                FROM tickets
                WHERE status = 'Closed'
                GROUP BY {col}
                ORDER BY {col}
                """,
                (col,),
            )
        )

    for col in ["team", "task_type", "priority", "assignee"]:
        TASKS.append(
            sql_task(
                f"d1_gen_{safe_names[col]}_sla_fail_rate",
                1,
                f"按{group_labels[col]}统计 SLA 失败率",
                "练习条件聚合和分母口径。",
                f"只看 Closed 工单，按 {col} 计算 sla_fail_rate，process_hours > sla_hours 记为失败，保留 4 位。",
                f"""
                SELECT
                    {col},
                    ROUND(AVG(CASE WHEN process_hours > sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_fail_rate
                FROM tickets
                WHERE status = 'Closed'
                GROUP BY {col}
                ORDER BY {col}
                """,
                (col,),
            )
        )
        TASKS.append(
            sql_task(
                f"d1_gen_{safe_names[col]}_high_share",
                1,
                f"按{group_labels[col]}统计高优先级占比",
                "练习条件占比。",
                f"按 {col} 计算 high_priority_share，priority='High' 记为高优先级，保留 4 位。",
                f"""
                SELECT
                    {col},
                    ROUND(AVG(CASE WHEN priority = 'High' THEN 1.0 ELSE 0.0 END), 4) AS high_priority_share
                FROM tickets
                GROUP BY {col}
                ORDER BY {col}
                """,
                (col,),
            )
        )

    for status in ["Closed", "Open", "Backlog"]:
        status_slug = status.lower()
        TASKS.append(
            sql_task(
                f"d1_gen_month_{status_slug}_count",
                1,
                f"月度 {status} 工单量",
                "练习状态过滤和月度聚合。",
                f"按月统计 status='{status}' 的工单量，输出 month、ticket_cnt。",
                f"""
                SELECT strftime(create_time, '%Y-%m') AS month, COUNT(*) AS ticket_cnt
                FROM tickets
                WHERE status = '{status}'
                GROUP BY month
                ORDER BY month
                """,
                ("month",),
            )
        )

    for priority in ["Low", "Medium", "High"]:
        priority_slug = priority.lower()
        TASKS.append(
            sql_task(
                f"d1_gen_team_{priority_slug}_count",
                1,
                f"团队 {priority} 优先级工单量",
                "练习复合分组口径。",
                f"按 team 统计 priority='{priority}' 的工单量，输出 team、ticket_cnt。",
                f"""
                SELECT team, COUNT(*) AS ticket_cnt
                FROM tickets
                WHERE priority = '{priority}'
                GROUP BY team
                ORDER BY team
                """,
                ("team",),
            )
        )

    rank_specs = [
        ("team", "task_type", "AVG(process_hours)", "avg_process_hours", "平均处理时长", "ROUND(AVG(process_hours), 2)"),
        ("team", "assignee", "COUNT(*)", "ticket_cnt", "工单量", "COUNT(*)"),
        ("team", "task_type", "AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END)", "rework_rate", "返工率", "ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4)"),
        ("priority", "team", "COUNT(*)", "ticket_cnt", "工单量", "COUNT(*)"),
        ("task_type", "team", "AVG(process_hours)", "avg_process_hours", "平均处理时长", "ROUND(AVG(process_hours), 2)"),
    ]
    for idx, (group_col, item_col, order_expr, metric_alias, metric_label, select_expr) in enumerate(rank_specs, start=1):
        TASKS.append(
            sql_task(
                f"d2_gen_rank_{idx}_{group_col}_{item_col}",
                2,
                f"每{group_labels[group_col]} Top 3 {group_labels[item_col]}",
                "练习 ROW_NUMBER 分区排名。",
                f"只看 Closed 工单，按 {group_col} 找出 {metric_label} Top 3 的 {item_col}。",
                f"""
                WITH ranked AS (
                    SELECT
                        {group_col},
                        {item_col},
                        {select_expr} AS {metric_alias},
                        ROW_NUMBER() OVER (
                            PARTITION BY {group_col}
                            ORDER BY {order_expr} DESC, {item_col}
                        ) AS rn
                    FROM tickets
                    WHERE status = 'Closed'
                    GROUP BY {group_col}, {item_col}
                )
                SELECT {group_col}, {item_col}, {metric_alias}
                FROM ranked
                WHERE rn <= 3
                ORDER BY {group_col}, {metric_alias} DESC, {item_col}
                """,
                (group_col, metric_alias, item_col),
            )
        )

    for col in ["team", "task_type", "assignee", "priority"]:
        TASKS.append(
            sql_task(
                f"d2_gen_global_rank_{safe_names[col]}_volume",
                2,
                f"{group_labels[col]}工单量全局排名",
                "练习 RANK 全局排名。",
                f"按 {col} 统计工单量，并输出 volume_rank。",
                f"""
                WITH base AS (
                    SELECT {col}, COUNT(*) AS ticket_cnt
                    FROM tickets
                    GROUP BY {col}
                )
                SELECT
                    {col},
                    ticket_cnt,
                    RANK() OVER (ORDER BY ticket_cnt DESC, {col}) AS volume_rank
                FROM base
                ORDER BY volume_rank, {col}
                """,
                ("volume_rank", col),
            )
        )
        TASKS.append(
            sql_task(
                f"d2_gen_global_rank_{safe_names[col]}_sla",
                2,
                f"{group_labels[col]} SLA 全局排名",
                "练习窗口排名和条件聚合。",
                f"只看 Closed 工单，按 {col} 计算 SLA 达成率并输出 sla_rank。",
                f"""
                WITH base AS (
                    SELECT
                        {col},
                        ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
                    FROM tickets
                    WHERE status = 'Closed'
                    GROUP BY {col}
                )
                SELECT
                    {col},
                    sla_rate,
                    RANK() OVER (ORDER BY sla_rate DESC, {col}) AS sla_rank
                FROM base
                ORDER BY sla_rank, {col}
                """,
                ("sla_rank", col),
            )
        )

    for col in ["team", "priority", "task_type"]:
        TASKS.append(
            sql_task(
                f"d2_gen_monthly_lag_{safe_names[col]}",
                2,
                f"按{group_labels[col]}拆解月度环比",
                "练习 LAG 分区环比。",
                f"按 month、{col} 统计工单量，并计算同一 {col} 下相对上月的 mom_change。",
                f"""
                WITH monthly AS (
                    SELECT
                        strftime(create_time, '%Y-%m') AS month,
                        {col},
                        COUNT(*) AS ticket_cnt
                    FROM tickets
                    GROUP BY month, {col}
                )
                SELECT
                    month,
                    {col},
                    ticket_cnt,
                    ticket_cnt - LAG(ticket_cnt) OVER (PARTITION BY {col} ORDER BY month) AS mom_change
                FROM monthly
                ORDER BY month, {col}
                """,
                ("month", col),
            )
        )
        TASKS.append(
            sql_task(
                f"d2_gen_monthly_cumulative_{safe_names[col]}",
                2,
                f"按{group_labels[col]}拆解累计工单量",
                "练习 SUM OVER 分区累计。",
                f"按 month、{col} 统计工单量，并计算同一 {col} 下累计工单量 cumulative_ticket_cnt。",
                f"""
                WITH monthly AS (
                    SELECT
                        strftime(create_time, '%Y-%m') AS month,
                        {col},
                        COUNT(*) AS ticket_cnt
                    FROM tickets
                    GROUP BY month, {col}
                )
                SELECT
                    month,
                    {col},
                    ticket_cnt,
                    SUM(ticket_cnt) OVER (
                        PARTITION BY {col}
                        ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) AS cumulative_ticket_cnt
                FROM monthly
                ORDER BY month, {col}
                """,
                ("month", col),
            )
        )

    join_specs = [
        ("category", "COUNT(*)", "ticket_cnt", "工单量", "COUNT(*)"),
        ("category", "AVG(t.process_hours)", "avg_process_hours", "平均处理时长", "ROUND(AVG(t.process_hours), 2)"),
        ("complexity", "COUNT(*)", "ticket_cnt", "复杂度工单量", "COUNT(*)"),
        ("complexity", "AVG(CASE WHEN t.is_rework THEN 1.0 ELSE 0.0 END)", "rework_rate", "返工率", "ROUND(AVG(CASE WHEN t.is_rework THEN 1.0 ELSE 0.0 END), 4)"),
    ]
    for idx, (col, _order_expr, alias, label, select_expr) in enumerate(join_specs, start=1):
        TASKS.append(
            sql_task(
                f"d2_gen_task_dim_{idx}_{col}_{alias}",
                2,
                f"按任务维表统计{label}",
                "练习连接任务维表后聚合。",
                f"连接 task_dim，按 {col} 输出 {alias}。",
                f"""
                SELECT
                    d.{col},
                    {select_expr} AS {alias}
                FROM tickets t
                JOIN task_dim d ON t.task_type = d.task_type
                GROUP BY d.{col}
                ORDER BY d.{col}
                """,
                (col,),
                datasets=("tickets", "task_dim"),
            )
        )

    for col in ["level", "team"]:
        TASKS.append(
            sql_task(
                f"d2_gen_assignee_dim_{col}_sla",
                2,
                f"按人员维表 {col} 统计 SLA",
                "练习连接人员维表后聚合。",
                f"连接 assignee_dim，只看 Closed 工单，按人员维表的 {col} 统计 sla_rate。",
                f"""
                SELECT
                    a.{col},
                    ROUND(AVG(CASE WHEN t.process_hours <= t.sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate
                FROM tickets t
                JOIN assignee_dim a ON t.assignee = a.assignee
                WHERE t.status = 'Closed'
                GROUP BY a.{col}
                ORDER BY a.{col}
                """,
                (col,),
                datasets=("tickets", "assignee_dim"),
            )
        )
        TASKS.append(
            sql_task(
                f"d2_gen_assignee_dim_{col}_avg_hours",
                2,
                f"按人员维表 {col} 统计平均时长",
                "练习连接人员维表后聚合。",
                f"连接 assignee_dim，只看 Closed 工单，按人员维表的 {col} 统计 avg_process_hours。",
                f"""
                SELECT
                    a.{col},
                    ROUND(AVG(t.process_hours), 2) AS avg_process_hours
                FROM tickets t
                JOIN assignee_dim a ON t.assignee = a.assignee
                WHERE t.status = 'Closed'
                GROUP BY a.{col}
                ORDER BY a.{col}
                """,
                (col,),
                datasets=("tickets", "assignee_dim"),
            )
        )

    py_metric_templates = [
        ("team", "团队"),
        ("priority", "优先级"),
        ("task_type", "任务类型"),
        ("status", "状态"),
        ("assignee", "处理人"),
    ]
    for col, label in py_metric_templates:
        TASKS.append(
            python_task(
                f"d3_gen_py_{safe_names[col]}_summary",
                3,
                f"pandas 按{label}汇总",
                "练习 pandas groupby 多指标。",
                f"实现 solve(df)，按 {col} 返回 ticket_cnt、avg_process_hours、rework_rate。",
                f"""
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    out = (
                        df.groupby("{col}")
                        .agg(
                            ticket_cnt=("ticket_id", "count"),
                            avg_process_hours=("process_hours", "mean"),
                            rework_rate=("is_rework", "mean"),
                        )
                        .reset_index()
                    )
                    out["avg_process_hours"] = out["avg_process_hours"].round(2)
                    out["rework_rate"] = out["rework_rate"].round(4)
                    return out.sort_values("{col}").reset_index(drop=True)
                """,
                PY_STARTER,
                (col,),
            )
        )
        TASKS.append(
            python_task(
                f"d3_gen_py_{safe_names[col]}_closed_sla",
                3,
                f"pandas 按{label}计算 SLA",
                "练习筛选、布尔条件和 groupby。",
                f"实现 solve(df)，只看 Closed 工单，按 {col} 返回 closed_cnt、sla_rate。",
                f"""
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    closed = df[df["status"] == "Closed"].copy()
                    closed["sla_hit"] = closed["process_hours"] <= closed["sla_hours"]
                    out = (
                        closed.groupby("{col}")
                        .agg(closed_cnt=("ticket_id", "count"), sla_rate=("sla_hit", "mean"))
                        .reset_index()
                    )
                    out["sla_rate"] = out["sla_rate"].round(4)
                    return out.sort_values("{col}").reset_index(drop=True)
                """,
                PY_STARTER,
                (col,),
            )
        )

    for issue_name, expression in [
        ("duplicate_ticket_id", 'data["ticket_id"].duplicated(keep=False)'),
        ("missing_assignee", 'data["assignee"].isna()'),
        ("missing_create_time", 'data["create_time"].isna()'),
        ("negative_process_hours", 'data["process_hours"] < 0'),
        ("extreme_process_hours", 'data["process_hours"] > 240'),
    ]:
        TASKS.append(
            python_task(
                f"d3_gen_py_dirty_{issue_name}",
                3,
                f"pandas 检查 {issue_name}",
                "练习单项数据质量检查。",
                f"使用 tickets_dirty，实现 solve(df)，返回 issue_type、issue_count，统计 {issue_name}。",
                f"""
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    data = df.copy()
                    data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
                    mask = {expression}
                    return pd.DataFrame([{{"issue_type": "{issue_name}", "issue_count": int(mask.sum())}}])
                """,
                PY_STARTER,
                ("issue_type",),
                ("tickets_dirty",),
            )
        )

    for col, label in [("team", "团队"), ("priority", "优先级"), ("task_type", "任务类型")]:
        TASKS.append(
            python_task(
                f"d4_gen_py_monthly_pivot_{safe_names[col]}",
                4,
                f"pandas 月度 x {label} 透视",
                "练习 pivot_table 和缺失填充。",
                f"实现 solve(df)，返回以 month 为行、{col} 为列的工单量透视表，缺失填 0。",
                f"""
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    data = df.copy()
                    data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
                    data["month"] = data["create_time"].dt.strftime("%Y-%m")
                    out = pd.pivot_table(
                        data,
                        index="month",
                        columns="{col}",
                        values="ticket_id",
                        aggfunc="count",
                        fill_value=0,
                    ).reset_index()
                    return out.sort_values("month").reset_index(drop=True)
                """,
                PY_STARTER,
                ("month",),
            )
        )
        TASKS.append(
            python_task(
                f"d4_gen_py_{safe_names[col]}_top5_avg_hours",
                4,
                f"pandas {label}平均时长 Top 5",
                "练习排序和 Top N。",
                f"实现 solve(df)，只看 Closed 工单，按 {col} 计算 avg_process_hours，并返回 Top 5。",
                f"""
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    closed = df[df["status"] == "Closed"].copy()
                    out = closed.groupby("{col}")["process_hours"].mean().reset_index(name="avg_process_hours")
                    out["avg_process_hours"] = out["avg_process_hours"].round(2)
                    return out.sort_values(["avg_process_hours", "{col}"], ascending=[False, True]).head(5).reset_index(drop=True)
                """,
                PY_STARTER,
                ("avg_process_hours", col),
            )
        )
        TASKS.append(
            python_task(
                f"d4_gen_py_monthly_{safe_names[col]}_sla",
                4,
                f"pandas 月度{label} SLA",
                "练习分组、条件指标和排序。",
                f"实现 solve(df)，只看 Closed 工单，按 month、{col} 返回 sla_rate。",
                f"""
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    data = df.copy()
                    data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
                    closed = data[data["status"] == "Closed"].copy()
                    closed["month"] = closed["create_time"].dt.strftime("%Y-%m")
                    closed["sla_hit"] = closed["process_hours"] <= closed["sla_hours"]
                    out = closed.groupby(["month", "{col}"])["sla_hit"].mean().reset_index(name="sla_rate")
                    out["sla_rate"] = out["sla_rate"].round(4)
                    return out.sort_values(["month", "{col}"]).reset_index(drop=True)
                """,
                PY_STARTER,
                ("month", col),
            )
        )

    for window in [2, 3, 4, 6]:
        TASKS.append(
            python_task(
                f"d4_gen_py_rolling_{window}m_volume",
                4,
                f"pandas {window} 月滚动工单量",
                "练习 rolling 窗口。",
                f"实现 solve(df)，按月返回 ticket_cnt 和 rolling_{window}m_ticket_cnt。",
                f"""
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    data = df.copy()
                    data["create_time"] = pd.to_datetime(data["create_time"], errors="coerce")
                    data["month"] = data["create_time"].dt.strftime("%Y-%m")
                    out = data.groupby("month").size().reset_index(name="ticket_cnt").sort_values("month")
                    out["rolling_{window}m_ticket_cnt"] = out["ticket_cnt"].rolling({window}, min_periods=1).sum().astype(int)
                    return out.reset_index(drop=True)
                """,
                PY_STARTER,
                ("month",),
            )
        )

    for col in ["team", "priority", "task_type", "assignee"]:
        TASKS.append(
            sql_task(
                f"d5_gen_sql_ops_{safe_names[col]}_kpi",
                5,
                f"按{group_labels[col]}输出运营 KPI",
                "练习综合业务指标。",
                f"按 {col} 输出 ticket_cnt、avg_process_hours、sla_rate、backlog_cnt、rework_rate。",
                f"""
                SELECT
                    {col},
                    COUNT(*) AS ticket_cnt,
                    ROUND(AVG(process_hours), 2) AS avg_process_hours,
                    ROUND(AVG(CASE WHEN status = 'Closed' AND process_hours <= sla_hours THEN 1.0 WHEN status = 'Closed' THEN 0.0 ELSE NULL END), 4) AS sla_rate,
                    SUM(CASE WHEN status = 'Backlog' THEN 1 ELSE 0 END) AS backlog_cnt,
                    ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4) AS rework_rate
                FROM tickets
                GROUP BY {col}
                ORDER BY {col}
                """,
                (col,),
                timebox_minutes=35,
            )
        )

    for col in ["team", "priority", "task_type", "status", "assignee"]:
        TASKS.append(
            sql_task(
                f"d5_gen_sql_monthly_{safe_names[col]}_volume_hours",
                5,
                f"月度{group_labels[col]}业务量与时长",
                "练习综合案例中的时间拆解。",
                f"按 month、{col} 输出 ticket_cnt、avg_process_hours，平均时长保留 2 位。",
                f"""
                SELECT
                    strftime(create_time, '%Y-%m') AS month,
                    {col},
                    COUNT(*) AS ticket_cnt,
                    ROUND(AVG(process_hours), 2) AS avg_process_hours
                FROM tickets
                GROUP BY month, {col}
                ORDER BY month, {col}
                """,
                ("month", col),
                timebox_minutes=30,
            )
        )

    for col, label in [("team", "团队"), ("priority", "优先级"), ("task_type", "任务类型")]:
        TASKS.append(
            python_task(
                f"d5_gen_py_ops_{safe_names[col]}_kpi",
                5,
                f"pandas 按{label}输出运营 KPI",
                "练习 pandas 综合业务指标。",
                f"实现 solve(df)，按 {col} 输出 ticket_cnt、avg_process_hours、sla_rate、backlog_cnt、rework_rate。",
                f"""
                import pandas as pd


                def solve(df: pd.DataFrame) -> pd.DataFrame:
                    data = df.copy()
                    data["closed_flag"] = data["status"].eq("Closed")
                    data["sla_hit"] = data["closed_flag"] & (data["process_hours"] <= data["sla_hours"])
                    data["backlog_flag"] = data["status"].eq("Backlog")
                    rows = []
                    for key, g in data.groupby("{col}"):
                        closed = g[g["closed_flag"]]
                        rows.append({{
                            "{col}": key,
                            "ticket_cnt": len(g),
                            "avg_process_hours": round(g["process_hours"].mean(), 2),
                            "sla_rate": round(g.loc[g["closed_flag"], "sla_hit"].mean(), 4),
                            "backlog_cnt": int(g["backlog_flag"].sum()),
                            "rework_rate": round(g["is_rework"].mean(), 4),
                        }})
                    return pd.DataFrame(rows).sort_values("{col}").reset_index(drop=True)
                """,
                PY_STARTER,
                (col,),
                timebox_minutes=35,
            )
        )

    dirty_sql_checks = [
        ("duplicate_ticket_id", "ticket_id IN (SELECT ticket_id FROM tickets_dirty GROUP BY ticket_id HAVING COUNT(*) > 1)"),
        ("missing_assignee", "assignee IS NULL"),
        ("missing_create_time", "create_time IS NULL"),
        ("negative_process_hours", "process_hours < 0"),
        ("close_before_create", "close_time < create_time"),
        ("invalid_status", "status NOT IN ('Closed', 'Open', 'Backlog')"),
        ("invalid_priority", "priority NOT IN ('Low', 'Medium', 'High')"),
        ("unknown_team", "team NOT IN ('AP', 'AR', 'GL', 'Payroll', 'Procurement')"),
        ("extreme_process_hours", "process_hours > 240"),
    ]
    for issue_name, where_expr in dirty_sql_checks:
        TASKS.append(
            sql_task(
                f"d6_gen_sql_dirty_{issue_name}",
                6,
                f"SQL 检查 {issue_name}",
                "练习单项脏数据排查。",
                f"使用 tickets_dirty，统计 {issue_name} 的行数，输出 issue_type、issue_count。",
                f"""
                SELECT '{issue_name}' AS issue_type, COUNT(*) AS issue_count
                FROM tickets_dirty
                WHERE {where_expr}
                """,
                ("issue_type",),
                datasets=("tickets_dirty",),
                timebox_minutes=18,
            )
        )

    simulation_specs = [
        ("team", "团队"),
        ("priority", "优先级"),
        ("task_type", "任务类型"),
        ("assignee", "处理人"),
    ]
    for col, label in simulation_specs:
        TASKS.append(
            sql_task(
                f"d7_gen_sql_mock_month_{safe_names[col]}",
                7,
                f"限时模拟：月度{label}异常定位",
                "完成一次指标计算和业务解释。",
                f"只看 Closed 工单，按 month、{col} 输出 ticket_cnt、sla_rate、avg_process_hours、rework_rate，并在结论区写发现、原因和建议。",
                f"""
                SELECT
                    strftime(create_time, '%Y-%m') AS month,
                    {col},
                    COUNT(*) AS ticket_cnt,
                    ROUND(AVG(CASE WHEN process_hours <= sla_hours THEN 1.0 ELSE 0.0 END), 4) AS sla_rate,
                    ROUND(AVG(process_hours), 2) AS avg_process_hours,
                    ROUND(AVG(CASE WHEN is_rework THEN 1.0 ELSE 0.0 END), 4) AS rework_rate
                FROM tickets
                WHERE status = 'Closed'
                GROUP BY month, {col}
                ORDER BY month, {col}
                """,
                ("month", col),
                timebox_minutes=60,
            )
        )


_add_sprint_tasks()
_add_generated_tasks()


TASK_BY_ID = {task.id: task for task in TASKS}


def get_task(task_id: str) -> TaskSpec:
    return TASK_BY_ID[task_id]


def list_tasks() -> list[TaskSpec]:
    return TASKS
