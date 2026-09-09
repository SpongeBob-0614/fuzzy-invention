# fuzzy-invention

在 `codex/agent-learning` 分支上，逐步学习编写初赛 Coding Agent。

主题：GitHub + Spreadsheets 功能复刻，关注 Actions、组织权限、审计和 Rulesets。
这个仓库最终要做的程序，会根据需求生成应用。我们每次只实现一个小步骤。

## 当前进度：生成、测试并修复权限函数

```text
requirements.yaml → 模型生成结构化计划 → 模型生成权限函数 → 自动测试
                                                          ↓ 失败
                                                  修复一次 → 复测
```

- `tasks/github-spreadsheets/requirements.yaml`：第一课的精简需求输入。
- `main.py`：读取 YAML，打印模块，为第一个模块生成计划，校验后保存到 `runs/permissions-plan.json`。
- `generate_permissions.py`：读取计划和测试，生成 `change_permission()`，检查 Python 语法后保存并自动测试；失败时把代码和报错交给模型修复一次，再校验、保存和复测。
- `demo_repair.py`：模拟错误的首次回答，用真实模型进行一次修复，演练完整的失败处理流程。
- `tests/test_permissions.py`：验证普通成员修改被拒绝、owner 修改成功这两个场景。
- `docs/practice-requirements-draft.yaml`：后续练习场景草稿，目前不用阅读或运行。

当前只生成一个纯函数，用输入参数模拟角色和权限，还没有真实组织、登录或数据存储。
输出中的模块顺序就是文件顺序，不表示依赖执行顺序。

## 运行

Python 3.9 或更新版本。在项目目录中执行：

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

在当前终端中设置并导出环境变量 `DEEPSEEK_API_KEY`，不要把密钥写进源码。
程序使用 DeepSeek 的 `deepseek-v4-flash` 模型，不会自动读取 `.env` 文件。

然后在项目目录中依次执行：

```sh
.venv/bin/python main.py tasks/github-spreadsheets
.venv/bin/python generate_permissions.py
```

生成脚本会自动运行两个权限场景。首次通过或修复后通过时，输出
`任务完成：权限测试全部通过。`，脚本退出码为 `0`；修复后仍失败则输出报错并退出 `1`。

`main.py` 调用一次模型；`generate_permissions.py` 调用一次模型生成代码，
测试失败时再调用一次模型修复。测试本身不调用模型。

已有计划后，可以单独演练失败与修复流程：

```sh
.venv/bin/python demo_repair.py
echo $?
```

演练的首次错误回答由本地提供，真实模型只调用一次用于修复。
演练也会更新 `runs/generated/permissions.py`，沿用同一组测试和退出状态。
`runs/` 中的计划和代码是本地生成产物，不提交到 Git；首次使用需要先运行 `main.py` 生成计划。

`yaml.safe_load()` 把 YAML 文本转成 Python 数据：根节点是字典，
`requirement["children"]` 是列表，列表里的每一项又是一个字典。

## 后续逐步加入

1. 保存运行报告，并统一需求读取、生成与测试的运行入口。
2. 扩展需求与验收场景，逐步理解模块依赖顺序。
3. 加入受控的文件读写等工具，生成更完整的应用。
4. 根据届时的平台要求完成适配与提交验证。

## 练习与比赛的边界

这里的需求由我们自己编写，正式需求以比赛平台发布为准。
字段组织参考 [Octos ARC 适配器](https://github.com/octos-org/arc-adapter/tree/b0999c95f7875c8d4ff3e58e733fb2c5abc8caf7)
和 [HAFleet 需求读取实现](https://github.com/onewesong/hafleet-arc/blob/ce14960fc005968e6de0ac9986f3147135eb2f2a/hafleet_arc/requirements.py)。
当前 CLI 是教学入口，尚未实现完整 ARC-Bench 参数、事件协议或产物约定。

后续概念参考：

- [Actions workflows](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows)
- [组织角色](https://docs.github.com/en/organizations/managing-peoples-access-to-your-organization-with-roles/roles-in-an-organization)
- [仓库角色](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization)
- [Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)
- [组织审计](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/reviewing-the-audit-log-for-your-organization)
