from functools import lru_cache
import json

import numpy as np
import pandas as pd


FIELD_DICTIONARY = [
    {"field": "ticket_id", "type": "string", "meaning": "工单唯一编号"},
    {"field": "create_time", "type": "datetime", "meaning": "工单创建时间"},
    {"field": "close_time", "type": "datetime", "meaning": "工单关闭时间，未关闭为空"},
    {"field": "team", "type": "string", "meaning": "处理团队"},
    {"field": "assignee", "type": "string", "meaning": "处理人"},
    {"field": "task_type", "type": "string", "meaning": "任务类型"},
    {"field": "sla_hours", "type": "number", "meaning": "SLA 要求处理小时数"},
    {"field": "process_hours", "type": "number", "meaning": "实际处理小时数"},
    {"field": "is_rework", "type": "boolean", "meaning": "是否返工"},
    {"field": "status", "type": "string", "meaning": "Closed/Open/Backlog"},
    {"field": "priority", "type": "string", "meaning": "Low/Medium/High"},
]

TASK_DIM_FIELDS = [
    {"field": "task_type", "type": "string", "meaning": "任务类型"},
    {"field": "category", "type": "string", "meaning": "任务归属类别"},
    {"field": "complexity", "type": "number", "meaning": "复杂度评分，1 到 5"},
]

ASSIGNEE_DIM_FIELDS = [
    {"field": "assignee", "type": "string", "meaning": "处理人"},
    {"field": "team", "type": "string", "meaning": "所属团队"},
    {"field": "level", "type": "string", "meaning": "Analyst/Senior/Lead"},
]


@lru_cache(maxsize=1)
def get_datasets() -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(20250604)
    teams = {
        "AP": ["ap_chen", "ap_li", "ap_wang", "ap_zhao"],
        "AR": ["ar_sun", "ar_zhou", "ar_qian", "ar_wu"],
        "GL": ["gl_liu", "gl_xu", "gl_ma", "gl_huang"],
        "Payroll": ["pay_gao", "pay_lin", "pay_fang", "pay_he"],
        "Procurement": ["pro_luo", "pro_zheng", "pro_tan", "pro_yang"],
    }
    task_dim = pd.DataFrame(
        [
            ("Invoice", "Finance Ops", 3),
            ("Payment", "Finance Ops", 3),
            ("Reconciliation", "Control", 4),
            ("Vendor Master", "Master Data", 2),
            ("Expense Claim", "Finance Ops", 2),
            ("Payroll Query", "People Ops", 3),
            ("Month-end Close", "Control", 5),
            ("Report Request", "Reporting", 2),
        ],
        columns=["task_type", "category", "complexity"],
    )
    assignee_rows = []
    levels = ["Analyst", "Senior", "Lead", "Analyst"]
    for team, assignees in teams.items():
        for idx, assignee in enumerate(assignees):
            assignee_rows.append((assignee, team, levels[idx]))
    assignee_dim = pd.DataFrame(assignee_rows, columns=["assignee", "team", "level"])

    task_weights = np.array([0.22, 0.15, 0.16, 0.09, 0.13, 0.08, 0.10, 0.07])
    priority_weights = np.array([0.25, 0.53, 0.22])
    status_weights = np.array([0.82, 0.09, 0.09])
    task_base = {
        "Invoice": 30,
        "Payment": 28,
        "Reconciliation": 50,
        "Vendor Master": 20,
        "Expense Claim": 24,
        "Payroll Query": 32,
        "Month-end Close": 60,
        "Report Request": 22,
    }
    team_factor = {"AP": 1.08, "AR": 0.96, "GL": 1.18, "Payroll": 0.92, "Procurement": 1.02}
    priority_factor = {"Low": 0.8, "Medium": 1.0, "High": 1.3}
    sla_by_priority = {"Low": 72, "Medium": 48, "High": 24}
    dates = pd.date_range("2025-01-01", "2025-06-30", freq="D")

    rows = []
    task_values = task_dim["task_type"].to_numpy()
    team_values = np.array(list(teams.keys()))
    for i in range(1, 481):
        team = str(rng.choice(team_values, p=[0.24, 0.18, 0.22, 0.16, 0.20]))
        assignee = str(rng.choice(teams[team]))
        task_type = str(rng.choice(task_values, p=task_weights))
        priority = str(rng.choice(["Low", "Medium", "High"], p=priority_weights))
        status = str(rng.choice(["Closed", "Open", "Backlog"], p=status_weights))
        create_time = pd.Timestamp(rng.choice(dates)) + pd.Timedelta(hours=int(rng.integers(8, 19)))
        base_hours = task_base[task_type] * team_factor[team] * priority_factor[priority]
        noise = float(rng.normal(0, 8))
        process_hours = round(max(2.0, base_hours + noise), 2)
        sla_hours = sla_by_priority[priority]
        close_time = pd.NaT
        if status == "Closed":
            close_time = create_time + pd.Timedelta(hours=float(process_hours))
        rework_probability = 0.08
        if task_type in {"Reconciliation", "Month-end Close"}:
            rework_probability += 0.09
        if team == "GL":
            rework_probability += 0.04
        is_rework = bool(rng.random() < rework_probability)
        rows.append(
            {
                "ticket_id": f"T2025{i:04d}",
                "create_time": create_time,
                "close_time": close_time,
                "team": team,
                "assignee": assignee,
                "task_type": task_type,
                "sla_hours": float(sla_hours),
                "process_hours": float(process_hours),
                "is_rework": is_rework,
                "status": status,
                "priority": priority,
            }
        )

    tickets = pd.DataFrame(rows)
    dirty = tickets.copy()
    dirty = pd.concat([dirty, tickets.iloc[[0, 1, 2, 3, 4]]], ignore_index=True)
    dirty.loc[10:12, "assignee"] = None
    dirty.loc[20, "close_time"] = dirty.loc[20, "create_time"] - pd.Timedelta(hours=3)
    dirty.loc[21, "process_hours"] = -5.0
    dirty.loc[22, "status"] = "Done?"
    dirty.loc[23, "priority"] = "Urgent"
    dirty.loc[24, "process_hours"] = 999.0
    dirty.loc[25, "create_time"] = pd.NaT
    dirty.loc[26, "team"] = "Unknown"

    return {"tickets": tickets, "tickets_dirty": dirty, "task_dim": task_dim, "assignee_dim": assignee_dim}


def table_fields(table_name: str) -> list[dict[str, str]]:
    if table_name in {"tickets", "tickets_dirty"}:
        return FIELD_DICTIONARY
    if table_name == "task_dim":
        return TASK_DIM_FIELDS
    if table_name == "assignee_dim":
        return ASSIGNEE_DIM_FIELDS
    return []


def records_for_json(df: pd.DataFrame, limit: int = 20) -> list[dict[str, object]]:
    sample = df.head(limit).copy()
    for col in sample.columns:
        if pd.api.types.is_datetime64_any_dtype(sample[col]):
            sample[col] = sample[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    sample = sample.replace({np.nan: None, pd.NaT: None})
    return json.loads(sample.to_json(orient="records", force_ascii=False))


def dataset_preview(table_names: list[str], limit: int = 12) -> dict[str, list[dict[str, object]]]:
    datasets = get_datasets()
    return {name: records_for_json(datasets[name], limit=limit) for name in table_names}

