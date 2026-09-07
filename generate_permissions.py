import ast
import json
from pathlib import Path
from main import call_model


def main():
    root = Path(__file__).resolve().parent
    plan_text = (root / "runs/permissions-plan.json").read_text(encoding="utf-8")
    tests_text = (root / "tests/test_permissions.py").read_text(encoding="utf-8")

    prompt = (
        "请生成一个 Python 文件，只实现纯函数 "
        "change_permission(actor_role, current_permission, new_permission)。\n"
        "actor_role 为 owner 时，返回 success 为 true、"
        "permission 为 new_permission 的字典；\n"
        "其他角色返回 success 为 false、permission 为 current_permission 的字典。"
        "Python 中请使用 True/False。\n"
        "不要添加文件读写、网络操作、第三方依赖或测试代码。\n"
        '只返回 JSON：{"code": "完整的 Python 源码"}，不要 Markdown 代码块。\n'
        "以下计划仅作背景，本轮只实现上述函数：\n" + plan_text
        + "\n必须满足的测试：\n" + tests_text
    )

    generated = json.loads(call_model(prompt))
    if (
        not isinstance(generated, dict)
        or not isinstance(generated.get("code"), str)
        or not generated["code"].strip()
    ):
        raise ValueError("模型必须返回非空的 code 字符串")

    code = generated["code"]
    ast.parse(code)

    output = root / "runs/generated/permissions.py"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(code, encoding="utf-8")
    print("代码已保存:", output)


if __name__ == "__main__":
    main()