<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../../utils/api'

const loading = ref(false)
const datasets = ref([])
const exportResult = ref(null)

const form = ref({
  dataset_id: null,
  output_name: '',
  train_ratio: 0.8,
  val_ratio: 0.1,
  test_ratio: 0.1,
  include_unlabeled: false
})

onMounted(async () => {
  try {
    const response = await api.get('/datasets')
    datasets.value = response.data
  } catch (error) {
    console.error(error)
  }
})

async function handleExport() {
  if (!form.value.dataset_id) {
    ElMessage.warning('请选择数据集')
    return
  }

  const total = form.value.train_ratio + form.value.val_ratio + form.value.test_ratio
  if (Math.abs(total - 1) > 0.01) {
    ElMessage.warning('分割比例之和必须为1')
    return
  }

  loading.value = true
  try {
    const response = await api.post('/export/yolo', form.value)
    exportResult.value = response.data
    ElMessage.success('导出成功')
  } catch (error) {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function handleDownload() {
  if (!exportResult.value?.download_url) return

  try {
    const token = localStorage.getItem('token')
    const link = document.createElement('a')
    link.href = exportResult.value.download_url + `?token=${token}`
    link.download = 'dataset.zip'
    link.click()
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

function getDatasetName(id) {
  return datasets.value.find(d => d.id === id)?.name || ''
}
</script>

<template>
  <div class="export-page">
    <div class="page-header">
      <h2>YOLO格式导出</h2>
    </div>

    <div class="export-form">
      <el-form :model="form" label-width="120px">
        <el-form-item label="选择数据集" required>
          <el-select v-model="form.dataset_id" placeholder="请选择数据集" style="width: 300px">
            <el-option
              v-for="ds in datasets"
              :key="ds.id"
              :label="`${ds.name} (${ds.labeled_images}/${ds.total_images})`"
              :value="ds.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="输出名称">
          <el-input
            v-model="form.output_name"
            placeholder="留空则使用数据集名称"
            style="width: 300px"
          />
        </el-form-item>

        <el-form-item label="数据集分割">
          <div class="split-config">
            <div class="split-item">
              <span>训练集</span>
              <el-input-number
                v-model="form.train_ratio"
                :min="0"
                :max="1"
                :step="0.1"
                :precision="1"
              />
            </div>
            <div class="split-item">
              <span>验证集</span>
              <el-input-number
                v-model="form.val_ratio"
                :min="0"
                :max="1"
                :step="0.1"
                :precision="1"
              />
            </div>
            <div class="split-item">
              <span>测试集</span>
              <el-input-number
                v-model="form.test_ratio"
                :min="0"
                :max="1"
                :step="0.1"
                :precision="1"
              />
            </div>
          </div>
        </el-form-item>

        <el-form-item label="包含未标注">
          <el-switch v-model="form.include_unlabeled" />
          <span class="tip">开启后将包含未标注的图片（标签文件为空）</span>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleExport">
            开始导出
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 导出结果 -->
    <div v-if="exportResult" class="export-result">
      <h3>导出完成</h3>
      <div class="result-info">
        <div class="info-grid">
          <div class="info-item">
            <span class="label">数据集</span>
            <span class="value">{{ getDatasetName(form.dataset_id) }}</span>
          </div>
          <div class="info-item">
            <span class="label">类别数</span>
            <span class="value">{{ exportResult.categories }}</span>
          </div>
          <div class="info-item">
            <span class="label">总图片数</span>
            <span class="value">{{ exportResult.total_images }}</span>
          </div>
          <div class="info-item">
            <span class="label">训练集</span>
            <span class="value">{{ exportResult.train_images }}</span>
          </div>
          <div class="info-item">
            <span class="label">验证集</span>
            <span class="value">{{ exportResult.val_images }}</span>
          </div>
          <div class="info-item">
            <span class="label">测试集</span>
            <span class="value">{{ exportResult.test_images }}</span>
          </div>
          <div class="info-item">
            <span class="label">标注框数</span>
            <span class="value">{{ exportResult.total_annotations }}</span>
          </div>
        </div>

        <el-button type="success" size="large" @click="handleDownload" :icon="'Download'">
          下载 ZIP 文件
        </el-button>
      </div>
    </div>

    <!-- 导出格式说明 -->
    <div class="format-info">
      <h3>YOLO格式说明</h3>
      <div class="format-content">
        <pre>
dataset/
├── data.yaml          # 配置文件
├── images/
│   ├── train/        # 训练图片
│   ├── val/          # 验证图片
│   └── test/         # 测试图片
└── labels/
    ├── train/        # 训练标签
    ├── val/          # 验证标签
    └── test/         # 测试标签

# 标签格式 (每行一个目标)
class_id x_center y_center width height
        </pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.export-page {
  background: white;
  padding: 24px;
  border-radius: 8px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
}

.export-form {
  margin-bottom: 32px;
}

.split-config {
  display: flex;
  gap: 24px;
}

.split-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.split-item span {
  font-size: 13px;
  color: #666;
}

.tip {
  margin-left: 12px;
  color: #999;
  font-size: 13px;
}

.export-result {
  padding: 24px;
  background: #f0f9eb;
  border-radius: 8px;
  margin-bottom: 32px;
}

.export-result h3 {
  margin-top: 0;
  color: #67c23a;
}

.result-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-item .label {
  font-size: 12px;
  color: #999;
}

.info-item .value {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.format-info {
  padding: 24px;
  background: #f5f7fa;
  border-radius: 8px;
}

.format-info h3 {
  margin-top: 0;
}

.format-content pre {
  background: #2d2d2d;
  color: #f8f8f2;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
}
</style>
