# Wake-Up-Service

> 一个跨平台的 MP4 转 MP3 随机音频播放器。

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/Iceclank/Wake-Up-Service)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Auto%20Install-green)](https://ffmpeg.org/)
[![Release](https://img.shields.io/github/v/release/Iceclank/Wake-Up-Service)](https://github.com/Iceclank/Wake-Up-Service/releases)

**起因是学校新搞了个午读，班主任让我中午放音乐把大家叫起来，鉴于我** *~~不想读+起不来~~* **热衷于自动化流程，遂开发此项目交差**

---

## 下载


无需安装 Python，直接下载 Release 中的 **`.exe` 可执行文件**：

[下载最新版本](https://github.com/Iceclank/Wake-Up-Service/releases/latest)

下载后将 `.exe` 文件与 MP4 视频放在同一文件夹下，双击运行即可。

---

## 功能特性

- **全自动格式转换**：启动时自动检测根目录下的 MP4 文件，一键转换为 MP3 并存入 `audio/` 文件夹
- **智能同步**：自动比对 MP4 与 MP3 文件，新增、删除、修改时自动重新转换
- **随机播放**：3 秒文件名滚动动画，随机抽取并播放音频，已播放自动排除不重复
- **启动参数**：支持 `-r` 参数启动后自动开始随机播放
- **音量调节**：内置音量滑块，实时调节播放音量

---

## 快速开始

### 直接运行 exe（Windows）

1. 从 [Releases](https://github.com/Iceclank/Wake-Up-Service/releases) 下载 `Wake-Up-Service.exe`
2. 将 `.exe` 和 MP4 文件放在同一文件夹下
3. 双击运行，程序会自动完成转换和播放

```
文件夹/
├── Wake-Up-Service.exe
├── video_01.mp4
├── video_02.mp4
└── audio/              # 自动生成
```
---

## 使用说明

| 按钮 | 功能 |
|------|------|
| **开始随机** | 触发 3 秒文件名滚动动画，结束后播放选中音频 |
| **停止播放** | 立即停止当前音频（包括系统级进程） |
| **重置列表** | 清空已播放记录，全部恢复可随机状态（需确认） |
| **手动转换/同步** | 强制重新扫描并转换所有 MP4 文件 |
| **音量滑块** | 实时调节播放音量（0 ~ 100） |
| **帮助 → 关于** | 查看版本信息与致谢 |

### 启动参数

```bash
# 普通启动 —— 同步完成后等待操作
python random_mp3_player_auto.py

# 自动播放模式 —— 同步完成后立即开始随机播放
python random_mp3_player_auto.py -r
```

---

## 跨平台说明

| 系统 | FFmpeg 自动安装方式 |
|------|---------------------|
| **Windows** | 自动下载 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 静态构建版（约 80MB） |
| **macOS** | 优先通过 Homebrew 安装，无 Homebrew 则下载静态构建版 |
| **Linux** | 自动检测包管理器（apt/dnf/yum/pacman 等），调用 `pkexec` 系统安装 |

> 若自动安装失败，程序会提示对应平台的手动安装指南。

---

## 技术栈

- **Python 3.8+**
- **tkinter** — GUI 界面
- **pygame** — 跨平台音频播放
- **FFmpeg** — MP4 转 MP3 格式转换
- **subprocess / threading** — 进程管理与后台任务

---

## 致谢

- **Constructed by** KIMI 2.6
- **Format conversion by** [FFmpeg](https://ffmpeg.org)

---

## 许可证

本项目代码采用 [MIT License](LICENSE) 开源。

> **注意**：若您分发的程序包中包含了 FFmpeg 的可执行文件，需遵守 [FFmpeg 的许可证条款](https://ffmpeg.org/legal.html)（通常为 GPL/LGPL）。FFmpeg 的许可证独立于本项目，请确保在分发时附带 FFmpeg 的源码或相关声明。



~~沟槽的午读能不能qs啊?~~
