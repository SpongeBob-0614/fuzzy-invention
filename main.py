"""读取需求，调用模型生成结构化计划，并检查和保存计划。"""

import argparse
from pathlib import Path

import yaml
import json
import os
from urllib.request import Request, urlopen

def read_requirements(directory):
    """YAML 文件中的对象会变成 Python dict，列表会变成 list。"""
    path = directory / "requirements.yaml"
    requirement = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(requirement, dict) or requirement.get("id") != "ROOT":
        raise ValueError("需求文件需要 id: ROOT 的根节点")
    modules = requirement.get("children")
    if not isinstance(modules, list) or not modules:
        raise ValueError("ROOT.children 需要至少一个功能模块")
    for module in modules:
        if not isinstance(module, dict) or not all(
            isinstance(module.get(key), str) and module[key].strip() for key in ("id", "name")
        ):
            raise ValueError("每个功能模块需要非空的 id 和 name")
    return requirement


def call_model(prompt):
    """发送一次模型请求并返回回答文本；未正常结束时抛出错误。"""
    payload = {
        "model": "deepseek-v4-flash",
        "messages": [{"role": "user", "content": prompt}],
        "thinking": {"type": "disabled"},
        "response_format": {"type": "json_object"},
        "max_tokens": 1500,
        "stream": False,
    }

    request = Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"],
            "Content-Type": "application/json",
        },
        method="POST",
    )

    print("正在调用 DeepSeek...")
    with urlopen(request, timeout=60) as response:
        result = json.load(response)

    choice = result["choices"][0]
    print("模型回答:", choice["message"]["content"])
    print("结束原因:", choice["finish_reason"])
    if choice["finish_reason"] != "stop":
        raise RuntimeError(
            "模型回答未正常完成，结束原因：" + choice["finish_reason"]
        )
    return choice["message"]["content"]


def main():
    parser = argparse.ArgumentParser(description="第 01 步：读取需求文件")
    parser.add_argument("requirement_dir", type=Path, help="包含 requirements.yaml 的目录")
    args = parser.parse_args()
    try:
        requirement = read_requirements(args.requirement_dir)
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.exit(2, "读取失败: {}\n".format(error))

    print("主题:", requirement.get("name", "未命名"))
    print("功能模块（文件顺序）:")
    for module in requirement["children"]:
        print("- {}: {}".format(module["id"], module["name"]))
        for scenario in module.get("scenarios", []):
            print("  验收场景:", scenario["name"])

    module = requirement["children"][0]

    prompt = (
        "根据下面的需求和验收场景，列出实现步骤，暂时不要写代码。\n"
        "只返回 JSON，不要 Markdown 代码块或额外解释。\n"
        '格式：{"module_id": "...", "steps": [{"id": 1, "description": "..."}]}\n'
        "module_id 必须与需求的 id 一致；steps 是非空列表，步骤编号从 1 开始。\n\n"
        + yaml.safe_dump(module, allow_unicode=True, sort_keys=False)
    )

    print("\n准备发给模型的内容：")
    print(prompt)

    content = call_model(prompt)
    plan = json.loads(content)

    if not isinstance(plan, dict) or plan.get("module_id") != module["id"]:
        raise ValueError("计划的 module_id 与当前需求不一致")

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("steps 必须是非空列表")

    for number, step in enumerate(steps, start=1):
        if not isinstance(step, dict) or type(step.get("id")) is not int or step["id"] != number:
            raise ValueError("步骤 id 必须是从 1 开始的连续整数")

        description = step.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("每个步骤需要非空的 description")

    plan_path = Path("runs/permissions-plan.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("计划已保存:", plan_path)


if __name__ == "__main__":
    main()
