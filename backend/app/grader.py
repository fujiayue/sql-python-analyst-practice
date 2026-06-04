from __future__ import annotations

from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from .data import get_datasets, records_for_json
from .tasks import TaskSpec


def _execute_sql(sql: str, table_names: tuple[str, ...]) -> pd.DataFrame:
    con = duckdb.connect(database=":memory:")
    datasets = get_datasets()
    try:
        for name in table_names:
            con.register(name, datasets[name])
        return con.execute(sql).fetchdf()
    finally:
        con.close()


def _sort_frame(df: pd.DataFrame, sort_by: tuple[str, ...]) -> pd.DataFrame:
    out = df.copy()
    if sort_by and all(col in out.columns for col in sort_by):
        ascending = [False if col.endswith("_cnt") or col.endswith("_hours") or col.endswith("_rate") and col not in {"month"} else True for col in sort_by]
        out = out.sort_values(list(sort_by), ascending=ascending, kind="mergesort")
    elif len(out.columns) > 0:
        out = out.sort_values(list(out.columns), kind="mergesort")
    return out.reset_index(drop=True)


def _coerce_for_compare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        elif pd.api.types.is_bool_dtype(out[col]):
            out[col] = out[col].astype(bool)
        elif pd.api.types.is_numeric_dtype(out[col]):
            out[col] = pd.to_numeric(out[col], errors="coerce")
        else:
            out[col] = out[col].astype("object")
    return out


def _compare_frames(user_df: pd.DataFrame, expected_df: pd.DataFrame, sort_by: tuple[str, ...]) -> dict[str, Any]:
    if list(user_df.columns) != list(expected_df.columns):
        return {
            "passed": False,
            "error_type": "column_mismatch",
            "feedback": f"列名不一致。需要 {list(expected_df.columns)}，你返回的是 {list(user_df.columns)}。",
            "hint": "先确保 SELECT 或 DataFrame 返回列名、列顺序完全对齐。",
        }
    user = _coerce_for_compare(_sort_frame(user_df, sort_by))
    expected = _coerce_for_compare(_sort_frame(expected_df, sort_by))
    if len(user) != len(expected):
        return {
            "passed": False,
            "error_type": "row_count_mismatch",
            "feedback": f"行数不一致。需要 {len(expected)} 行，你返回 {len(user)} 行。",
            "hint": "检查筛选条件、GROUP BY 粒度、JOIN 是否造成重复或丢失。",
        }
    for col in expected.columns:
        left = user[col]
        right = expected[col]
        if pd.api.types.is_numeric_dtype(right):
            left_num = pd.to_numeric(left, errors="coerce").to_numpy(dtype=float)
            right_num = pd.to_numeric(right, errors="coerce").to_numpy(dtype=float)
            if not np.allclose(left_num, right_num, equal_nan=True, atol=1e-4, rtol=1e-4):
                return {
                    "passed": False,
                    "error_type": "value_mismatch",
                    "feedback": f"字段 {col} 的数值不一致。",
                    "hint": "检查聚合口径、分母、是否只统计 Closed 工单，以及小数保留规则。",
                }
        else:
            left_values = left.where(pd.notna(left), "__NA__").astype(str).to_list()
            right_values = right.where(pd.notna(right), "__NA__").astype(str).to_list()
            if left_values != right_values:
                return {
                    "passed": False,
                    "error_type": "value_mismatch",
                    "feedback": f"字段 {col} 的文本或日期值不一致。",
                    "hint": "检查日期格式、排序字段、枚举筛选和字符串别名。",
                }
    return {
        "passed": True,
        "error_type": None,
        "feedback": "通过。结果列、行数和关键数值都对齐。",
        "hint": "现在把这个结果翻译成业务语言：发现、可能原因、建议动作。",
    }


def grade_sql(task: TaskSpec, code: str) -> dict[str, Any]:
    try:
        user_df = _execute_sql(code, task.datasets)
    except Exception as exc:
        return {
            "passed": False,
            "error_type": "sql_error",
            "feedback": str(exc),
            "hint": "先看报错位置；常见问题是字段名、逗号、GROUP BY 列和日期函数。",
            "result": {"columns": [], "rows": []},
        }
    expected_df = _execute_sql(task.solution, task.datasets)
    comparison = _compare_frames(user_df, expected_df, task.sort_by)
    return {
        **comparison,
        "result": {"columns": list(user_df.columns), "rows": records_for_json(user_df, limit=50)},
    }


