# 竞赛信息管理系统

基于 Python + Flask + HTML + CSS + JavaScript + SQLite 的前后端分离竞赛信息管理系统。

## 功能特性

- **竞赛管理**: 添加、编辑、删除竞赛信息（官网链接、比赛项目链接）
- **学生管理**: 管理参赛学生信息（姓名、年级、专业、联系方式）
- **数据采集**: 自动采集 https://cpipc.acge.org.cn/ 网站的最新竞赛信息
- **数据可视化**: 仪表盘展示统计数据
- **中文日志**: 系统运行日志全部使用中文（专业名词除外）
- **前后端分离**: RESTful API 接口，支持跨域访问

## 技术栈

- **后端**: Python 3 + Flask + Flask-CORS
- **前端**: HTML5 + CSS3 + JavaScript (原生)
- **数据库**: SQLite
- **数据采集**: requests + BeautifulSoup4 + lxml

## 项目结构

```
G:\竞赛管理系统\
├── backend\              # 后端代码
│   ├── app.py           # Flask主应用
│   ├── database.py      # 数据库模块
│   └── collector.py     # 数据采集模块
├── frontend\            # 前端代码
│   ├── index.html       # 主页面
│   ├── css\
│   │   └── style.css    # 样式文件
│   └── js\
│       └── app.js       # 前端JavaScript
├── data\                # 数据库文件
│   └── competition.db   # SQLite数据库
├── logs\                # 日志目录
├── tests\               # 测试脚本
│   └── test_system.py   # 系统测试
├── venv\                # Python虚拟环境（G盘）
├── requirements.txt     # Python依赖
└── 启动系统.bat         # 启动脚本
```

## 快速开始

### 方式一：使用启动脚本（推荐）

双击运行 `启动系统.bat`

### 方式二：手动启动

```bash
# 进入项目目录
cd G:\竞赛管理系统

# 激活虚拟环境
.\venv\Scripts\activate

# 安装依赖（首次运行）
pip install -r requirements.txt

# 启动系统
python backend\app.py
```

### 访问系统

打开浏览器访问: http://localhost:5000

## API接口

### 健康检查
- `GET /api/health` - 系统健康检查

### 竞赛管理
- `GET /api/competitions` - 获取竞赛列表
- `POST /api/competitions` - 创建竞赛
- `PUT /api/competitions/<id>` - 更新竞赛
- `DELETE /api/competitions/<id>` - 删除竞赛

### 学生管理
- `GET /api/students` - 获取学生列表
- `POST /api/students` - 创建学生
- `PUT /api/students/<id>` - 更新学生
- `DELETE /api/students/<id>` - 删除学生

### 数据采集
- `POST /api/collect` - 触发数据采集
- `GET /api/collected-data` - 获取采集数据

### 统计与日志
- `GET /api/statistics` - 获取统计数据
- `GET /api/logs` - 获取系统日志

## 测试

运行自动化测试：

```bash
cd G:\竞赛管理系统
.\venv\Scripts\activate
python tests\test_system.py
```

测试覆盖：
- 健康检查接口
- 竞赛CRUD操作（正常流程、异常校验）
- 学生CRUD操作（正常流程、异常校验）
- 数据采集功能
- 统计接口
- 日志功能
- 前端页面访问
- 数据库读写
- 边界条件测试
- 异常处理测试

## 数据库表结构

### competitions (竞赛表)
- id: 主键
- name: 竞赛名称
- official_url: 官网链接
- description: 描述
- category: 类别
- status: 状态
- start_date: 开始日期
- end_date: 结束日期

### students (学生表)
- id: 主键
- name: 姓名
- grade: 年级
- major: 专业
- phone: 电话
- email: 邮箱

### student_competitions (学生竞赛关联表)
- id: 主键
- student_id: 学生ID
- competition_id: 竞赛ID
- role: 角色
- progress: 进度
- project_url: 项目链接

### collected_data (采集数据表)
- id: 主键
- title: 标题
- content: 内容
- summary: 摘要
- source_url: 来源链接
- publish_date: 发布日期

### system_logs (系统日志表)
- id: 主键
- level: 日志级别
- message: 日志消息
- module: 模块名称

## 注意事项

1. 虚拟环境位于G盘，不占用C盘空间
2. 所有日志使用中文（专业名词除外）
3. 系统默认端口为5000
4. 数据库文件自动创建在data目录下

## 开发说明

- 前端使用原生JavaScript，无需构建工具
- 后端使用Flask开发模式，支持热重载
- 数据库使用SQLite，无需额外安装数据库服务

## 许可证

MIT License
