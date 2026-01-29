<script setup>
import { ref, onMounted } from 'vue'
import api from '../../utils/api'

const stats = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await api.get('/admin/statistics/overview')
    stats.value = response.data
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <h2>仪表盘</h2>

    <div class="stats-grid" v-if="stats">
      <div class="stat-card">
        <div class="icon users">
          <el-icon :size="32"><User /></el-icon>
        </div>
        <div class="info">
          <span class="value">{{ stats.total_users }}</span>
          <span class="label">用户总数</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="icon datasets">
          <el-icon :size="32"><Folder /></el-icon>
        </div>
        <div class="info">
          <span class="value">{{ stats.total_datasets }}</span>
          <span class="label">数据集数量</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="icon images">
          <el-icon :size="32"><Picture /></el-icon>
        </div>
        <div class="info">
          <span class="value">{{ stats.total_images }}</span>
          <span class="label">图片总数</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="icon labeled">
          <el-icon :size="32"><Select /></el-icon>
        </div>
        <div class="info">
          <span class="value">{{ stats.labeled_images }}</span>
          <span class="label">已标注</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="icon pending">
          <el-icon :size="32"><Clock /></el-icon>
        </div>
        <div class="info">
          <span class="value">{{ stats.pending_images }}</span>
          <span class="label">待标注</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="icon annotations">
          <el-icon :size="32"><Aim /></el-icon>
        </div>
        <div class="info">
          <span class="value">{{ stats.total_annotations }}</span>
          <span class="label">标注框总数</span>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <h3>快捷操作</h3>
      <div class="action-buttons">
        <router-link to="/admin/datasets">
          <el-button type="primary" :icon="'Plus'">创建数据集</el-button>
        </router-link>
        <router-link to="/admin/users">
          <el-button :icon="'User'">管理用户</el-button>
        </router-link>
        <router-link to="/admin/statistics">
          <el-button :icon="'PieChart'">查看统计</el-button>
        </router-link>
        <router-link to="/admin/export">
          <el-button :icon="'Download'">导出数据</el-button>
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.dashboard h2 {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-card .icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  color: white;
}

.icon.users { background: linear-gradient(135deg, #667eea, #764ba2); }
.icon.datasets { background: linear-gradient(135deg, #f093fb, #f5576c); }
.icon.images { background: linear-gradient(135deg, #4facfe, #00f2fe); }
.icon.labeled { background: linear-gradient(135deg, #43e97b, #38f9d7); }
.icon.pending { background: linear-gradient(135deg, #fa709a, #fee140); }
.icon.annotations { background: linear-gradient(135deg, #a18cd1, #fbc2eb); }

.stat-card .info {
  display: flex;
  flex-direction: column;
}

.stat-card .value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-card .label {
  color: #999;
  font-size: 14px;
}

.quick-actions {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.quick-actions h3 {
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-buttons a {
  text-decoration: none;
}
</style>
