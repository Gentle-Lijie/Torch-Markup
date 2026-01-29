<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import api from '../../utils/api'

const users = ref([])
const loading = ref(true)
const resetDialogVisible = ref(false)
const createDialogVisible = ref(false)
const selectedUser = ref(null)
const newPassword = ref('')
const newUser = ref({
  username: '',
  password: '',
  email: '',
  is_admin: false
})

onMounted(() => {
  loadUsers()
})

async function loadUsers() {
  loading.value = true
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } finally {
    loading.value = false
  }
}

async function toggleUserStatus(user) {
  try {
    await api.put(`/admin/users/${user.id}`, {
      is_active: !user.is_active
    })
    ElMessage.success(user.is_active ? '已禁用' : '已启用')
    loadUsers()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

async function toggleAdminStatus(user) {
  try {
    await ElMessageBox.confirm(
      user.is_admin
        ? `确定要取消 "${user.username}" 的管理员权限吗？`
        : `确定要将 "${user.username}" 设为管理员吗？`,
      '确认',
      { type: 'warning' }
    )

    await api.put(`/admin/users/${user.id}`, {
      is_admin: !user.is_admin
    })
    ElMessage.success('操作成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已在拦截器中处理
    }
  }
}

function showResetDialog(user) {
  selectedUser.value = user
  newPassword.value = ''
  resetDialogVisible.value = true
}

async function handleResetPassword() {
  if (!newPassword.value || newPassword.value.length < 6) {
    ElMessage.warning('密码长度不能少于6位')
    return
  }

  try {
    await api.post(`/admin/users/${selectedUser.value.id}/reset-password`, {
      new_password: newPassword.value
    })
    ElMessage.success('密码重置成功')
    resetDialogVisible.value = false
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

async function handleDeleteUser(user) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '警告',
      { type: 'warning' }
    )

    await api.delete(`/admin/users/${user.id}`)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已在拦截器中处理
    }
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function handleCommand(command, user) {
  if (command === 'toggleAdmin') {
    toggleAdminStatus(user)
  } else if (command === 'delete') {
    handleDeleteUser(user)
  }
}

function showCreateDialog() {
  newUser.value = {
    username: '',
    password: '',
    email: '',
    is_admin: false
  }
  createDialogVisible.value = true
}

async function handleCreateUser() {
  if (!newUser.value.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  if (!newUser.value.password || newUser.value.password.length < 6) {
    ElMessage.warning('密码长度不能少于6位')
    return
  }

  try {
    await api.post('/admin/users', newUser.value)
    ElMessage.success('用户创建成功')
    createDialogVisible.value = false
    loadUsers()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}
</script>

<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreateDialog">添加用户</el-button>
    </div>

    <el-table :data="users" v-loading="loading" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.email || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="角色" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">
            {{ row.is_admin ? '管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'warning'" size="small">
            {{ row.is_active ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="images_labeled" label="标注图片数" width="120" />
      <el-table-column label="注册时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="240">
        <template #default="{ row }">
          <div class="action-buttons">
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" @click="showResetDialog(row)">重置密码</el-button>
            <el-dropdown trigger="click" @command="(cmd) => handleCommand(cmd, row)">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="toggleAdmin">
                    {{ row.is_admin ? '取消管理员' : '设为管理员' }}
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided style="color: #f56c6c">
                    删除用户
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加用户对话框 -->
    <el-dialog v-model="createDialogVisible" title="添加用户" width="450px">
      <el-form :model="newUser" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="newUser.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input
            v-model="newUser.password"
            type="password"
            placeholder="请输入密码（至少6位）"
            show-password
          />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="newUser.email" placeholder="留空则自动生成" />
          <div class="form-tip">留空将自动生成为：用户名@torch-markup.local</div>
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="newUser.is_admin" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateUser">创建</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetDialogVisible" title="重置密码" width="400px">
      <el-form>
        <el-form-item label="用户">
          <span>{{ selectedUser?.username }}</span>
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.users-page {
  background: white;
  padding: 24px;
  border-radius: 8px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
