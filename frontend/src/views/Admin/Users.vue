<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../utils/api'

const users = ref([])
const loading = ref(true)
const resetDialogVisible = ref(false)
const selectedUser = ref(null)
const newPassword = ref('')

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
</script>

<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
    </div>

    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="email" label="邮箱" width="200" show-overflow-tooltip>
        <template #default="{ row }">
          {{ row.email || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="角色" width="100">
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
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            :type="row.is_active ? 'warning' : 'success'"
            @click="toggleUserStatus(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button
            size="small"
            @click="toggleAdminStatus(row)"
          >
            {{ row.is_admin ? '取消管理员' : '设为管理员' }}
          </el-button>
          <el-button size="small" @click="showResetDialog(row)">重置密码</el-button>
          <el-button size="small" type="danger" @click="handleDeleteUser(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

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
</style>
