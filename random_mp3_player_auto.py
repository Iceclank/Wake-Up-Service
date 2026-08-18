"""
午休服务
跨平台: Windows/macOS/Linux
启动参数: -r 启动后自动开始随机播放
Designed by Iceclank (https://github.com/Iceclank)
Constructed by KIMI 2.6
Format conversion by FFmpeg(https://ffmpeg.org)
"""

import os
import sys
import random
import threading
import time
import subprocess
import shutil
import tkinter as tk
from tkinter import messagebox, font as tkfont
from urllib.request import urlretrieve
import zipfile

try:
    import pygame
except ImportError:
    pygame = None

#  FFmpeg自动安装器
class FFmpegAutoInstaller:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.embedded_dir = os.path.join(root_dir, "ffmpeg")
        self.ffmpeg_cmd=None
        self.ffplay_cmd=None
        self.platform = sys.platform
        self._detect()

    def _detect(self):
        for cmd in ["ffmpeg", "ffmpeg.exe"]:
            if self._cmd_exists(cmd):
                self.ffmpeg_cmd = cmd
                break
        for cmd in ["ffplay", "ffplay.exe"]:
            if self._cmd_exists(cmd):
                self.ffplay_cmd = cmd
                break

        if not self.ffmpeg_cmd:
            embedded_ffmpeg = os.path.join(self.embedded_dir, "bin", "ffmpeg.exe" if "win" in self.platform else "ffmpeg")
            if os.path.exists(embedded_ffmpeg):
                self.ffmpeg_cmd = embedded_ffmpeg
            elif os.path.exists(os.path.join(self.embedded_dir, "ffmpeg")):
                self.ffmpeg_cmd = os.path.join(self.embedded_dir, "ffmpeg")

        if not self.ffplay_cmd:
            embedded_ffplay = os.path.join(self.embedded_dir, "bin", "ffplay.exe" if "win" in self.platform else "ffplay")
            if os.path.exists(embedded_ffplay):
                self.ffplay_cmd = embedded_ffplay
            elif os.path.exists(os.path.join(self.embedded_dir, "ffplay")):
                self.ffplay_cmd = os.path.join(self.embedded_dir, "ffplay")

    def _cmd_exists(self, cmd):
        try:
            result = subprocess.run([cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def is_available(self):
        return self.ffmpeg_cmd is not None

    def get_ffmpeg(self):
        return self.ffmpeg_cmd

    def get_ffplay(self):
        return self.ffplay_cmd

    def install(self, progress_callback=None):
        if "win" in self.platform:
            return self._install_windows(progress_callback)
        elif "darwin" in self.platform:
            return self._install_macos(progress_callback)
        else:
            return self._install_linux(progress_callback)

    def _report(self, msg, progress_callback):
        if progress_callback:
            progress_callback(msg)
        print(f"[FFmpegInstaller] {msg}")

    def _install_windows(self, progress_callback):
        self._report("检测到 Windows 系统", progress_callback)
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        zip_path = os.path.join(self.root_dir, "ffmpeg-download.zip")

        try:
            self._report("正在下载 FFmpeg (~80MB)...", progress_callback)
            urlretrieve(url, zip_path, reporthook=lambda b, bs, ts: self._download_progress(b, bs, ts, progress_callback))
            self._report("下载完成，正在解压...", progress_callback)

            extract_dir = os.path.join(self.root_dir, "ffmpeg-temp")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            subdirs = [d for d in os.listdir(extract_dir) if os.path.isdir(os.path.join(extract_dir, d))]
            if not subdirs:
                raise RuntimeError("解压后未找到 FFmpeg 目录")

            src = os.path.join(extract_dir, subdirs[0])
            dst = self.embedded_dir
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.move(src, dst)

            shutil.rmtree(extract_dir)
            os.remove(zip_path)

            self._detect()
            if self.ffmpeg_cmd:
                self._report("FFmpeg 安装成功", progress_callback)
                return True
            else:
                raise RuntimeError("安装后未检测到 FFmpeg")

        except Exception as e:
            self._report(f"安装失败: {e}", progress_callback)
            for p in [zip_path, os.path.join(self.root_dir, "ffmpeg-temp")]:
                if os.path.exists(p):
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p)
                        else:
                            os.remove(p)
                    except Exception:
                        pass
            return False

    def _download_progress(self, block_num, block_size, total_size, progress_callback):
        if total_size > 0 and progress_callback and block_num % 20 == 0:
            pct = min(100, int(block_num * block_size * 100 / total_size))
            progress_callback(f"下载中... {pct}%")

    def _install_macos(self, progress_callback):
        self._report("检测到macOS系统", progress_callback)
        has_brew = self._cmd_exists("brew")

        if has_brew:
            self._report("发现Homebrew，正在安装FFmpeg...", progress_callback)
            try:
                result = subprocess.run(
                    ["brew", "install", "ffmpeg"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300
                )
                if result.returncode == 0:
                    self._report("Homebrew安装完成", progress_callback)
                    self._detect()
                    if self.ffmpeg_cmd:
                        return True
                else:
                    self._report(f"Homebrew安装出错: {result.stderr}", progress_callback)
            except Exception as e:
                self._report(f"Homebrew安装异常: {e}", progress_callback)
        else:
            self._report("未检测到Homebrew", progress_callback)

        self._report("尝试下载静态构建版...", progress_callback)
        return self._install_macos_static(progress_callback)

    def _install_macos_static(self, progress_callback):
        url = "https://www.osxexperts.net/ffmpeg7.zip"
        zip_path = os.path.join(self.root_dir, "ffmpeg-download.zip")

        try:
            self._report("正在下载 FFmpeg for macOS...", progress_callback)
            urlretrieve(url, zip_path)
            self._report("下载完成，正在解压...", progress_callback)

            extract_dir = os.path.join(self.root_dir, "ffmpeg-temp")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            ffmpeg_bin = None
            for root, dirs, files in os.walk(extract_dir):
                for f in files:
                    if f == "ffmpeg":
                        ffmpeg_bin = os.path.join(root, f)
                        break
                if ffmpeg_bin:
                    break

            if not ffmpeg_bin:
                raise RuntimeError("解压后未找到 ffmpeg 可执行文件")

            dst = self.embedded_dir
            if os.path.exists(dst):
                shutil.rmtree(dst)
            os.makedirs(dst, exist_ok=True)
            shutil.copy2(ffmpeg_bin, os.path.join(dst, "ffmpeg"))
            os.chmod(os.path.join(dst, "ffmpeg"), 0o755)

            ffplay_bin = None
            for root, dirs, files in os.walk(extract_dir):
                for f in files:
                    if f == "ffplay":
                        ffplay_bin = os.path.join(root, f)
                        break
                if ffplay_bin:
                    break
            if ffplay_bin:
                shutil.copy2(ffplay_bin, os.path.join(dst, "ffplay"))
                os.chmod(os.path.join(dst, "ffplay"), 0o755)

            shutil.rmtree(extract_dir)
            os.remove(zip_path)

            self._detect()
            if self.ffmpeg_cmd:
                self._report("FFmpeg 安装成功", progress_callback)
                return True
            else:
                raise RuntimeError("安装后未检测到 FFmpeg")

        except Exception as e:
            self._report(f"静态版安装失败: {e}", progress_callback)
            for p in [zip_path, os.path.join(self.root_dir, "ffmpeg-temp")]:
                if os.path.exists(p):
                    try:
                        if os.path.isdir(p):
                            shutil.rmtree(p)
                        else:
                            os.remove(p)
                    except Exception:
                        pass
            return False

    def _install_linux(self, progress_callback):
        self._report("检测到 Linux 系统", progress_callback)
        pkg_manager = self._detect_linux_pkg_manager()
        if not pkg_manager:
            self._report("无法识别 Linux 发行版", progress_callback)
            return False

        self._report(f"使用包管理器: {pkg_manager}", progress_callback)

        cmds = {
            "apt":   ["pkexec", "apt", "install", "-y", "ffmpeg"],
            "dnf":   ["pkexec", "dnf", "install", "-y", "ffmpeg"],
            "yum":   ["pkexec", "yum", "install", "-y", "ffmpeg"],
            "pacman":["pkexec", "pacman", "-S", "--noconfirm", "ffmpeg"],
            "zypper":["pkexec", "zypper", "install", "-y", "ffmpeg"],
            "apk":   ["pkexec", "apk", "add", "ffmpeg"],
        }

        cmd = cmds.get(pkg_manager)
        if not cmd:
            return False

        try:
            self._report("正在调用系统安装器 (可能需要输入密码)...", progress_callback)
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
            if result.returncode == 0:
                self._report("安装完成", progress_callback)
                self._detect()
                return self.ffmpeg_cmd is not None
            else:
                self._report(f"安装失败: {result.stderr}", progress_callback)
                return False
        except Exception as e:
            self._report(f"安装异常: {e}", progress_callback)
            return False

    def _detect_linux_pkg_manager(self):
        managers = [
            ("/usr/bin/apt", "apt"),
            ("/usr/bin/apt-get", "apt"),
            ("/usr/bin/dnf", "dnf"),
            ("/usr/bin/yum", "yum"),
            ("/usr/bin/pacman", "pacman"),
            ("/usr/bin/zypper", "zypper"),
            ("/sbin/apk", "apk"),
        ]
        for path, name in managers:
            if os.path.exists(path):
                return name
        for name in ["apt", "dnf", "yum", "pacman", "zypper", "apk"]:
            if self._cmd_exists(name):
                return name
        return None

    def get_manual_install_guide(self):
        if "win" in self.platform:
            return "Windows 自动安装失败，请手动下载：\nhttps://www.gyan.dev/ffmpeg/builds/\n解压后将 bin 目录加入系统 PATH"
        elif "darwin" in self.platform:
            return "macOS 自动安装失败，请手动执行：\nbrew install ffmpeg\n或访问 https://ffmpeg.org/download.html#build-mac 下载"
        else:
            return "Linux 自动安装失败，请手动执行：\nsudo apt install ffmpeg   (Debian/Ubuntu)\nsudo dnf install ffmpeg   (Fedora)\nsudo pacman -S ffmpeg     (Arch)"

#  转换器与播放器
class MP4ToMP3Converter:
    def __init__(self, root_dir, ffmpeg_cmd):
        self.root_dir = root_dir
        self.audio_dir = os.path.join(root_dir, "audio")
        os.makedirs(self.audio_dir, exist_ok=True)
        self.ffmpeg_cmd = ffmpeg_cmd

    def get_mp4_files(self):
        files = []
        for f in os.listdir(self.root_dir):
            if f.lower().endswith('.mp4') and os.path.isfile(os.path.join(self.root_dir, f)):
                files.append(f)
        return sorted(files)

    def get_audio_files(self):
        if not os.path.exists(self.audio_dir):
            return []
        return sorted([f for f in os.listdir(self.audio_dir) if f.lower().endswith('.mp3')])

    def check_sync(self):
        mp4_files = self.get_mp4_files()
        mp3_files = self.get_audio_files()
        mp4_stems = {os.path.splitext(f)[0] for f in mp4_files}
        mp3_stems = {os.path.splitext(f)[0] for f in mp3_files}
        missing_mp3 = mp4_stems - mp3_stems
        orphan_mp3 = mp3_stems - mp4_stems
        needs_conversion = bool(missing_mp3) or bool(orphan_mp3)
        return needs_conversion, mp4_files, mp3_files, missing_mp3, orphan_mp3

    def convert_all(self, progress_callback=None):
        _, mp4_files, mp3_files, _, orphan_mp3 = self.check_sync()
        converted = []
        failed = []
        skipped = []

        for mp3_name in mp3_files:
            stem = os.path.splitext(mp3_name)[0]
            if stem in orphan_mp3:
                try:
                    os.remove(os.path.join(self.audio_dir, mp3_name))
                    if progress_callback:
                        progress_callback(0, 0, f"清理: {mp3_name}")
                except Exception as e:
                    print(f"删除文件失败: {e}")

        total = len(mp4_files)
        for i, mp4_name in enumerate(mp4_files):
            stem = os.path.splitext(mp4_name)[0]
            mp3_name = stem + ".mp3"
            mp3_path = os.path.join(self.audio_dir, mp3_name)
            mp4_path = os.path.join(self.root_dir, mp4_name)

            if os.path.exists(mp3_path):
                skipped.append(mp3_name)
                if progress_callback:
                    progress_callback(i + 1, total, f"跳过: {mp4_name}")
                continue

            if progress_callback:
                progress_callback(i + 1, total, f"转换中: {mp4_name}")

            cmd = [
                self.ffmpeg_cmd, "-y", "-i", mp4_path,
                "-vn", "-ar", "44100", "-ac", "2", "-b:a", "320k",
                "-map", "a", mp3_path
            ]
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
                if result.returncode == 0:
                    converted.append(mp3_name)
                else:
                    print(f"FFmpeg 错误: {result.stderr}")
                    failed.append(mp4_name)
            except Exception as e:
                print(f"转换异常: {mp4_name} -> {e}")
                failed.append(mp4_name)

        return converted, failed, skipped


class AudioPlayer:
    def __init__(self, ffplay_cmd=None):
        self._stop_event = threading.Event()
        self._proc = None
        self._play_thread = None
        self._pygame_ok = False
        self._ffplay_cmd = ffplay_cmd
        self._volume = 1.0

        if pygame:
            try:
                pygame.mixer.init(frequency=44100)
                self._pygame_ok = True
            except Exception as e:
                print(f"[AudioPlayer] pygame mixer init failed: {e}")
                self._pygame_ok = False

    def set_volume(self, value):
        """设置音量，value 为 0.0 ~ 1.0"""
        self._volume = max(0.0, min(1.0, value))
        if self._pygame_ok and pygame.mixer.get_init():
            try:
                pygame.mixer.music.set_volume(self._volume)
            except Exception:
                pass

    def play(self, filepath, on_finish=None):
        self.stop()
        self._stop_event.clear()

        def _play():
            try:
                if self._pygame_ok:
                    try:
                        pygame.mixer.music.load(filepath)
                        pygame.mixer.music.set_volume(self._volume)
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            if self._stop_event.is_set():
                                pygame.mixer.music.stop()
                                return
                            time.sleep(0.05)
                        if on_finish and not self._stop_event.is_set():
                            on_finish()
                        return
                    except Exception as e:
                        print(f"[AudioPlayer] pygame 播放失败: {e}，使用系统播放器")
                self._play_system(filepath, on_finish)
            except Exception as e:
                print(f"[AudioPlayer] 播放失败: {e}")

        self._play_thread = threading.Thread(target=_play, daemon=True)
        self._play_thread.start()

    def _play_system(self, filepath, on_finish=None):
        filepath = os.path.abspath(filepath)
        if sys.platform == "darwin":
            cmd = ["afplay", filepath]
        elif sys.platform == "win32":
            if self._ffplay_cmd and os.path.exists(self._ffplay_cmd):
                cmd = [self._ffplay_cmd, "-nodisp", "-autoexit", filepath]
            else:
                os.startfile(filepath)
                if on_finish:
                    on_finish()
                return
        else:
            if self._ffplay_cmd and os.path.exists(self._ffplay_cmd):
                cmd = [self._ffplay_cmd, "-nodisp", "-autoexit", filepath]
            else:
                cmd = ["xdg-open", filepath]

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=(sys.platform != "win32")
            )
        except FileNotFoundError:
            print(f"[AudioPlayer] 找不到播放器命令: {cmd[0]}")
            return

        while True:
            ret = self._proc.poll()
            if ret is not None:
                break
            if self._stop_event.is_set():
                self._kill_proc()
                break
            time.sleep(0.05)

        if on_finish and not self._stop_event.is_set():
            on_finish()

    def _kill_proc(self):
        if self._proc is None:
            return
        try:
            self._proc.terminate()
            self._proc.wait(timeout=1)
        except Exception:
            try:
                self._proc.kill()
                self._proc.wait(timeout=1)
            except Exception:
                pass
        finally:
            self._proc = None

    def stop(self):
        self._stop_event.set()
        if self._pygame_ok and pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
        self._kill_proc()
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=2)

    def cleanup(self):
        self.stop()
        if self._pygame_ok and pygame.mixer.get_init():
            try:
                pygame.mixer.quit()
            except Exception:
                pass

