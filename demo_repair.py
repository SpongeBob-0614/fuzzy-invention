"""模拟首次生成出错，再调用一次真实模型修复；产物仍写入 runs/generated。"""

import json
from unittest.mock import patch

import generate_permissions as generator


def main():
    real_call_model = generator.call_model
    call_count = 0

    def demo_call_model(prompt):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            print("演练：首次回答使用故意写错的代码，不调用 DeepSeek。")
            # 故意让普通 member 也能修改权限，触发第一个测试失败。
            return json.dumps({
                "code": (
                    "def change_permission(actor_role, current_permission, new_permission):\n"
                    "    return {'success': True, 'permission': new_permission}\n"
                )
            })

        if call_count == 2:
            print("演练：把失败信息交给 DeepSeek，进行一次修复。")
            return real_call_model(prompt)

        raise RuntimeError("本次演练最多允许生成和修复两个步骤")

    with patch.object(generator, "call_model", side_effect=demo_call_model):
        generator.main()


if __name__ == "__main__":
    main()
