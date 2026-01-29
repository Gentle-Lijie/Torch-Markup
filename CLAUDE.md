# Torch-Markup 开发规范

## 项目概述

Torch-Markup 是一个图像数据标注平台，支持 YOLO 格式数据集的管理和标注。

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus + Pinia
- **后端**: Python 3.10+ + FastAPI + SQLAlchemy + Pydantic
- **数据库**: MySQL 8.0+

## 项目结构

```
torch-markup/
├── frontend/           # Vue 3 前端
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── components/ # 通用组件
│   │   ├── stores/     # Pinia 状态管理
│   │   ├── router/     # Vue Router 配置
│   │   └── utils/      # 工具函数
│   └── vite.config.js
├── backend/            # FastAPI 后端
│   ├── app/
│   │   ├── core/       # 配置、数据库、安全
│   │   ├── models/     # SQLAlchemy 模型
│   │   ├── routers/    # API 路由
│   │   └── services/   # 业务逻辑
│   └── requirements.txt
├── database/
│   └── init.sql        # 数据库初始化
└── start.sh            # 一键启动脚本
```

## 开发命令

```bash
# 启动所有服务
./start.sh

# 停止服务
./start.sh stop

# 查看状态
./start.sh status

# 查看日志
./start.sh logs
```

## 后端开发规范

### API 路由

- 路由文件位于 `backend/app/routers/`
- 使用 RESTful 风格
- 统一使用 `/api` 前缀
- 认证路由: `/api/auth/*`
- 管理路由: `/api/admin/*` (需要管理员权限)

### 数据模型

- 模型定义位于 `backend/app/models/`
- 使用 SQLAlchemy ORM
- 表名使用复数形式 (users, datasets, images)
- 必须包含 `id` 主键和时间戳字段

### 认证

- 使用 JWT Token 认证
- Token 有效期 24 小时
- 获取当前用户: `Depends(get_current_user)`
- 获取管理员: `Depends(get_current_admin)`

## 前端开发规范

### 组件命名

- 页面组件使用 PascalCase: `Login.vue`, `Annotation.vue`
- 通用组件使用 PascalCase: `AnnotationCanvas.vue`

### 状态管理

- Store 文件位于 `frontend/src/stores/`
- 使用 Pinia Composition API 风格
- 用户状态: `useUserStore`
- 标注状态: `useAnnotationStore`

### API 调用

- 统一使用 `src/utils/api.js` 中的 axios 实例
- 自动携带 Token
- 错误统一在拦截器中处理

## 数据库规范

### 表结构

- `users` - 用户表
- `datasets` - 数据集表
- `categories` - 类别表
- `images` - 图片表
- `annotations` - 标注表
- `annotation_history` - 标注历史
- `work_statistics` - 工作量统计

### 字段命名

- 使用 snake_case
- 外键: `{table}_id` (如 `dataset_id`)
- 时间戳: `created_at`, `updated_at`
- 布尔值: `is_*` (如 `is_admin`, `is_active`)

## YOLO 格式

标注使用 YOLO 格式存储:
```
class_id x_center y_center width height
```
- 所有坐标归一化到 0-1 范围
- `x_center`, `y_center` 是边界框中心点
- `width`, `height` 是边界框宽高

## 快捷键

标注页面支持以下快捷键:
- `Ctrl+S` - 保存
- `N` - 跳过 (无目标)
- `Ctrl+Z` - 撤销
- `Ctrl+Shift+Z` - 重做
- `Delete` - 删除选中框
- `滚轮` - 缩放
- `空格+拖动` - 平移

## 默认账户

- 管理员: `admin / 123456`
