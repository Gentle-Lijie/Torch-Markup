<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnnotationStore } from '../stores/annotation'
import { ElMessage, ElMessageBox } from 'element-plus'
import AnnotationCanvas from '../components/AnnotationCanvas.vue'
import api from '../utils/api'

const route = useRoute()
const router = useRouter()
const store = useAnnotationStore()

const datasetId = computed(() => parseInt(route.params.datasetId))
const progress = ref(null)
const showHelp = ref(false)

onMounted(async () => {
  await loadData()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  store.reset()
})

async function loadData() {
  try {
    await store.loadCategories(datasetId.value)
    await store.fetchNextImage(datasetId.value)
    await loadProgress()
  } catch (error) {
    ElMessage.error('加载数据失败')
  }
}

async function loadProgress() {
  try {
    const response = await api.get(`/images/dataset/${datasetId.value}/progress`)
    progress.value = response.data
  } catch (error) {
    console.error('Failed to load progress', error)
  }
}

async function handleSave() {
  try {
    await store.saveAnnotations(false)
    ElMessage.success('保存成功')
    await store.fetchNextImage(datasetId.value)
    await loadProgress()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

async function handleSkip() {
  try {
    await store.saveAnnotations(true)
    ElMessage.info('已跳过')
    await store.fetchNextImage(datasetId.value)
    await loadProgress()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

function handleKeydown(e) {
  // 忽略输入框中的按键
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
    return
  }

  const key = e.key.toLowerCase()

  // 快捷键
  switch (key) {
    case 's':
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault()
        handleSave()
      }
      break
    case 'n':
      handleSkip()
      break
    case 'z':
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault()
        if (e.shiftKey) {
          store.redo()
        } else {
          store.undo()
        }
      }
      break
    case '?':
      showHelp.value = !showHelp.value
      break
    case 'escape':
      showHelp.value = false
      break
    default:
      // 数字或字母快捷键选择类别
      store.selectCategoryByKey(key)
  }
}

function selectCategory(category) {
  store.selectedCategory = category
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="annotation-container">
    <!-- 顶部工具栏 -->
    <header class="toolbar">
      <div class="left">
        <el-button @click="goBack" :icon="'ArrowLeft'">返回</el-button>
        <span class="image-info" v-if="store.currentImage">
          {{ store.currentImage.filename }}
          <span v-if="store.currentImage.width">
            ({{ store.currentImage.width }} x {{ store.currentImage.height }})
          </span>
        </span>
      </div>
      <div class="center">
        <el-button-group>
          <el-button @click="store.undo()" :disabled="!store.canUndo" :icon="'RefreshLeft'">
            撤销
          </el-button>
          <el-button @click="store.redo()" :disabled="!store.canRedo" :icon="'RefreshRight'">
            重做
          </el-button>
        </el-button-group>
      </div>
      <div class="right">
        <el-button @click="showHelp = true" :icon="'QuestionFilled'">帮助</el-button>
        <el-button @click="handleSkip" type="warning">跳过 (N)</el-button>
        <el-button @click="handleSave" type="primary">保存 (Ctrl+S)</el-button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 左侧类别面板 -->
      <aside class="category-panel">
        <h3>类别选择</h3>
        <div class="category-list">
          <div
            v-for="category in store.categories"
            :key="category.id"
            class="category-item"
            :class="{ active: store.selectedCategory?.id === category.id }"
            @click="selectCategory(category)"
          >
            <span class="color-dot" :style="{ background: category.color }"></span>
            <span class="name">{{ category.name }}</span>
            <span class="shortcut" v-if="category.shortcut_key">
              {{ category.shortcut_key }}
            </span>
          </div>
        </div>

        <div class="annotations-list" v-if="store.annotations.length > 0">
          <h3>当前标注 ({{ store.annotations.length }})</h3>
          <div
            v-for="(ann, index) in store.annotations"
            :key="ann.id"
            class="annotation-item"
          >
            <span class="index">#{{ index + 1 }}</span>
            <span class="category">
              {{ store.categories.find(c => c.id === ann.category_id)?.name || '未知' }}
            </span>
            <el-button
              type="danger"
              size="small"
              :icon="'Delete'"
              circle
              @click="store.removeAnnotation(ann.id)"
            />
          </div>
        </div>
      </aside>

      <!-- 画布区域 -->
      <div class="canvas-container">
        <div v-if="store.isLoading" class="loading-overlay">
          <el-icon class="is-loading" :size="48"><Loading /></el-icon>
        </div>

        <div v-else-if="!store.currentImage" class="empty-state">
          <el-empty description="没有更多图片需要标注">
            <el-button type="primary" @click="goBack">返回首页</el-button>
          </el-empty>
        </div>

        <AnnotationCanvas
          v-else
          :image-id="store.currentImage.id"
          :annotations="store.annotations"
          :categories="store.categories"
          :selected-category="store.selectedCategory"
          @add="store.addAnnotation"
          @update="store.updateAnnotation"
          @delete="store.removeAnnotation"
        />
      </div>

      <!-- 右侧进度面板 -->
      <aside class="progress-panel">
        <h3>标注进度</h3>
        <div v-if="progress" class="progress-info">
          <el-progress
            type="circle"
            :percentage="progress.progress"
            :width="120"
          />
          <div class="stats">
            <div class="stat-row">
              <span>总计:</span>
              <span>{{ progress.total }}</span>
            </div>
            <div class="stat-row">
              <span>已标注:</span>
              <span class="success">{{ progress.labeled }}</span>
            </div>
            <div class="stat-row">
              <span>已跳过:</span>
              <span class="warning">{{ progress.skipped }}</span>
            </div>
            <div class="stat-row">
              <span>待处理:</span>
              <span class="info">{{ progress.pending }}</span>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <!-- 快捷键帮助弹窗 -->
    <el-dialog v-model="showHelp" title="快捷键帮助" width="500px">
      <div class="help-content">
        <table class="shortcuts-table">
          <tr>
            <td><kbd>Ctrl</kbd> + <kbd>S</kbd></td>
            <td>保存当前标注</td>
          </tr>
          <tr>
            <td><kbd>N</kbd></td>
            <td>跳过当前图片（无目标）</td>
          </tr>
          <tr>
            <td><kbd>Ctrl</kbd> + <kbd>Z</kbd></td>
            <td>撤销</td>
          </tr>
          <tr>
            <td><kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>Z</kbd></td>
            <td>重做</td>
          </tr>
          <tr>
            <td><kbd>Delete</kbd> / <kbd>Backspace</kbd></td>
            <td>删除选中的标注框</td>
          </tr>
          <tr>
            <td><kbd>鼠标滚轮</kbd></td>
            <td>缩放画布</td>
          </tr>
          <tr>
            <td><kbd>空格</kbd> + 拖动</td>
            <td>平移画布</td>
          </tr>
          <tr>
            <td><kbd>1-9</kbd> 或 <kbd>自定义键</kbd></td>
            <td>快速切换类别</td>
          </tr>
          <tr>
            <td><kbd>?</kbd></td>
            <td>显示/隐藏帮助</td>
          </tr>
        </table>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.annotation-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1a1a2e;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #16213e;
  border-bottom: 1px solid #0f3460;
}

.toolbar .left,
.toolbar .center,
.toolbar .right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.image-info {
  color: #a0a0a0;
  font-size: 14px;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.category-panel,
.progress-panel {
  width: 240px;
  padding: 16px;
  background: #16213e;
  overflow-y: auto;
}

.category-panel h3,
.progress-panel h3 {
  color: white;
  margin-bottom: 16px;
  font-size: 14px;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #0f3460;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.category-item:hover {
  background: #1a4a7a;
}

.category-item.active {
  background: #e94560;
}

.color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 10px;
}

.category-item .name {
  flex: 1;
  color: white;
}

.category-item .shortcut {
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  font-size: 12px;
  color: #ccc;
}

.annotations-list {
  margin-top: 24px;
}

.annotation-item {
  display: flex;
  align-items: center;
  padding: 8px;
  background: #0f3460;
  border-radius: 4px;
  margin-bottom: 8px;
}

.annotation-item .index {
  color: #888;
  margin-right: 8px;
}

.annotation-item .category {
  flex: 1;
  color: white;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.loading-overlay,
.empty-state {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(26, 26, 46, 0.9);
}

.loading-overlay .el-icon {
  color: #e94560;
}

.progress-panel .progress-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.stats {
  width: 100%;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  color: #a0a0a0;
  border-bottom: 1px solid #0f3460;
}

.stat-row .success {
  color: #67c23a;
}

.stat-row .warning {
  color: #e6a23c;
}

.stat-row .info {
  color: #409eff;
}

.help-content {
  padding: 16px;
}

.shortcuts-table {
  width: 100%;
  border-collapse: collapse;
}

.shortcuts-table td {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.shortcuts-table td:first-child {
  width: 200px;
}

kbd {
  display: inline-block;
  padding: 2px 6px;
  background: #f5f5f5;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 12px;
}
</style>
