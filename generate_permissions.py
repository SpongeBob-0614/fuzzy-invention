import ast
import json
from pathlib import Path
from main import call_model
import subprocess
import sys


def run_tests(root, output):
    for cache_file in (output.parent / "__pycache__").glob("permissions.*.pyc"):
        cache_file.unlink()

    return subprocess.run(
        [sys.executable, str(root / "tests/test_permissions.py")],
        env={"PYTHONPATH": str(output.parent)},
        capture_output=True,
        text=True,
        timeout=10,
    )

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

    result = run_tests(root, output)

    print("测试退出码:", result.returncode)
    print("测试输出:", result.stdout)
    print("测试错误:", result.stderr)
    if result.returncode != 0:
        repair_prompt = (
            prompt
            + "\n\n上次生成的代码：\n" + code
            + "\n测试退出码：" + str(result.returncode)
            + "\n测试输出：\n" + result.stdout
            + "\n测试报错：\n" + result.stderr
            + "\n请根据测试修复代码，保持函数接口不变，"
            "仍然只返回包含 code 字段的 JSON。"
        )
        print("\n准备发给模型的修复请求：")
        print(repair_prompt)
        repaired_content = call_model(repair_prompt)
        repaired = json.loads(repaired_content)
        if (
            not isinstance(repaired, dict)
            or not isinstance(repaired.get("code"), str)
            or not repaired["code"].strip()
        ):
            raise ValueError("修复回答必须包含非空的 code 字符串")

        repaired_code = repaired["code"]
        ast.parse(repaired_code)
        output.write_text(repaired_code, encoding="utf-8")
        print("修复后的代码已保存:", output)

        result = run_tests(root, output)
        print("复测退出码:", result.returncode)
        print("复测输出:", result.stdout)
        print("复测错误:", result.stderr)

    if result.returncode != 0:
        print("任务失败：修复后测试仍未通过。")
        sys.exit(1)

    print("任务完成：权限测试全部通过。")


if __name__ == "__main__":
    main()
