

<h1>数字人流式直播</h1>

一个基于 GPT-SoVits 等开源tts项目的数字人流式直播项目.<br><br>

---

## 功能特性

1. 基于 GPT-SoVits 等开源tts项目的数字人流式直播
   - 实时语音合成
   - 多种语音风格支持
   - 流式音频输出

2. 基于 MaxKB 知识库问答系统的数字人流式直播
   - 智能问答
   - 知识库管理
   - 上下文理解

3. 基于 大模型 的数字人流式直播
   - 多轮对话
   - 个性化回复
   - 实时互动

## 技术架构

### 前端

- Vue 3 + Vite
- Element Plus UI
- Web Audio API
- WebSocket 实时通信

### 后端

- GPT-SoVits 语音合成
- Swaph Agent 对话引擎
- stream 流式传输文本、音频、视频数据
- MaxKB 知识库系统

## 快速开始

### 环境要求

- Node.js 16+
- Python 3.10+
- CUDA 支持(推荐)

### 安装

1. 克隆项目

```bash
git clone --recursive https://github.com/teatimekon/GPT-SoVITS-Stream
cd GPT-SoVITS-Stream
```

2. 安装前端依赖

```bash
#安装音频前端
cd frontend_audio
npm install

#安装视频前端
cd ../frontend_video
npm install
```

3. 安装后端依赖

```bash
pip install -r requirements.txt
```

4. 启动后端

```bash
python tts_server/shuziren_tts_server_interrupt.py
```

## 使用说明

1. 商品直播
- 填写商品信息
- 选择语音风格
- 生成直播话术
- 开始语音直播

2. 知识问答直播
- 导入知识库
- 开启问答模式
- 接收用户提问
- 实时语音回答

3. 对话直播
- 选择对话模型
- 设置对话风格
- 开启实时对话
- 语音互动交流

## 开源协议

本项目采用 MIT 协议开源。作者不对软件具备任何控制力,使用软件者、传播软件导出的声音者自负全责。如不认可该条款,则不能使用或引用软件包内任何代码和文件。详见根目录 LICENSE。

## 贡献指南

欢迎提交 Issue 和 Pull Request 贡献代码。在贡献之前请先阅读:

1. Issue / PR 模板
2. 代码规范文档
3. 贡献指南

## 致谢

感谢以下开源项目:

- [GPT-SoVits](https://github.com/RVC-Boss/GPT-SoVITS)
- [Swaph](https://github.com/teatimekon/Swaph)
- [UVR5](https://github.com/Anjok07/ultimatevocalremovergui)

</div>