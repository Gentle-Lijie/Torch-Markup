<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../utils/api'

const router = useRouter()

const datasets = ref([])
const loading = ref(true)
const dialogVisible = ref(false)
const dialogTitle = ref('创建数据集')
const isEdit = ref(false)

const form = ref({
  id: null,
  name: '',
  description: '',
  image_path: '',
  label_path: ''
})

onMounted(() => {
  loadDatasets()
})

async function loadDatasets() {
  loading.value = true
  try {
    const response = await api.get('/datasets')
    datasets.value = response.data
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  dialogTitle.value = '创建数据集'
  form.value = {
    id: null,
    name: '',
    description: '',
    image_path: '',
    label_path: ''
  }
  dialogVisible.value = true
}

function showEditDialog(dataset) {
  isEdit.value = true
  dialogTitle.value = '编辑数据集'
  form.value = { ...dataset }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name || !form.value.image_path) {
    ElMessage.warning('请填写必填字段')
    return
  }

  try {
    if (isEdit.value) {
      await api.put(`/datasets/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/datasets', form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadDatasets()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

async function handleScan(dataset) {
  try {
    const response = await api.post(`/datasets/${dataset.id}/scan`)
    ElMessage.success(`扫描完成: 发现${response.data.found_images}张图片, 导入${response.data.imported_images}张, 跳过${response.data.skipped_images}张`)
    loadDatasets()
  } catch (error) {
    // 错误已在拦截器中处理
  }
}

async function handleDelete(dataset) {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据集 "${dataset.name}" 吗？这将删除所有相关的图片和标注数据。`,
      '警告',
      { type: 'warning' }
    )

    await api.delete(`/datasets/${dataset.id}`)
    ElMessage.success('删除成功')
    loadDatasets()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已在拦截器中处理
    }
  }
}

function goToCategories(datasetId) {
  router.push(`/admin/categories/${datasetId}`)
}
</script>

<template>
  <div class="datasets-page">
    <div class="page-header">
      <h2>数据集管理</h2>
      <el-button type="primary" @click="showCreateDialog" :icon="'Plus'">
        创建数据集
      </el-button>
    </div>

    <el-table :data="datasets" v-loading="loading" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="image_path" label="图片路径" show-overflow-tooltip />
      <el-table-column prop="total_images" label="图片数" width="100" />
      <el-table-column prop="labeled_images" label="已标注" width="100" />
      <el-table-column label="进度" width="120">
        <template #default="{ row }">
          <el-progress
            :percentage="row.total_images > 0 ? Math.round(row.labeled_images / row.total_images * 100) : 0"
            :stroke-width="6"
          />
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="goToCategories(row.id)">类别</el-button>
          <el-button size="small" type="primary" @click="handleScan(row)">扫描</el-button>
          <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="数据集名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="数据集描述" />
        </el-form-item>
        <el-form-item label="图片路径" required>
          <el-input v-model="form.image_path" placeholder="/path/to/images" />
          <div class="form-tip">服务器上的图片目录绝对路径</div>
        </el-form-item>
        <el-form-item label="标签路径">
          <el-input v-model="form.label_path" placeholder="/path/to/labels" />
          <div class="form-tip">YOLO标签保存目录（可选）</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.datasets-page {
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

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
</style>
