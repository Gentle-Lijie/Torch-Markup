<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import api from '../utils/api'

const router = useRouter()
const userStore = useUserStore()

const datasets = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const response = await api.get('/datasets')
    datasets.value = response.data
  } finally {
    loading.value = false
  }
})

function startAnnotation(datasetId) {
  router.push(`/annotate/${datasetId}`)
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="home-container">
    <header class="header">
      <div class="logo">
        <h1>Torch-Markup</h1>
      </div>
      <div class="user-info">
        <span>{{ userStore.user?.username }}</span>
        <el-button v-if="userStore.isAdmin" type="primary" link @click="router.push('/admin')">
          管理后台
        </el-button>
        <el-button type="primary" link @click="router.push('/tutorial')">
          使用教程
        </el-button>
        <el-button type="danger" link @click="handleLogout">
          退出登录
        </el-button>
      </div>
    </header>

    <main class="main">
      <h2 class="section-title">选择数据集开始标注</h2>

      <div v-loading="loading" class="datasets-grid">
        <div v-if="!loading && datasets.length === 0" class="empty-state">
          <el-empty description="暂无可用数据集">
            <template v-if="userStore.isAdmin">
              <el-button type="primary" @click="router.push('/admin/datasets')">
                创建数据集
              </el-button>
            </template>
          </el-empty>
        </div>

        <div
          v-for="dataset in datasets"
          :key="dataset.id"
          class="dataset-card"
          @click="startAnnotation(dataset.id)"
        >
          <div class="card-header">
            <h3>{{ dataset.name }}</h3>
          </div>
          <div class="card-body">
            <p class="description">{{ dataset.description || '暂无描述' }}</p>
            <div class="stats">
              <div class="stat-item">
                <span class="label">总图片</span>
                <span class="value">{{ dataset.total_images }}</span>
              </div>
              <div class="stat-item">
                <span class="label">已标注</span>
                <span class="value">{{ dataset.labeled_images }}</span>
              </div>
              <div class="stat-item">
                <span class="label">进度</span>
                <span class="value">
                  {{ dataset.total_images > 0
                    ? Math.round(dataset.labeled_images / dataset.total_images * 100)
                    : 0 }}%
                </span>
              </div>
            </div>
            <el-progress
              :percentage="dataset.total_images > 0
                ? Math.round(dataset.labeled_images / dataset.total_images * 100)
                : 0"
              :stroke-width="6"
            />
          </div>
          <div class="card-footer">
            <el-button type="primary" size="small">开始标注</el-button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 32px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.logo h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
}

.section-title {
  margin-bottom: 24px;
  color: #333;
}

.datasets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 60px;
}

.dataset-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.dataset-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.card-header h3 {
  margin: 0;
}

.card-body {
  padding: 20px;
}

.description {
  color: #666;
  margin-bottom: 16px;
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
}

.stat-item .label {
  display: block;
  font-size: 12px;
  color: #999;
}

.stat-item .value {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}

.card-footer {
  padding: 12px 20px;
  border-top: 1px solid #f0f0f0;
  text-align: right;
}
</style>
