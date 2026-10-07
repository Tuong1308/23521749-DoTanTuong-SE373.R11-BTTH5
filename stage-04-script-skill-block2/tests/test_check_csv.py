"""csv-quality script: thống kê fixture, tổng giờ/quá tải theo --max-hours, lỗi input/schema/parse exit 1, lỗi dữ liệu exit 0."""

import json
import subprocess
import sys

import pytest

import paths

SCRIPT = paths.FIXTURES_DIR / "skills" / "csv-quality" / "scripts" / "check_csv.py"


def run(path, max_hours="10"):
    args = [sys.executable, str(SCRIPT), "--input", str(path)]
    if max_hours is not None:
        args += ["--max-hours", str(max_hours)]
    return subprocess.run(args, capture_output=True, text=True, timeout=10)


def write_csv(tmp_path, text):
    path = tmp_path / "t.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_fixture_statistics():
    result = run(paths.FIXTURES_DIR / "data" / "tasks.csv")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["row_count"] == 6
    assert data["missing_owner_count"] == 1
    assert data["invalid_hours_count"] == 1
    assert data["duplicate_id_count"] == 1
    assert data["duplicate_ids"] == ["T02"]
    assert [(i["line"], i["column"], i["type"]) for i in data["issues"]] == [
        (4, "owner", "missing_owner"),
        (5, "hours", "invalid_hours"),
        (6, "task_id", "duplicate_id"),
    ]
    assert "total_hours" not in data


@pytest.mark.parametrize("hours", ["NaN", "nan", "Infinity", "-inf", "-1", ""])
def test_non_finite_negative_or_empty_hours_rejected(tmp_path, hours):
    data = json.loads(run(write_csv(tmp_path, f"task_id,owner,hours\nT01,Lan,{hours}\n")).stdout)
    assert data["invalid_hours_count"] == 1
    assert data["issues"][0]["line"] == 2


def test_clean_data_exit_0_without_issues(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\nT02,Minh,2.5\n"))
    assert result.returncode == 0
    assert json.loads(result.stdout)["issues"] == []


def test_missing_file_exit_1(tmp_path):
    result = run(tmp_path / "khong-co.csv")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Không đọc được file" in result.stderr


def test_missing_column_exit_1(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner\nT01,Lan\n"))
    assert result.returncode == 1
    assert "Thiếu cột bắt buộc: hours" in result.stderr


def test_parse_error_exit_1(tmp_path):
    result = run(write_csv(tmp_path, 'task_id,owner,hours\nT01,"La"n,4\n'))
    assert result.returncode == 1
    assert "Lỗi parse CSV" in result.stderr


def test_script_does_not_modify_input():
    source = paths.FIXTURES_DIR / "data" / "tasks.csv"
    before = source.read_bytes()
    run(source)
    assert source.read_bytes() == before


# ---------- Tổng giờ theo owner và người quá tải (--max-hours) ----------

WORKLOAD = paths.FIXTURES_DIR / "data" / "workload.csv"
WORKLOAD_EXCLUDED = [
    {"line": 5, "task_id": "T04", "reasons": ["invalid_hours"]},
    {"line": 6, "task_id": "T02", "reasons": ["duplicate_id"]},
    {"line": 7, "task_id": "T05", "reasons": ["missing_owner"]},
]


def test_workload_threshold_8_lan_overloaded():
    result = run(WORKLOAD, 8)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["max_hours"] == 8
    assert data["hours_by_owner"] == {"Lan": 9, "Minh": 3}
    assert data["overloaded_owners"] == [{"owner": "Lan", "total_hours": 9}]
    assert data["excluded_rows"] == WORKLOAD_EXCLUDED
    # thống kê chất lượng cũ vẫn tính trên mọi dòng
    assert (data["row_count"], data["missing_owner_count"], data["invalid_hours_count"], data["duplicate_ids"]) == (6, 1, 1, ["T02"])


def test_workload_threshold_equal_total_is_not_overloaded():
    data = json.loads(run(WORKLOAD, 9).stdout)
    assert data["hours_by_owner"] == {"Lan": 9, "Minh": 3}
    assert data["overloaded_owners"] == []
    assert data["excluded_rows"] == WORKLOAD_EXCLUDED


def test_first_occurrence_with_invalid_hours_still_wins_duplicate():
    """ID xuất hiện lần đầu với hours sai: loại dòng đó và loại luôn các dòng trùng sau, không cộng giá trị hợp lệ phía sau."""
    result = run(paths.FIXTURES_DIR / "data" / "workload-edge.csv", 0)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["hours_by_owner"] == {"Minh": 0}
    assert "Lan" not in data["hours_by_owner"]
    assert data["overloaded_owners"] == []
    assert data["excluded_rows"] == [
        {"line": 2, "task_id": "E01", "reasons": ["invalid_hours"]},
        {"line": 3, "task_id": "E01", "reasons": ["duplicate_id"]},
    ]


def test_all_reasons_in_fixed_order_and_owner_normalization(tmp_path):
    text = "task_id,owner,hours\n A1 , Lan , 2 \nA2,lan,3\n,,abc\nA1,,x\nA3,Lan\n\nA4,Minh,1.5\n"
    data = json.loads(run(write_csv(tmp_path, text), 2).stdout)
    assert data["hours_by_owner"] == {"Lan": 2, "Minh": 1.5, "lan": 3}  # strip, không gộp khác hoa/thường
    assert data["overloaded_owners"] == [{"owner": "lan", "total_hours": 3}]
    assert data["excluded_rows"] == [
        {"line": 4, "task_id": None, "reasons": ["missing_task_id", "missing_owner", "invalid_hours"]},
        {"line": 5, "task_id": "A1", "reasons": ["duplicate_id", "missing_owner", "invalid_hours"]},
        {"line": 6, "task_id": "A3", "reasons": ["wrong_field_count", "invalid_hours"]},
    ]


def test_missing_max_hours_exit_non_zero():
    result = run(WORKLOAD, None)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "--max-hours" in result.stderr


@pytest.mark.parametrize("value", ["-1", "nan", "inf", "abc", ""])
def test_invalid_max_hours_exit_non_zero(value):
    result = subprocess.run([sys.executable, str(SCRIPT), "--input", str(WORKLOAD), f"--max-hours={value}"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "--max-hours" in result.stderr


def test_missing_file_with_threshold_exit_1(tmp_path):
    result = run(tmp_path / "khong-co.csv", 8)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Không đọc được file" in result.stderr


def test_workload_input_not_modified():
    before = WORKLOAD.read_bytes()
    run(WORKLOAD, 8)
    assert WORKLOAD.read_bytes() == before
