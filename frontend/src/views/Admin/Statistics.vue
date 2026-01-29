<script setup>
import { ref, onMounted } from 'vue'
import api from '../../utils/api'

const loading = ref(true)
const datasets = ref([])
const selectedDataset = ref(null)
const dateRange = ref([])
const dailyStats = ref([])
const userStats = ref([])

onMounted(async () => {
  await loadDatasets()
  await loadStatistics()
})

async function loadDatasets() {
  try {
    const response = await api.get('/datasets')
    datasets.value = response.data
  } catch (error) {
    console.error(error)
  }
}

async function loadStatistics() {
  loading.value = true
  try {
    const params = {}
    if (selectedDataset.value) {
      params.dataset_id = selectedDataset.value
    }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const [dailyRes, userRes] = await Promise.all([
      api.get('/admin/statistics/daily', { params: { days: 30, ...params } }),
      api.get('/admin/statistics/users', { params })
    ])

    dailyStats.value = dailyRes.data
    userStats.value = userRes.data
  } finally {
    loading.value = false
  }
}

function handleFilter() {
  loadStatistics()
}

async function handleExport(format) {
  try {
    const params = { format }
    if (selectedDataset.value) {
      params.dataset_id = selectedDataset.value
    }
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    if (format === 'csv') {
      const response = await api.get('/admin/statistics/export', {
        params,
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = 'statistics.csv'
      link.click()
      window.URL.revokeObjectURL(url)
    } else {
      const response = await api.get('/admin/statistics/export', { params })
      console.log(response.data)
    }
  } catch (error) {
    console.error(error)
  }
}
</script>

<template>
  <div class="statistics-page" v-loading="loading">
    <div class="page-header">
      <h2>工作量统计</h2>
      <div class="filters">
        <el-select v-model="selectedDataset" placeholder="全部数据集" clearable @change="handleFilter">
          <el-option
            v-for="ds in datasets"
            :key="ds.id"
            :label="ds.name"
            :value="ds.id"
          />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          @change="handleFilter"
        />
        <el-dropdown @command="handleExport">
          <el-button type="primary">
            导出 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
              <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 每日统计图表 -->
    <div class="chart-section">
      <h3>每日标注趋势（近30天）</h3>
      <div class="chart-placeholder">
        <el-table :data="dailyStats" max-height="300">
          <el-table-column prop="date" label="日期" width="120" />
          <el-table-column prop="images_labeled" label="标注图片数" />
          <el-table-column prop="annotations_created" label="标注框数" />
          <el-table-column label="图表">
            <template #default="{ row }">
              <div class="mini-bar">
                <div
                  class="bar"
                  :style="{ width: `${Math.min(row.images_labeled * 2, 100)}%` }"
                ></div>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 用户统计 -->
    <div class="user-stats-section">
      <h3>用户工作量排行</h3>
      <el-table :data="userStats">
        <el-table-column type="index" label="排名" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="images_labeled" label="标注图片数">
          <template #default="{ row }">
            <span class="value">{{ row.images_labeled }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="annotations_created" label="标注框数">
          <template #default="{ row }">
            <span class="value">{{ row.annotations_created }}</span>
          </template>
        </el-table-column>
        <el-table-column label="贡献度">
          <template #default="{ row }">
            <el-progress
              :percentage="userStats.length > 0
                ? Math.round(row.images_labeled / Math.max(...userStats.map(u => u.images_labeled)) * 100)
                : 0"
              :stroke-width="12"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.statistics-page {
  background: white;
  padding: 24px;
  border-radius: 8px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-header h2 {
  margin: 0;
}

.filters {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.chart-section,
.user-stats-section {
  margin-bottom: 32px;
}

.chart-section h3,
.user-stats-section h3 {
  margin-bottom: 16px;
  color: #333;
}

.mini-bar {
  width: 100%;
  height: 16px;
  background: #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
}

.mini-bar .bar {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 8px;
}

.value {
  font-weight: bold;
  color: #409eff;
}
</style>
