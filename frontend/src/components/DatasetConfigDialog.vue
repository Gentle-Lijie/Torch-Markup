<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../utils/api'

const props = defineProps({
  modelValue: Boolean,
  datasetId: Number,
  datasetName: String
})

const emit = defineEmits(['update:modelValue', 'saved'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const saving = ref(false)
const config = ref({
  format_type: 'yolo',
  annotation_path: '',
  source_width: 1920,
  source_height: 1080,
  auto_import_annotations: true
})

const formatOptions = [
  { value: 'yolo', label: 'YOLO 格式' },
  { value: 'dji_roco', label: 'DJI ROCO 格式' }
]

watch(() => props.modelValue, async (val) => {
  if (val && props.datasetId) {
    await loadConfig()
  }
})

async function loadConfig() {
  loading.value = true
  try {
    const response = await api.get(`/dataset-configs/${props.datasetId}`)
    config.value = {
      format_type: response.data.format_type || 'yolo',
      annotation_path: response.data.annotation_path || '',
      source_width: response.data.source_width || 1920,
      source_height: response.data.source_height || 1080,
      auto_import_annotations: response.data.auto_import_annotations ?? true
    }
  } catch (error) {
    console.error('加载配置失败', error)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    await api.post('/dataset-configs/', {
      dataset_id: props.datasetId,
      ...config.value
    })
    ElMessage.success('配置保存成功')
    emit('saved')
    visible.value = false
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleImportCategories() {
  try {
    const response = await api.post(`/dataset-configs/${props.datasetId}/import-default-categories`)
    ElMessage.success(response.data.message)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  }
}

async function handleImportAnnotations() {
  try {
    const response = await api.post(`/dataset-configs/${props.datasetId}/import-annotations`)
    ElMessage.success(response.data.message)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  }
}
</script>

<template>
  <el-dialog
    v-model="visible"
    :title="`数据集配置 - ${datasetName}`"
    width="500px"
  >
    <div v-loading="loading" class="config-form">
      <el-form label-width="120px">
        <el-form-item label="数据格式">
          <el-select v-model="config.format_type" style="width: 100%">
            <el-option
              v-for="opt in formatOptions"
              :key="opt.value"
              :value="opt.value"
              :label="opt.label"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="标注目录" v-if="config.format_type === 'dji_roco'">
          <el-input
            v-model="config.annotation_path"
            placeholder="留空则自动查找 image_annotation 目录"
          />
        </el-form-item>

        <el-form-item label="原始宽度" v-if="config.format_type === 'dji_roco'">
          <el-input-number v-model="config.source_width" :min="1" />
        </el-form-item>

        <el-form-item label="原始高度" v-if="config.format_type === 'dji_roco'">
          <el-input-number v-model="config.source_height" :min="1" />
        </el-form-item>

        <el-form-item label="自动导入标注" v-if="config.format_type === 'dji_roco'">
          <el-switch v-model="config.auto_import_annotations" />
        </el-form-item>

        <el-divider v-if="config.format_type === 'dji_roco'" />

        <div v-if="config.format_type === 'dji_roco'" class="action-buttons">
          <el-button @click="handleImportCategories">
            导入默认类别
          </el-button>
          <el-button @click="handleImportAnnotations">
            导入现有标注
          </el-button>
        </div>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSave">
        保存配置
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.config-form {
  min-height: 200px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
}
</style>
