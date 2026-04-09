# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "tabulate>=0.9", "pytest>=8.0"]
# ///
"""create-technical-solution Eval Runner。

读取用例定义，在独立测试项目中验证 create-technical-solution skill 行为。
用例与测试环境分离，不随 skill 分发。

用法：
    # 列出现有用例
    python3 evals/create-technical-solution/eval_runner.py list

    # 初始化测试项目（一次性）
    python3 evals/create-technical-solution/eval_runner.py setup-project

    # 生成测试 fixture
    python3 evals/create-technical-solution/eval_runner.py fixture T01
    python3 evals/create-technical-solution/eval_runner.py fixture --all

    # 在目标项目中运行 skill 后，检查结果
    python3 evals/create-technical-solution/eval_runner.py grade T01
    python3 evals/create-technical-solution/eval_runner.py grade T01 --state .architecture/.state/.../xxx.yaml

    # 生成报告
    python3 evals/create-technical-solution/eval_runner.py report
    python3 evals/create-technical-solution/eval_runner.py report --format json

    # validate-state.py 单元测试
    python3 evals/create-technical-solution/eval_runner.py test-validate
"""

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    print("缺少 pyyaml。运行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    from tabulate import tabulate
except ImportError:
    def tabulate(data, headers=None, tablefmt=None):
        """Fallback tabulate"""
        if headers:
            print(" | ".join(str(h) for h in headers))
        for row in data:
            print(" | ".join(str(v) for v in row))
        return ""

EVAL_DIR = Path(__file__).parent
CASE_FILE = EVAL_DIR / "cases" / "T01.json"
TESTS_DIR = EVAL_DIR / "tests"
FIXTURES_DIR = EVAL_DIR / "fixtures"
REPORTS_DIR = EVAL_DIR / "reports"
DEFAULT_TARGET = Path(__file__).resolve().parents[2] / "tests" / "sample-project"

SKILL_ROOT = Path(__file__).resolve().parents[2] / "skills" / "create-technical-solution"
VALIDATE_SCRIPT = SKILL_ROOT / "scripts" / "validate-state.py"
STATE_TEMPLATE_PATH = SKILL_ROOT / "templates" / "_template.yaml"


def load_state_template() -> dict:
    template = yaml.safe_load(STATE_TEMPLATE_PATH.read_text(encoding="utf-8")) or {}
    if not isinstance(template, dict):
        raise ValueError(f"状态模板格式无效: {STATE_TEMPLATE_PATH}")
    return template


def load_cases() -> list[dict]:
    with open(CASE_FILE) as f:
        return json.load(f)


def find_case(cases: list[dict], case_id: str) -> dict | None:
    for c in cases:
        for tag in c.get("tags", []):
            if tag == case_id or tag.startswith(f"{case_id.lower()}-"):
                return c
        slug = c.get("query", "")[:30]
        if case_id.replace("-", "").lower() in slug.lower():
            return c
    first_match = next((c for c in cases if case_id.lower() in json.dumps(c, ensure_ascii=False).lower()), None)
    return first_match


def load_test_case_file(case_id: str) -> list[dict]:
    """从 eval/tests/ 读取 assertion 定义"""
    test_files = {
        "T01": "T01-full-新增订单支付模块.md",
        "T02": "T02-light-单模块小改动.md",
        "T03": "T03-moderate-鉴权重构.md",
        "T04": "T04-full-repowiki-多租户数据隔离.md",
        "T05": "T05-moderate-repowiki-不存在-缓存层.md",
        "T06": "T06-full-服务拆分.md",
        "E01": "E01-边缘-单成员.md",
        "E02": "E02-边缘-主题模糊.md",
        "E03": "E03-边缘-前置文件缺失.md",
        "E04": "E04-边缘-slug-冲突.md",
        "E05": "E05-边缘-WD-EXP-字段缺失.md",
        "E06": "E06-边缘-WD-EXP-字段缺失.md",
        "D01": "D01-D04-描述边界.md",
        "D02": "D01-D04-描述边界.md",
        "D03": "D01-D04-描述边界.md",
        "D04": "D01-D04-描述边界.md",
        "N01": "N01-N06-负向用例.md",
        "N02": "N01-N06-负向用例.md",
        "N03": "N01-N06-负向用例.md",
        "N04": "N01-N06-负向用例.md",
        "N05": "N01-N06-负向用例.md",
        "N06": "N01-N06-负向用例.md",
    }
    fname = test_files.get(case_id)
    if not fname:
        return []
    path = TESTS_DIR / fname
    if not path.exists():
        return []
    content = path.read_text()
    assertions = []
    for line in content.split("\n"):
        if "|" in line and ("skill-revealing" in line or "baseline" in line):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6:
                assertions.append({
                    "id": parts[1],
                    "type": parts[2],
                    "description": parts[3],
                    "pass_criteria": parts[4],
                    "fail_condition": parts[5],
                })
    return assertions


def cmd_list(cases: list[dict]) -> None:
    """列出所有用例"""
    data = []
    for i, c in enumerate(cases):
        tags = c.get("tags", [])
        data.append([
            f"T{i+1:02d}",
            c.get("query", "")[:50],
            ", ".join(tags),
        ])
    print(tabulate(data, headers=["ID", "Query", "Tags"], tablefmt="grid"))
    print(f"\n总计: {len(cases)} 条用例")


def cmd_setup_project(path: str | None = None) -> None:
    """初始化 .architecture/ 测试项目"""
    target = Path(path) if path else DEFAULT_TARGET
    target = target.resolve()
    arch = target / ".architecture"
    arch.mkdir(parents=True, exist_ok=True)
    (arch / "templates").mkdir(exist_ok=True)
    (arch / ".state" / "create-technical-solution").mkdir(parents=True, exist_ok=True)
    (arch / "technical-solutions").mkdir(exist_ok=True)
    (target / "src").mkdir(exist_ok=True)

    # members.yml
    members_file = arch / "members.yml"
    if not members_file.exists():
        members_file.write_text("""members:
  - slug: architect
    name: 系统架构师
    role: system-architect
    skills: [api-design, database, deployment]
  - slug: backend-dev
    name: 后端工程师
    role: backend-developer
    skills: [api, microservices]
  - slug: frontend-dev
    name: 前端工程师
    role: frontend-developer
    skills: [ui, frontend]
  - slug: security-expert
    name: 安全专家
    role: security-specialist
    skills: [auth, encryption, audit]
""")

    # principles.md
    principles_file = arch / "principles.md"
    if not principles_file.exists():
        principles_file.write_text("# 架构原则\n<!-- 由 bootstrap-architecture 初始化 -->\n")

    # technical-solution-template.md
    template_file = arch / "templates" / "technical-solution-template.md"
    if not template_file.exists():
        template_file.write_text(
            "# 技术方案文档\n\n## 一、背景\n\n### 1.1 需求概述\n\n### 1.2 核心目标\n\n## 二、设计\n\n### 2.1 方案设计\n\n### 2.2 风险与验证\n",
            encoding="utf-8",
        )

    # src/__init__.py
    init_file = target / "src" / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")

    print(f"测试项目已初始化: {target}")
    print(f"  {members_file}  {'已创建' if not any(members_file.exists() for _ in [1]) else '已存在'}")
    print(f"  {principles_file}")
    print(f"  {template_file}")
    print(f"\n在该项目中运行 create-technical-solution skill 后，使用 grade 命令检查。")


def cmd_fixture(cases: list[dict], case_id: str, all_cases: bool = False) -> None:
    """生成测试 fixture"""
    FIXTURES_DIR.mkdir(exist_ok=True)

    cases_to_run = cases if all_cases else [c for c in cases if find_case(cases, case_id) == c]
    if not all_cases:
        target = find_case(cases, case_id)
        if target:
            cases_to_run = [target]
        else:
            print(f"未找到用例: {case_id}", file=sys.stderr)
            sys.exit(1)

    for case in cases_to_run:
        slug = case.get("query", "unknown")[:40].strip().lower().replace(" ", "-")
        state_template = copy.deepcopy(load_state_template())
        fixture = {
            "case_id": f"T{cases.index(case)+1:02d}" if case in cases else "unknown",
            "query": case.get("query", ""),
            "expected_flow_tier": case.get("expected_behavior", [{}])[0] if case.get("expected_behavior") else "",
            "expected_behaviors": case.get("expected_behavior", []),
            "tags": case.get("tags", []),
            "files_required": case.get("files", []),
            "notes": case.get("notes", ""),
            "fixture_created_at": datetime.now().isoformat(),
            "state_template": state_template,
            "status": "pending",
            "actual_flow_tier": None,
            "actual_behaviors": [],
            "assertion_results": {},
        }

        fname = f"{fixture['case_id']}_{slug}.json"
        fpath = FIXTURES_DIR / fname
        fpath.write_text(json.dumps(fixture, indent=2, ensure_ascii=False))
        print(f"Fixture 已生成: {fpath}")

        # 打印 setup 指令
        print(f"\n--- 执行步骤 ---")
        print(f"1. 不带 skill 执行 query: \"{case['query']}\"")
        print(f"2. 记录 baseline 输出")
        print(f"3. 带 create-technical-solution skill 执行相同 query")
        print(f"4. 记录 with_skill 输出")
        print(f"5. 运行: eval_runner.py grade {fixture['case_id']} --state <状态文件路径>")
        print(f"6. 运行: eval_runner.py report")
        print()


def cmd_grade(cases: list[dict], case_id: str = None, all_cases: bool = False, state_path: str = None, target: Path = None) -> None:
    """检查执行结果"""
    results = {}

    # 如果未指定状态文件路径，尝试从目标项目自动查找
    if target and not state_path:
        import glob as glob_mod
        state_dir = target / ".architecture" / ".state" / "create-technical-solution"
        if state_dir.exists():
            state_files = sorted(glob_mod.glob(str(state_dir / "*.yaml")))
            if state_files:
                state_path = state_files[-1]
                print(f"自动检测到状态文件: {state_path}")

    if state_path:
        import subprocess
        try:
            state_data = yaml.safe_load(Path(state_path).read_text(encoding="utf-8")) or {}
            tier = state_data.get("flow_tier") or "full"
            step = int(state_data.get("current_step") or 12)
            if state_data.get("can_enter_step_12") or state_data.get("final_document_path"):
                step = 12
            cmd = [sys.executable, str(VALIDATE_SCRIPT), "--state", state_path, "--step", str(step), "--flow-tier", tier, "--format", "json"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if proc.returncode == 0:
                results["validate_state"] = {"passed": True, "message": f"状态文件门禁通过（step={step}, tier={tier}）"}
            elif proc.returncode == 2:
                output = json.loads(proc.stdout) if proc.stdout else {}
                results["validate_state"] = {
                    "passed": False,
                    "step": step,
                    "flow_tier": tier,
                    "issues": output.get("issues", []),
                    "repair_plan": output.get("repair_plan", []),
                }
            else:
                results["validate_state"] = {"passed": False, "message": proc.stderr}
        except Exception as e:
            results["validate_state"] = {"passed": False, "error": str(e)}

    # 加载 assertion 定义并评估
    if case_id and not all_cases:
        target = find_case(cases, case_id)
        test_cases_to_check = [target] if target else cases
    else:
        test_cases_to_check = cases

    for case in test_cases_to_check:
        query = case.get("query", "")
        case_short_id = f"T{cases.index(case)+1:02d}" if case in cases else "unknown"
        assertions = load_test_case_file(case_short_id)

        print(f"\n=== {case_short_id}: {query[:60]} ===")
        print(f"预期行为 ({len(case.get('expected_behavior', []))} 条):")
        for i, eb in enumerate(case.get("expected_behavior", []), 1):
            print(f"  [{i}] {eb}")
        print(f"可用 assertion ({len(assertions)} 条):")
        for a in assertions:
            print(f"  [{a['id']}] {a['description']} (类型: {a['type']})")

    REPORTS_DIR.mkdir(exist_ok=True)
    report_data = {
        "graded_at": datetime.now().isoformat(),
        "cases_checked": len(test_cases_to_check),
        "validate_state_results": results,
        "grading_note": "请在 Claude 运行 skill 后提供输出内容以自动评估。当前仅检查了状态文件（如果提供）。",
    }
    report_file = REPORTS_DIR / "grade_results.json"
    report_file.write_text(json.dumps(report_data, indent=2, ensure_ascii=False))
    print(f"\n评判结果已保存: {report_file}")


def cmd_report(fmt: str = "markdown") -> None:
    """生成对比报告"""
    REPORTS_DIR.mkdir(exist_ok=True)

    # 加载所有 fixture
    fixtures = []
    if FIXTURES_DIR.exists():
        for f in sorted(FIXTURES_DIR.glob("*.json")):
            fixtures.append(json.loads(f.read_text()))

    if fmt == "json":
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_cases": len(fixtures),
            "fixtures": fixtures,
            "summary": {
                "pending": sum(1 for f in fixtures if f.get("status") == "pending"),
                "passed": sum(1 for f in fixtures if f.get("status") == "passed"),
                "failed": sum(1 for f in fixtures if f.get("status") == "failed"),
            },
        }
        out_file = REPORTS_DIR / "report.json"
        out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"JSON 报告已生成: {out_file}")
    else:
        lines = [
            "# create-technical-solution Eval 报告",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"\n## 用例统计",
            f"- 总计: {len(fixtures)} 条",
            f"- 待执行: {sum(1 for f in fixtures if f.get('status') == 'pending')}",
            f"- 通过: {sum(1 for f in fixtures if f.get('status') == 'passed')}",
            f"- 未通过: {sum(1 for f in fixtures if f.get('status') == 'failed')}",
            "",
            "## 用例详情",
            "",
        ]

        for f in fixtures:
            lines.append(f"### {f['case_id']}: {f['query'][:60]}")
            lines.append(f"- **状态**: {f.get('status', 'pending')}")
            lines.append(f"- **标签**: {', '.join(f.get('tags', []))}")
            if f.get('expected_flow_tier'):
                lines.append(f"- **预期 tier**: {f['expected_flow_tier']}")
            if f.get('actual_flow_tier'):
                lines.append(f"- **实际 tier**: {f['actual_flow_tier']}")
            lines.append("")

        content = "\n".join(lines)
        out_file = REPORTS_DIR / "report.md"
        out_file.write_text(content)
        print(f"Markdown 报告已生成: {out_file}")
        print()
        print(content)


