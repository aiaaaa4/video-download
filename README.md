# 一键加速视频下载

独立 Skill 仓库：`aiaaaa4.video-download`。

**`aiaaaa4.video-download` · v1.4.0 · [ClawHub](https://clawhub.ai/aiaaaa4/video-download)**

这个 Skill 使用 `yt-dlp` 与 FFmpeg，在下载前探测并列出实际分辨率、编码和可见的估算大小，再确认画质、保存位置、命名、源语言和播放列表行为。默认选择最高可用 SDR 兼容方案，下载纯视频流和最佳播放音轨并合并为成片，成功后删除两份中间文件；另行下载一份 ASR 最佳音频到 `.work/input/`。默认在桌面下新建独立项目文件夹，并以“原语言真实标题、平台日期、尾部视频 ID”统一命名项目和文件。

用户询问如何使用时，只需回复“直接发送下载链接即可。”收到首个下载链接后，Skill 通过本机状态文件判断是否首次使用；首次会先告知用户“首次使用video-download skill，我将执行一次依赖/环境检查和更新，后续任务将跳过此步骤。”，随后检查 yt-dlp 与 FFmpeg、尝试 yt-dlp 官方自更新并记录成功状态。后续任务跳过这一整套首次检查。用户不需要源码仓库、Git 或仓库测试；保存目录在每次正式任务确认路径后才创建并检查写权限。

## Repository Boundary

- 唯一资产：`skills/video-download/`
- 唯一版本来源：`registry.json`
- 通用验证：`python3 tools/validate_repo.py`
- 回归测试：`python3 -m unittest discover -s tests`
- 版本更新：`python3 tools/bump_skill_version.py --skill video-download --version <version>`
- 发布预检：`python3 tools/release_skill.py --skill video-download --changelog "<summary>" --dry-run`

该仓库由代码维护项目中的 `video-download` 独立对话负责。个人下载偏好和组合步骤属于日常生产 Flow，不写入本仓库。
