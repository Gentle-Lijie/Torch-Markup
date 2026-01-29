# Torch-Markup

<p align="center">
  <img src="docs/images/logo.png" alt="Torch-Markup Logo" width="200">
</p>

<p align="center">
  <strong>轻量级图像数据标注平台</strong><br>
  支持多种 YOLO 格式导出，专为目标检测数据集制作设计
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Vue-3.x-brightgreen" alt="Vue 3">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-blue" alt="FastAPI">
  <img src="https://img.shields.io/badge/MySQL-8.0+-orange" alt="MySQL">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>


---

## 功能预览

| 管理后台仪表盘 | 标注界面 |
|:---:|:---:|
|![dashboard](/Users/LijieZhou/Development/torch-markup/docs/dashboard.png)| ![label1](https://p.ipic.vip/z172zz.png) |

| 数据集管理 | 工作量统计 |
|:---:|:---:|
| ![export](https://p.ipic.vip/u09xyl.png) | ![workload](https://p.ipic.vip/cp76sa.png) |

---


---

## 功能特性

### 已实现功能

#### 用户系统
- [x] 用户注册/登录（JWT 认证）
- [x] 管理员/普通用户角色区分
- [x] 用户管理（添加、禁用、删除、重置密码）
- [x] 会话管理（退出时自动清除 Token）

#### 数据集管理
- [x] 创建数据集（指定图片目录）
- [x] 自动扫描导入图片
- [x] 数据集激活/停用
- [x] 数据集统计信息

#### 类别管理
- [x] 添加/编辑/删除标注类别
- [x] 自定义类别颜色
- [x] 自定义快捷键
- [x] 类别排序

#### 标注功能
- [x] Canvas 画布标注
- [x] 绘制矩形边界框
- [x] 调整边界框大小
- [x] 删除边界框
- [x] 画布缩放/平移
- [x] 图片自动分配机制
- [x] 保存/跳过操作
- [x] 标注进度显示

#### 数据导出
- [x] **YOLOv5/v7/v8 格式** (Ultralytics)
- [x] **YOLO Darknet 格式** (v3/v4)
- [x] **COCO JSON 格式**
- [x] 自定义训练/验证/测试集比例
- [x] 可选包含未标注图片

#### 统计功能
- [x] 整体统计概览
- [x] 每日标注量统计
- [x] 用户工作量排行
- [x] 统计数据导出 (CSV/JSON)

### 计划开发功能

#### 标注增强
- [ ] 撤销/重做功能
- [ ] 标注历史记录
- [ ] 快捷键帮助面板
- [ ] 图片上一张/下一张导航
- [ ] 标注框复制/粘贴
- [ ] 标注框微调（键盘方向键）
- [ ] 自动保存

#### 数据增强
- [ ] 图片旋转标注
- [ ] 图片翻转
- [ ] 亮度/对比度调整预览
- [ ] 数据增强导出选项

#### AI 辅助
- [ ] 预标注功能（接入 YOLO 模型）
- [ ] 智能标注建议
- [ ] 自动标注审核

#### 协作功能
- [ ] 标注任务分配
- [ ] 标注质量审核
- [ ] 评论/反馈系统
- [ ] 实时协作

#### 其他
- [ ] 多语言支持 (i18n)
- [ ] 深色模式
- [ ] 移动端适配
- [ ] 视频标注支持
- [ ] 语义分割标注
- [ ] 关键点标注
- [ ] WebSocket 实时通知
- [ ] 第三方登录 (OAuth)

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Vite + Element Plus + Pinia |
| **后端** | Python 3.10+ + FastAPI + PyMySQL |
| **数据库** | MySQL 8.0+ |
| **认证** | JWT (python-jose + bcrypt) |

---

## 项目结构

```
torch-markup/
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── router/         # 路由配置
│   │   └── utils/          # 工具函数
│   └── package.json
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── core/           # 核心配置（数据库、认证）
│   │   ├── routers/        # API 路由
│   │   └── main.py         # 应用入口
│   └── requirements.txt
├── database/
│   └── init.sql            # 数据库初始化脚本
├── demo/                    # 演示数据集
├── docs/                    # 文档和截图
│   └── images/             # README 截图
├── dev.sh                   # 开发启动脚本
├── CLAUDE.md               # 开发规范
└── README.md
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+

### 方式一：一键启动（推荐）

```bash
# 1. 初始化数据库
mysql -u root -p < database/init.sql

# 2. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env 文件，设置数据库密码

# 3. 一键启动
./dev.sh
```

启动后：
- 前端: http://localhost:5173
- 后端: http://localhost:8000
- API 文档: http://localhost:8000/docs

按 `Ctrl+C` 停止服务并自动清除所有登录状态。

### 方式二：手动启动

#### 1. 数据库初始化

```bash
mysql -u root -p < database/init.sql
```

#### 2. 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 DATABASE_URL

# 启动服务
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 3. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 默认账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | 123456 |

---

## 部署指南

### Docker 部署（推荐）

```yaml
# docker-compose.yml
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: your_password
      MYSQL_DATABASE: torch_markup
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "3306:3306"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: mysql+pymysql://root:your_password@mysql:3306/torch_markup
      SECRET_KEY: your-production-secret-key
    ports:
      - "8000:8000"
    depends_on:
      - mysql

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  mysql_data:
```

### 手动部署

#### 后端部署 (Gunicorn + Uvicorn)

```bash
cd backend
pip install gunicorn

# 启动
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### 前端部署 (Nginx)

```bash
cd frontend
npm run build

# 将 dist 目录部署到 Nginx
```

Nginx 配置示例：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/torch-markup/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `mysql+pymysql://root:123456@localhost:3306/torch_markup` |
| `SECRET_KEY` | JWT 密钥（生产环境请更换） | `your-super-secret-key` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间(分钟) | `1440` |
| `CORS_ORIGINS` | 允许的跨域来源 | `["http://localhost:5173"]` |

---

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+S` | 保存当前标注 |
| `N` | 跳过当前图片（无目标） |
| `Ctrl+Z` | 撤销 |
| `Ctrl+Shift+Z` | 重做 |
| `Delete` / `Backspace` | 删除选中的框 |
| `滚轮` | 缩放画布 |
| `空格+拖动` | 平移画布 |
| `1-9` / 自定义键 | 切换类别 |

---

## 导出格式说明

### YOLOv5/v7/v8 (Ultralytics)

```
dataset/
├── data.yaml           # 配置文件
├── images/
│   ├── train/         # 训练图片
│   ├── val/           # 验证图片
│   └── test/          # 测试图片
└── labels/
    ├── train/         # 训练标签 (.txt)
    ├── val/
    └── test/

# 标签格式 (归一化坐标 0-1)
class_id x_center y_center width height
```

### YOLO Darknet (v3/v4)

```
dataset/
├── classes.names       # 类别名称
├── dataset.data        # 配置文件
├── train.txt          # 训练图片路径列表
├── val.txt
├── test.txt
├── images/            # 所有图片
└── labels/            # 所有标签
```

### COCO JSON

```
dataset/
├── annotations/
│   ├── instances_train.json
│   ├── instances_val.json
│   └── instances_test.json
├── train/             # 训练图片
├── val/
└── test/
```

---

## 截图需求清单

请截取以下页面的截图，保存到 `docs/images/` 目录：

| 文件名 | 页面 | 说明 |
|--------|------|------|
| `logo.png` | - | 项目 Logo (200x200) |
| `dashboard.png` | `/admin` | 管理后台仪表盘 |
| `annotation.png` | `/annotate/1` | 标注界面（显示图片和标注框） |
| `datasets.png` | `/admin/datasets` | 数据集管理页面 |
| `categories.png` | `/admin/categories/1` | 类别管理页面 |
| `users.png` | `/admin/users` | 用户管理页面 |
| `statistics.png` | `/admin/statistics` | 统计页面 |
| `export.png` | `/admin/export` | 数据导出页面 |
| `login.png` | `/login` | 登录页面 |
| `home.png` | `/` | 首页（数据集列表） |

---

## API 文档

启动后端后访问 http://localhost:8000/docs 查看完整的 Swagger API 文档。

主要 API 端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/register` | 用户注册 |
| GET | `/api/datasets` | 获取数据集列表 |
| POST | `/api/datasets` | 创建数据集 |
| POST | `/api/datasets/{id}/scan` | 扫描导入图片 |
| GET | `/api/images/next/{dataset_id}` | 获取下一张待标注图片 |
| POST | `/api/images/{id}/save` | 保存标注 |
| POST | `/api/export` | 导出数据集 |
| GET | `/api/admin/users` | 获取用户列表 |
| GET | `/api/admin/statistics/overview` | 获取统计概览 |

---

## 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

请遵循 [CLAUDE.md](CLAUDE.md) 中的开发规范。

---

## License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 致谢

- [Vue.js](https://vuejs.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Element Plus](https://element-plus.org/)
- [Ultralytics YOLO](https://docs.ultralytics.com/)