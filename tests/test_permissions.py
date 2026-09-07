from permissions import change_permission

# 普通成员操作被拒绝，权限保持不变。
result = change_permission("member", "read", "write")
assert result == {"success": False, "permission": "read"}

# owner 操作成功，权限变为 write。
result = change_permission("owner", "read", "write")
assert result == {"success": True, "permission": "write"}

print("两个权限场景均通过")