# 一键加速视频下载

独立 Skill 仓库：`aiaaaa4.video-download`。

**`aiaaaa4.video-download` · v1.3.0 · [ClawHub](https://clawhub.ai/aiaaaa4/video-download)**

这个 Skill 使用 `yt-dlp` 与 FFmpeg，在下载前确认画质、保存位置和命名；下载时保存最高质量原始封面，并可为后续处理准备隐藏音频和原语言字幕。它只负责通用下载能力，不包含任何个人 Flow 的固定策略。

## Repository Boundary

- 唯一资产：`skills/video-download/`
- 唯一版本来源：`registry.json`
- 通用验证：`python3 tools/validate_repo.py`
- 回归测试：`python3 -m unittest discover -s tests`
- 版本更新：`python3 tools/bump_skill_version.py --skill video-download --version <version>`
- 发布预检：`python3 tools/release_skill.py --skill video-download --changelog "<summary>" --dry-run`

该仓库由代码维护项目中的 `video-download` 独立对话负责。个人下载偏好和组合步骤属于日常生产 Flow，不写入本仓库。
