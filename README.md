# Facebook Video Downloader

一个简单高效的 Facebook 视频下载工具，使用 Next.js 和 FastAPI 构建。

## 功能特点

- 简洁现代的用户界面
- 支持下载 Facebook 公开视频
- 实时下载进度显示
- 详细的错误提示
- 跨平台支持
- 自动文件名生成

## 技术栈

### 前端
- Next.js
- TypeScript
- Tailwind CSS
- Fetch API

### 后端
- FastAPI
- Python 3.8+
- BeautifulSoup4
- Requests

## 安装说明

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 启动后端服务器：
```bash
python main.py
```

服务器将在 http://localhost:8001 运行

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动开发服务器：
```bash
npm run dev
```

前端将在 http://localhost:3000 运行

## 使用方法

1. 打开浏览器访问 http://localhost:3000
2. 将 Facebook 视频链接粘贴到输入框中
3. 点击"Get Video"按钮获取视频信息
4. 点击"Download"按钮下载视频

## 注意事项

- 仅支持公开的 Facebook 视频
- 视频大小限制为 500MB
- 需要稳定的网络连接
- 某些视频可能因为 Facebook 的限制无法下载

## 错误处理

- 如果视频无法下载，请检查：
  - 视频链接是否正确
  - 视频是否为公开视频
  - 网络连接是否稳定
  - 视频大小是否超过限制

## 开发说明

### API 端点

- `GET /api/get-video`: 获取视频信息
- `GET /api/download`: 下载视频

### 主要功能实现

- 使用 BeautifulSoup4 解析 Facebook 页面
- 使用内存缓冲区处理视频下载
- 实现了完整的错误处理和日志记录
- 支持 CORS 跨域请求
- 自动清理临时文件

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License
