import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../utils/api'

export const useAnnotationStore = defineStore('annotation', () => {
  const currentImage = ref(null)
  const annotations = ref([])
  const categories = ref([])
  const selectedCategory = ref(null)
  const history = ref([])
  const historyIndex = ref(-1)
  const isLoading = ref(false)

  // 计算属性
  const canUndo = computed(() => historyIndex.value > 0)
  const canRedo = computed(() => historyIndex.value < history.value.length - 1)

  // 加载类别
  async function loadCategories(datasetId) {
    const response = await api.get(`/categories/dataset/${datasetId}`)
    categories.value = response.data

    // 如果只有一个类别，自动选中
    if (categories.value.length === 1) {
      selectedCategory.value = categories.value[0]
    }

    return categories.value
  }

  // 获取下一张图片
  async function fetchNextImage(datasetId) {
    isLoading.value = true
    try {
      const response = await api.get(`/images/next/${datasetId}`)
      if (response.data) {
        currentImage.value = response.data
        annotations.value = response.data.annotations || []
        saveHistory()
      } else {
        currentImage.value = null
        annotations.value = []
      }
      return currentImage.value
    } finally {
      isLoading.value = false
    }
  }

  // 获取指定图片
  async function fetchImage(imageId) {
    isLoading.value = true
    try {
      const response = await api.get(`/images/${imageId}`)
      currentImage.value = response.data
      annotations.value = response.data.annotations || []
      saveHistory()
      return currentImage.value
    } finally {
      isLoading.value = false
    }
  }

  // 添加标注
  function addAnnotation(annotation) {
    const newAnnotation = {
      ...annotation,
      id: Date.now(), // 临时ID
      category_id: selectedCategory.value?.id || annotation.category_id
    }
    annotations.value.push(newAnnotation)
    saveHistory()
    return newAnnotation
  }

  // 更新标注
  function updateAnnotation(id, updates) {
    const index = annotations.value.findIndex(a => a.id === id)
    if (index !== -1) {
      annotations.value[index] = { ...annotations.value[index], ...updates }
      saveHistory()
    }
  }

  // 删除标注
  function removeAnnotation(id) {
    const index = annotations.value.findIndex(a => a.id === id)
    if (index !== -1) {
      annotations.value.splice(index, 1)
      saveHistory()
    }
  }

  // 保存历史记录
  function saveHistory() {
    // 如果在历史中间，删除后面的记录
    if (historyIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, historyIndex.value + 1)
    }
    history.value.push(JSON.parse(JSON.stringify(annotations.value)))
    historyIndex.value = history.value.length - 1

    // 限制历史记录数量
    if (history.value.length > 50) {
      history.value.shift()
      historyIndex.value--
    }
  }

  // 撤销
  function undo() {
    if (canUndo.value) {
      historyIndex.value--
      annotations.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
    }
  }

  // 重做
  function redo() {
    if (canRedo.value) {
      historyIndex.value++
      annotations.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
    }
  }

  // 保存标注
  async function saveAnnotations(skip = false) {
    if (!currentImage.value) return

    const annotationsData = annotations.value.map(a => ({
      category_id: a.category_id,
      x_center: a.x_center,
      y_center: a.y_center,
      width: a.width,
      height: a.height
    }))

    await api.post(`/images/${currentImage.value.id}/save`, {
      annotations: annotationsData,
      skip
    })
  }

  // 根据快捷键选择类别
  function selectCategoryByKey(key) {
    const category = categories.value.find(c => c.shortcut_key === key)
    if (category) {
      selectedCategory.value = category
      return category
    }
    return null
  }

  // 清空状态
  function reset() {
    currentImage.value = null
    annotations.value = []
    history.value = []
    historyIndex.value = -1
  }

  return {
    currentImage,
    annotations,
    categories,
    selectedCategory,
    isLoading,
    canUndo,
    canRedo,
    loadCategories,
    fetchNextImage,
    fetchImage,
    addAnnotation,
    updateAnnotation,
    removeAnnotation,
    undo,
    redo,
    saveAnnotations,
    selectCategoryByKey,
    reset
  }
})