def cmd_test_validate() -> None:
    """运行 validate-state.py 的单元测试"""
    import subprocess
    import shutil
    script = Path(__file__).parent / "test_validate_state.py"
    print("运行 validate-state.py 单元测试...\n")
    if shutil.which("uv"):
        command = ["uv", "run", "pytest", str(script), "-v"]
    else:
        command = [sys.executable, "-m", "pytest", str(script), "-v"]
    proc = subprocess.run(
        command,
        capture_output=False,
    )
    sys.exit(proc.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="create-technical-solution Eval Runner")
    sub = parser.add_subparsers(dest="command")

    # list
    sub.add_parser("list", help="列出所有用例")

    # setup-project
    p_setup = sub.add_parser("setup-project", help="初始化测试项目")
    p_setup.add_argument("path", nargs="?", default=None, help="目标项目路径")

    # fixture
    p_fix = sub.add_parser("fixture", help="生成测试 fixture")
    p_fix.add_argument("case_id", nargs="?", default=None, help="用例 ID（如 T01）")
    p_fix.add_argument("--target", default=str(DEFAULT_TARGET), help="目标项目路径")
    p_fix.add_argument("--all", action="store_true", help="生成所有 fixture")

    # grade
    p_gr = sub.add_parser("grade", help="检查执行结果")
    p_gr.add_argument("case_id", nargs="?", default=None, help="用例 ID")
    p_gr.add_argument("--target", default=str(DEFAULT_TARGET), help="目标项目路径")
    p_gr.add_argument("--state", default=None, help="状态文件路径（不指定则自动查找）")
    p_gr.add_argument("--all", action="store_true", help="评判所有用例")

    # report
    p_rep = sub.add_parser("report", help="生成对比报告")
    p_rep.add_argument("--format", choices=["markdown", "json"], default="markdown")

    # test-validate
    sub.add_parser("test-validate", help="运行 validate-state.py 单元测试")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cases = load_cases()

    if args.command == "list":
        cmd_list(cases)
    elif args.command == "setup-project":
        cmd_setup_project(args.path)
    elif args.command == "fixture":
        cmd_fixture(cases, args.case_id, args.all)
    elif args.command == "grade":
        target = Path(args.target)
        cmd_grade(cases, args.case_id, args.all, args.state, target)
    elif args.command == "report":
        cmd_report(args.format)
    elif args.command == "test-validate":
        cmd_test_validate()


if __name__ == "__main__":
    main()