#  主程序 GUI
class RandomPlayerApp:
    BG_MAIN = "#f0f2f5"
    BG_FRAME = "#ffffff"
    FG_TEXT = "#333333"
    FG_DIM = "#666666"
    FG_HIGHLIGHT = "#2196F3"
    FG_SUCCESS = "#4CAF50"
    FG_ERROR = "#f44336"
    FG_WARN = "#FF9800"
    BTN_PRIMARY = "#e8eaed"
    BTN_HOVER = "#dadce0"

    def __init__(self, root, auto_random=False):
        self.root = root
        self.root.title("午休服务")
        self.root.geometry("600x480")
        self.root.configure(bg=self.BG_MAIN)
        self.root.minsize(480, 400)

        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.auto_random = auto_random  # 是否启动后自动随机播放

        self.ffmpeg_installer = FFmpegAutoInstaller(self.root_dir)
        self.ffmpeg_cmd = self.ffmpeg_installer.get_ffmpeg()
        self.ffplay_cmd = self.ffmpeg_installer.get_ffplay()

        self.converter = None
        self.player = None

        self.all_files = []
        self.remaining = []
        self.played = []
        self.is_animating = False
        self.animation_after_id = None
        self.auto_play_after_conversion = False

        self._build_ui()
        self.root.after(300, self._startup_flow)

    def _build_ui(self):
        title_font = tkfont.Font(family="Microsoft YaHei", size=18, weight="bold")
        anim_font = tkfont.Font(family="Microsoft YaHei", size=16, weight="bold")
        info_font = tkfont.Font(family="Microsoft YaHei", size=11)
        btn_font = tkfont.Font(family="Microsoft YaHei", size=12, weight="bold")

        # 菜单栏
        menubar = tk.Menu(self.root, bg=self.BG_MAIN, fg=self.FG_TEXT, relief="flat")
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.BG_FRAME, fg=self.FG_TEXT)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        self.root.config(menu=menubar)

        tk.Label(
            self.root, text="午休服务", font=title_font,
            bg=self.BG_MAIN, fg=self.FG_TEXT
        ).pack(pady=(20, 8))

        self.ffmpeg_status = tk.Label(
            self.root, text="", font=("Microsoft YaHei", 10),
            bg=self.BG_MAIN, fg=self.FG_DIM
        )
        self.ffmpeg_status.pack(pady=(0, 4))

        self.anim_frame = tk.Frame(self.root, bg=self.BG_FRAME, bd=1, relief="solid")
        self.anim_frame.pack(padx=40, pady=10, fill=tk.BOTH, expand=True)

        self.anim_label = tk.Label(
            self.anim_frame, text="启动中，请稍候...", font=anim_font,
            bg=self.BG_FRAME, fg=self.FG_HIGHLIGHT, wraplength=480
        )
        self.anim_label.pack(expand=True, pady=30)

        self.info_label = tk.Label(
            self.root, text="剩余: 0 | 已播放: 0", font=info_font,
            bg=self.BG_MAIN, fg=self.FG_DIM
        )
        self.info_label.pack(pady=(6, 8))

        btn_frame = tk.Frame(self.root, bg=self.BG_MAIN)
        btn_frame.pack(pady=8)

        self.random_btn = tk.Button(
            btn_frame, text="开始随机", font=btn_font,
            bg=self.BTN_PRIMARY, fg=self.FG_TEXT, activebackground=self.BTN_HOVER,
            width=12, height=1, cursor="hand2",
            command=self._start_random, relief="flat"
        )
        self.random_btn.pack(side=tk.LEFT, padx=6)

        self.stop_btn = tk.Button(
            btn_frame, text="停止播放", font=btn_font,
            bg=self.BTN_PRIMARY, fg=self.FG_TEXT, activebackground=self.BTN_HOVER,
            width=10, height=1, cursor="hand2",
            command=self._stop_playback, relief="flat"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=6)

        self.reset_btn = tk.Button(
            btn_frame, text="重置列表", font=btn_font,
            bg=self.BTN_PRIMARY, fg=self.FG_TEXT, activebackground=self.BTN_HOVER,
            width=12, height=1, cursor="hand2",
            command=self._reset_list, relief="flat"
        )
        self.reset_btn.pack(side=tk.LEFT, padx=6)

        # 音量控制
        vol_frame = tk.Frame(self.root, bg=self.BG_MAIN)
        vol_frame.pack(pady=(4, 2))

        tk.Label(vol_frame, text="音量:", font=("Microsoft YaHei", 10),
                 bg=self.BG_MAIN, fg=self.FG_DIM).pack(side=tk.LEFT, padx=(0, 4))

        self.volume_var = tk.IntVar(value=100)
        self.volume_scale = tk.Scale(
            vol_frame, from_=0, to=100, orient=tk.HORIZONTAL,
            length=200, showvalue=True, variable=self.volume_var,
            bg=self.BG_MAIN, fg=self.FG_TEXT, troughcolor=self.BG_FRAME,
            highlightthickness=0, command=self._on_volume_change
        )
        self.volume_scale.pack(side=tk.LEFT)

        self.status_label = tk.Label(
            self.root, text="状态: 启动中...", font=("Microsoft YaHei", 10),
            bg=self.BG_MAIN, fg=self.FG_DIM
        )
        self.status_label.pack(pady=(4, 5))

        self.convert_btn = tk.Button(
            self.root, text="手动转换/同步", font=("Microsoft YaHei", 10),
            bg=self.BTN_PRIMARY, fg=self.FG_TEXT, activebackground=self.BTN_HOVER,
            cursor="hand2", command=self._manual_conversion, relief="flat"
        )
        self.convert_btn.pack(pady=5)

    def _set_status(self, text):
        self.status_label.config(text=f"状态: {text}")

    def _update_info(self):
        self.info_label.config(
            text=f"剩余: {len(self.remaining)} | 已播放: {len(self.played)} | 总计: {len(self.all_files)}"
        )

    def _startup_flow(self):
        if self.ffmpeg_cmd:
            self.ffmpeg_status.config(text="FFmpeg 已就绪", fg=self.FG_SUCCESS)
            self._init_app()
            return

        self.ffmpeg_status.config(text="未检测到 FFmpeg", fg=self.FG_ERROR)
        self.anim_label.config(text="未检测到 FFmpeg", fg=self.FG_ERROR)

        platform_name = "Windows" if "win" in sys.platform else ("macOS" if "darwin" in sys.platform else "Linux")
        answer = messagebox.askyesno(
            "自动安装 FFmpeg",
            f"未检测到 FFmpeg（当前系统: {platform_name}）\n\n"
            f"是否自动下载并安装？\n"
            f"- Windows: 下载约 80MB 静态构建版\n"
            f"- macOS: 通过 Homebrew 或静态版安装\n"
            f"- Linux: 调用系统包管理器安装\n\n"
            f"点击「是」自动安装，「否」退出程序。",
            icon="question"
        )

        if not answer:
            guide = self.ffmpeg_installer.get_manual_install_guide()
            messagebox.showinfo("手动安装指南", guide)
            self.root.destroy()
            return

        self._set_status("正在安装 FFmpeg...")
        self.anim_label.config(text="正在安装 FFmpeg...\n请稍候", fg=self.FG_WARN)
        self.convert_btn.config(state=tk.DISABLED)
        self.random_btn.config(state=tk.DISABLED)

        def install_progress(msg):
            self.root.after(0, lambda: self._set_status(msg))

        def install_thread():
            success = self.ffmpeg_installer.install(progress_callback=install_progress)
            self.root.after(0, lambda: self._install_finished(success))

        threading.Thread(target=install_thread, daemon=True).start()

    def _install_finished(self, success):
        self.convert_btn.config(state=tk.NORMAL)
        self.random_btn.config(state=tk.NORMAL)

        if success:
            self.ffmpeg_cmd = self.ffmpeg_installer.get_ffmpeg()
            self.ffplay_cmd = self.ffmpeg_installer.get_ffplay()
            self.ffmpeg_status.config(text="FFmpeg 安装成功", fg=self.FG_SUCCESS)
            self._set_status("FFmpeg 安装完成")
            self._init_app()
        else:
            self.ffmpeg_status.config(text="FFmpeg 安装失败", fg=self.FG_ERROR)
            self._set_status("安装失败")
            guide = self.ffmpeg_installer.get_manual_install_guide()
            messagebox.showerror(
                "安装失败",
                f"自动安装 FFmpeg 失败。\n\n{guide}\n\n安装完成后请重启本程序。"
            )
            self.anim_label.config(text="安装失败\n请手动安装后重启", fg=self.FG_ERROR)

    def _init_app(self):
        self.converter = MP4ToMP3Converter(self.root_dir, self.ffmpeg_cmd)
        self.player = AudioPlayer(self.ffplay_cmd)

        mp4_files = self.converter.get_mp4_files()
        if not mp4_files:
            self.anim_label.config(text="未找到 MP4 文件\n请将视频放入程序同级目录", fg=self.FG_WARN)
            self._set_status("等待 MP4 文件")
            return

        needs_conversion, _, _, missing, orphan = self.converter.check_sync()

        if needs_conversion:
            detail = []
            if missing:
                detail.append(f"待转换: {len(missing)} 个")
            if orphan:
                detail.append(f"待清理: {len(orphan)} 个")
            self.anim_label.config(text=f"检测到文件变动\n{', '.join(detail)}", fg=self.FG_WARN)
            self._set_status("自动同步中...")
            self.auto_play_after_conversion = True
            self._do_conversion(auto_mode=True)
        else:
            self._load_audio_list()
            if self.auto_random:
                self._set_status("文件已同步，即将自动播放")
                self.root.after(800, self._start_random)
            else:
                self.anim_label.config(text="准备就绪", fg=self.FG_HIGHLIGHT)
                self._set_status("文件已同步，等待操作")

    def _load_audio_list(self):
        audio_files = self.converter.get_audio_files()
        self.all_files = audio_files.copy()
        self.remaining = audio_files.copy()
        self.played = []
        self._update_info()

    def _do_conversion(self, auto_mode=False):
        self.convert_btn.config(state=tk.DISABLED)
        self.random_btn.config(state=tk.DISABLED)
        self._set_status("正在转换/同步...")

        def progress(current, total, msg):
            self.root.after(0, lambda: self._set_status(f"[{current}/{total}] {msg}"))

        def convert_thread():
            converted, failed, skipped = self.converter.convert_all(progress_callback=progress)
            self.root.after(0, lambda: self._conversion_done(converted, failed, skipped, auto_mode))

        threading.Thread(target=convert_thread, daemon=True).start()

    def _manual_conversion(self):
        self.auto_play_after_conversion = False
        self._do_conversion(auto_mode=False)

    def _conversion_done(self, converted, failed, skipped, auto_mode):
        self.convert_btn.config(state=tk.NORMAL)
        self.random_btn.config(state=tk.NORMAL)
        self._load_audio_list()

        msg_parts = []
        if converted:
            msg_parts.append(f"转换成功: {len(converted)} 个")
        if skipped:
            msg_parts.append(f"已存在: {len(skipped)} 个")
        if failed:
            msg_parts.append(f"失败: {len(failed)} 个")
        self._set_status(" | ".join(msg_parts) if msg_parts else "同步完成")

        if not auto_mode:
            info = f"同步完成！\n"
            if converted:
                info += f"成功: {len(converted)} 个\n"
            if skipped:
                info += f"跳过(已存在): {len(skipped)} 个\n"
            if failed:
                info += f"失败: {', '.join(failed)}"
            messagebox.showinfo("同步完成", info)

        if auto_mode and self.auto_play_after_conversion:
            if self.all_files:
                if self.auto_random:
                    self._set_status("转换完成，即将自动播放")
                    self.root.after(500, self._start_random)
                else:
                    self.anim_label.config(text="准备就绪", fg=self.FG_HIGHLIGHT)
                    self._set_status("转换完成，等待操作")
            else:
                self.anim_label.config(text="没有可用音频", fg=self.FG_ERROR)
                self._set_status("无可用音频")

    def _start_random(self):
        if self.is_animating:
            return
        if not self.remaining:
            if not self.all_files:
                messagebox.showinfo("提示", "没有可用的音频文件")
                return
            self._reset_list(silent=True)

        self.is_animating = True
        self.random_btn.config(state=tk.DISABLED)
        self._set_status("随机抽取中...")

        duration = 3.0
        interval = 50
        steps = int(duration * 1000 / interval)
        pool = self.remaining.copy()

        def animate(step=0):
            if step < steps:
                name = random.choice(pool)
                self.anim_label.config(text=name, fg=self.FG_TEXT)
                self.animation_after_id = self.root.after(interval, animate, step + 1)
            else:
                self._finalize_selection()

        animate()

    def _finalize_selection(self):
        if not self.remaining:
            self.is_animating = False
            self.random_btn.config(state=tk.NORMAL)
            return

        chosen = random.choice(self.remaining)
        self.remaining.remove(chosen)
        self.played.append(chosen)

        self.anim_label.config(text=f"已选中: {chosen}", fg=self.FG_HIGHLIGHT)
        self._update_info()
        self._set_status(f"正在播放: {chosen}")

        audio_path = os.path.join(self.converter.audio_dir, chosen)
        if os.path.exists(audio_path):
            self.player.play(
                audio_path,
                on_finish=lambda: self.root.after(0, lambda: self._on_play_finish(chosen))
            )
        else:
            self._set_status(f"文件不存在: {chosen}")

        self.is_animating = False
        self.random_btn.config(state=tk.NORMAL)

    def _on_play_finish(self, name):
        self._set_status(f"播放完成: {name}")

    def _stop_playback(self):
        self.player.stop()
        self._set_status("播放已停止")

    def _reset_list(self, silent=False):
        if not silent:
            if not messagebox.askyesno("确认重置", "确定要重置播放列表吗？\n已播放记录将被清空。", icon="warning"):
                return
        self.player.stop()
        self.remaining = self.all_files.copy()
        self.played = []
        self._update_info()
        self.anim_label.config(text="列表已重置", fg=self.FG_HIGHLIGHT)
        self._set_status("列表已重置")

    def _on_volume_change(self, value):
        """音量滑块变化回调"""
        if self.player:
            self.player.set_volume(int(value) / 100.0)

    def _show_about(self):
        """显示关于对话框"""
        about_text = (
            "午休服务\n启动参数: -r 启动后开始随机播放\n"
            "Designed by Iceclank (https://github.com/Iceclank)\n"
            "Constructed by KIMI 2.6\n"
            "Format conversion by FFmpeg (https://ffmpeg.org)\n"
        )
        messagebox.showinfo("关于", about_text)

    def on_close(self):
        if self.player:
            self.player.cleanup()
        if self.animation_after_id:
            self.root.after_cancel(self.animation_after_id)
        self.root.destroy()


def main():
    # 解析命令行参数，检测 -r 参数
    auto_random = "-r" in sys.argv
    root = tk.Tk()
    app = RandomPlayerApp(root, auto_random=auto_random)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()

# tmd午读能不能去死啊？
