# Torch-Markup

基于 Vue 3 + FastAPI + MySQL 构建的图像数据标注平台，支持 YOLO 格式数据集的管理和标注。

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus + Pinia
- **后端**: Python 3.10+ + FastAPI + SQLAlchemy + Pydantic
- **数据库**: MySQL 8.0+
- **认证**: JWT (python-jose + bcrypt)

## 项目结构

```
torch-markup/
├── frontend/                # 前端项目
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # 路由配置
│   │   └── utils/          # 工具函数
│   └── package.json
├── backend/                 # 后端项目
│   ├── app/
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据库模型
│   │   ├── routers/        # API 路由
│   │   └── services/       # 业务逻辑
│   └── requirements.txt
└── database/
    └── init.sql            # 数据库初始化脚本
```

## 快速开始

### 1. 数据库初始化

```bash
# 创建数据库并执行初始化脚本
mysql -u root -p < database/init.sql
```

### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (复制示例文件并修改)
cp .env.example .env

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问系统

- 前端: http://localhost:5173
- 后端 API 文档: http://localhost:8000/docs
- 默认管理员账户: admin / 123456

## 主要功能

### 管理后台
- **数据集管理**: 创建、扫描、导入图片目录
- **类别管理**: 添加标注类别，配置快捷键和颜色
- **用户管理**: 用户列表、禁用/启用、重置密码
- **工作量统计**: 每日统计图表、用户排行、数据导出
- **YOLO 导出**: 支持训练/验证/测试集分割

### 标注功能
- **画布操作**: 缩放、平移、框选
- **边界框绘制**: 拖拽绘制、调整大小、删除
- **快捷键支持**: 保存、跳过、撤销/重做、类别切换
- **实时进度**: 显示当前数据集标注进度

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+S | 保存当前标注 |
| N | 跳过当前图片 |
| Ctrl+Z | 撤销 |
| Ctrl+Shift+Z | 重做 |
| Delete | 删除选中的框 |
| 滚轮 | 缩放画布 |
| 空格+拖动 | 平移画布 |
| 1-9/自定义键 | 切换类别 |
| ? | 显示帮助 |

## YOLO 格式

导出的数据集结构：

```
dataset/
├── data.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

标签文件格式：
```
class_id x_center y_center width height
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接字符串 | mysql+pymysql://root:password@localhost:3306/torch_markup |
| SECRET_KEY | JWT 密钥 | your-secret-key |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token 过期时间(分钟) | 1440 |

## License

MIT