def _run_python(code: str, table_names: tuple[str, ...], timeout_seconds: int = 5) -> tuple[pd.DataFrame | None, str | None]:
    datasets = get_datasets()
    with tempfile.TemporaryDirectory(prefix="exam_trainer_") as temp_dir:
        temp_path = Path(temp_dir)
        input_files = []
        for name in table_names:
            file_path = temp_path / f"{name}.csv"
            datasets[name].to_csv(file_path, index=False)
            input_files.append(str(file_path))
        solution_path = temp_path / "user_solution.py"
        solution_path.write_text(code, encoding="utf-8")
        runner_path = temp_path / "runner.py"
        runner_path.write_text(
            textwrap.dedent(
                """
                import importlib.util
                import json
                from pathlib import Path
                import sys

                import pandas as pd

                files = json.loads(Path("inputs.json").read_text(encoding="utf-8"))
                spec = importlib.util.spec_from_file_location("user_solution", "user_solution.py")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if not hasattr(module, "solve"):
                    raise AttributeError("没有找到 solve 函数，请定义 solve(df) 或 solve(df1, df2)。")

                frames = []
                for file_name in files:
                    df = pd.read_csv(file_name)
                    for col in ["create_time", "close_time"]:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors="coerce")
                    frames.append(df)

                result = module.solve(*frames)
                if isinstance(result, pd.Series):
                    result = result.reset_index()
                elif isinstance(result, dict):
                    result = pd.DataFrame([result])
                elif not isinstance(result, pd.DataFrame):
                    result = pd.DataFrame(result)

                print(result.to_json(orient="split", date_format="iso", force_ascii=False))
                """
            ).strip(),
            encoding="utf-8",
        )
        (temp_path / "inputs.json").write_text(json.dumps(input_files), encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        process = subprocess.run(
            [sys.executable, str(runner_path)],
            cwd=temp_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
            env=env,
        )
        if process.returncode != 0:
            return None, process.stderr.strip() or process.stdout.strip()
        try:
            return pd.read_json(StringIO(process.stdout), orient="split"), None
        except Exception as exc:
            return None, f"无法解析 solve 返回结果：{exc}"


def grade_python(task: TaskSpec, code: str) -> dict[str, Any]:
    try:
        user_df, error = _run_python(code, task.datasets)
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "error_type": "timeout",
            "feedback": "代码运行超时。",
            "hint": "检查是否有死循环，或是否对 DataFrame 做了不必要的逐行循环。",
            "result": {"columns": [], "rows": []},
        }
    if error or user_df is None:
        return {
            "passed": False,
            "error_type": "python_error",
            "feedback": error or "Python 代码运行失败。",
            "hint": "先让 solve 返回 DataFrame；注意字段名、缩进、导入 pandas 和日期转换。",
            "result": {"columns": [], "rows": []},
        }
    expected_df, expected_error = _run_python(task.solution, task.datasets)
    if expected_error or expected_df is None:
        return {
            "passed": False,
            "error_type": "internal_solution_error",
            "feedback": expected_error or "标准答案运行失败。",
            "hint": "这是题库内部问题。",
            "result": {"columns": list(user_df.columns), "rows": records_for_json(user_df, limit=50)},
        }
    comparison = _compare_frames(user_df, expected_df, task.sort_by)
    return {
        **comparison,
        "result": {"columns": list(user_df.columns), "rows": records_for_json(user_df, limit=50)},
    }


def grade_submission(task: TaskSpec, code: str) -> dict[str, Any]:
    if task.mode == "sql":
        return grade_sql(task, code)
    if task.mode == "python":
        return grade_python(task, code)
    return {
        "passed": False,
        "error_type": "unsupported_mode",
        "feedback": f"暂不支持的题型：{task.mode}",
        "hint": "请选择 SQL 或 Python 题。",
        "result": {"columns": [], "rows": []},
    }


def score_conclusion(text: str) -> dict[str, Any]:
    content = text.strip()
    checks = [
        ("发现", any(word in content for word in ["发现", "显示", "上升", "下降", "高于", "低于", "集中", "主要"])),
        ("原因假设", any(word in content for word in ["原因", "可能", "由于", "导致", "说明", "推测"])),
        ("建议动作", any(word in content for word in ["建议", "优先", "进一步", "应该", "可以", "需要"])),
        ("关键指标", any(word in content for word in ["SLA", "sla", "%", "返工", "积压", "处理时长", "工单", "环比"]) or any(ch.isdigit() for ch in content)),
    ]
    passed = [name for name, ok in checks if ok]
    missing = [name for name, ok in checks if not ok]
    score = len(passed)
    return {
        "score": score,
        "max_score": len(checks),
        "passed": score >= 3,
        "passed_items": passed,
        "missing_items": missing,
        "feedback": "结论结构可用。" if score >= 3 else "结论还不够像业务输出。",
        "hint": "建议用三句话：发现了什么；原因可能是什么；下一步建议做什么。" if missing else "可以继续补充影响范围和优先级。",
    }

