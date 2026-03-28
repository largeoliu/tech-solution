import unittest
from pathlib import Path

from tests.skill_validation.helpers import require_all_snippets, require_snippets_in_order


INSTALLATION_PATH = Path(__file__).resolve().parents[2] / "INSTALLATION.md"


def bullet_list_after(text: str, marker: str) -> list[str]:
    start = text.index(marker) + len(marker)
    lines = text[start:].splitlines()
    bullets: list[str] = []
    for line in lines:
        if not line:
            if bullets:
                break
            continue
        if not line.startswith("- "):
            if bullets:
                break
            continue
        bullets.append(line[2:].strip())
    return bullets


class InstallationContractsTests(unittest.TestCase):
    def test_stage_1_routes_from_runtime_not_project_directories(self) -> None:
        installation = INSTALLATION_PATH.read_text(encoding="utf-8")

        require_snippets_in_order(
            self,
            installation,
            [
                "### Stage 1: 识别当前助手并解析目标目录",
                "`assistant_id` 只能来自当前 AI 助手宿主或运行时环境。",
                "不能根据项目里是否存在 `.qoder/`、`.trae/`、`.claude/` 等目录推断当前助手。",
                "若无法唯一识别当前助手，则停止安装并输出诊断。",
            ],
        )

    def test_project_target_registry_includes_exact_supported_assistants(self) -> None:
        installation = INSTALLATION_PATH.read_text(encoding="utf-8")

        expected_registry = [
            "`claude -> .claude/skills`",
            "`qoder -> .qoder/skills`",
            "`lingma -> .lingma/skills`",
            "`trae -> .trae/skills`",
            "`generic -> .agents/skills`",
        ]

        require_all_snippets(self, installation, expected_registry)

        registry_entries = bullet_list_after(installation, "当 `scope=project` 时，映射必须严格为：")
        self.assertEqual(
            registry_entries,
            expected_registry,
        )

    def test_conflicts_and_acceptance_examples_fail_fast(self) -> None:
        installation = INSTALLATION_PATH.read_text(encoding="utf-8")

        require_all_snippets(
            self,
            installation,
            [
                "如果宿主显式信号与宿主特征识别结果冲突，也必须停止安装。",
                "`Trae runtime + existing .qoder/ -> .trae/skills`",
                "`Qoder runtime + existing .trae/ -> .qoder/skills`",
                "`unrecognized runtime + multiple assistant directories -> fail without guessing`",
            ],
        )


if __name__ == "__main__":
    unittest.main()
