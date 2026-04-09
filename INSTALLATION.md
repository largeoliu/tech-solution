## 安装步骤

### Stage 1: 安装 skills 到目标目录

目标目录为 `.agents/skills`。

必须将仓库 `skills/` 目录下当前存在的全部一级 skill 目录完整复制到目标目录；这些目录共同构成当前 canonical skills 集合。

不要只复制后续将要执行的某一个 skill。

Stage 1 不保留安装备份。

Stage 1 仅替换仓库当前 canonical skills 的同名目录，不对目标目录中的额外 skill 做全量同步。

若目标目录中存在与 canonical skills 同名的目录，必须先删除整个旧目录，再复制新目录，避免旧文件残留。

目标目录中额外残留的旧 skill 目录不会删除；若发现这类目录，必须显式报告，供后续人工清理或单独同步。

执行以下指令：

```bash
TARGET=".agents/skills"
mkdir -p "$TARGET"
tmp_root="$(mktemp -d)"
trap 'rm -rf "$tmp_root"' EXIT
git clone https://github.com/largeoliu/tech-solution.git "$tmp_root/tech-solution"

canonical_skills=""

for skill_dir in "$tmp_root"/tech-solution/skills/*; do
  [ -d "$skill_dir" ] || continue
  skill_name="$(basename "$skill_dir")"
  canonical_skills="$canonical_skills $skill_name"
  rm -rf "$TARGET/$skill_name"
  cp -r "$skill_dir" "$TARGET/"
  [ -f "$TARGET/$skill_name/SKILL.md" ] || (echo "Missing $skill_name/SKILL.md" && exit 1)
  echo "已替换 canonical skill: $skill_name"
done

for existing_dir in "$TARGET"/*; do
  [ -d "$existing_dir" ] || continue
  skill_name="$(basename "$existing_dir")"
  case " $canonical_skills " in
    *" $skill_name "*) continue ;;
  esac
  echo "发现额外 skill（保留未删除）: $skill_name"
done

trap - EXIT
rm -rf "$tmp_root"
```

### Stage 2: 在同一次流程内转入项目初始化

确认 Stage 1 已将 `skills/` 下当前全部一级 skill 目录安装到目标目录后，继续读取并执行本地 `bootstrap-architecture` 的初始化流程，不要等待用户追加输入。

`INSTALLATION.md` 是外部安装入口，不是 Skill。它的职责止于完成安装并转入初始化。

这里指定的是安装完成后的下一步执行入口，不是 Stage 1 的安装范围。

必须基于以下目录下的文件完成当前项目初始化：

- `"$TARGET/bootstrap-architecture"`

完成标准：

- 生成 `.architecture/members.yml`，且成员集合反映当前项目所需的关键专家覆盖；当默认模板不足时，结果中包含新增的项目特有专家
- 生成 `.architecture/principles.md`
- 自动创建 `.architecture/templates/` 并将默认模板写入 `.architecture/templates/technical-solution-template.md`
- 仅当以上三个产物都已落盘时，初始化才算完成
- 如需替换默认模板，在初始化完成后显式调用 `manage-technical-solution-template`；安装入口本身不在中途询问用户是否定制模板
