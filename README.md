# Eden-skill

Eden 的模块化技能库：**一个总入口，按任务调用子 Skill，整个仓库统一发行版本。**

当前源码版本：**v0.2.0** · 已发行版本见 [Releases](https://github.com/berniebradford87342-ui/Eden-skill/releases) · [更新记录](CHANGELOG.md) · [技能目录](catalog.json) · [来源说明](THIRD_PARTY.md)

## 首批技能

| Skill | 功能 | 默认状态 |
|---|---|---|
| [eden-skill](skills/eden-skill/SKILL.md) | 总入口、任务分流、安装与升级指引 | 启用 |
| [eden-topic-research](skills/eden-topic-research/SKILL.md) | 双线选题、来源核验、七维评分、历史验证、Obsidian入库 | 启用 |
| [wechat-ai-content](skills/wechat-ai-content/SKILL.md) | 公众号 AI 内容研究、写作审校、配图排版、草稿读回与补传 | 启用 |
| [xiaohongshu-search](skills/xiaohongshu-search/SKILL.md) | 关键词搜索作品 | 启用 |
| [xiaohongshu-darkhorse](skills/xiaohongshu-darkhorse/SKILL.md) | 黑马爆文榜 | 启用 |
| [xhs-follower-growth-chart](skills/xhs-follower-growth-chart/SKILL.md) | 账号涨粉日／周／月榜 | 启用 |
| [bilibili-keywords-search](skills/bilibili-keywords-search/SKILL.md) | B站关键词作品 | 启用 |
| [xiaohongshu-similar-account](skills/xiaohongshu-similar-account/SKILL.md) | 相似账号重测 | 实验／默认停用 |

相似账号工具在Eden历史实跑中出现过错配，保留供重测，不默认参与选题。

## 下载与安装

本仓库公开，浏览、下载和 clone 无需仓库授权。打开 [Releases](https://github.com/berniebradford87342-ui/Eden-skill/releases/latest) 下载完整安装包或单个 Skill；也可以使用 **Code → Download ZIP**。

```sh
git clone https://github.com/berniebradford87342-ui/Eden-skill.git
cd Eden-skill
python3 install.py --list
# 只装总入口
python3 install.py
# 装选题主流程及其必要采集依赖（包括总入口）
python3 install.py --skill eden-topic-research
# 装公众号内容子Skill与总入口
python3 install.py --skill wechat-ai-content
# 所有默认启用Skill，不含实验工具
python3 install.py --all
# 项目级安装
python3 install.py --all --target /path/to/project/.agents/skills
```

默认安装到 `$CODEX_HOME/skills`（未设置时为 `~/.codex/skills`）。已有Skill目录直接保留，避免覆盖本地修改。需要升级时显式执行：

```sh
python3 install.py --all --upgrade
```

升级前按时间备份到目标目录的`.eden-backups/`。安装器只修改Skill目录，不读取或修改Obsidian选题卡片。安装后按客户端要求重新加载Skill。

## 调用

> 用 eden-skill 跑一轮选题，按Eden定位保留至少15条评分与取舍，补具体假设，追加新卡，已有选择与复盘保持不变。

总入口读取目录，按任务加载对应子Skill。Skill是Agent工作说明和辅助脚本，不是自运行服务；完整选题仍需要Agent核验来源与内容方案。可单独调用“查学习教育黑马榜”“验证最近三个完整月涨粉”“搜索B站Agent科普作品”。

公众号示例：“用 wechat-ai-content，按当前公众号定位把这个 AI 营销选题写成完整文章，核验来源、制作封面和内文图，排版后保存到草稿箱。”也可只要求写稿、排版或恢复指定批次。新子Skill自带创作规则与离线交付检查工具；联网研究、图片生成、第三方敏感词检测和公众号上传使用运行环境已配置能力，不捆绑账号凭据或第三方Skill。没有上传适配器时交付本地包并标明缺项。

## 本地配置

- Python **3.9+**、Git（使用clone时）、curl（部分红狐传输）。基础研究和安装脚本使用标准库。
- 红狐采集需要环境变量`REDFOX_API_KEY`，由用户在本机配置，不提交到仓库。
- `EDEN_VAULT`指向本机Obsidian库根目录；需已有`Eden账号运营/AI青少年教育账号说明.md`及对标资料。私人定位文件、选题卡片、反馈与登录态不随仓库发布。
- 涨粉榜的可选图片导出需Pillow，部分图表需matplotlib/numpy；Excel导出需pandas/openpyxl。仅使用相应功能时安装。
- 灰豚与原平台浏览器核验需要用户自己的可用登录；本仓库不承诺自动绕过权限或取得完整三个月历史。

## 数据与选题约定

选题研究的两条内容线为AI育儿热点话题、宝妈科普型；公众号使用自己的当前账号配置。原题保留，讲法再适配。科普不以近期热点为前提。先明确内容方案再评分，低分和待核不隐藏。时效类型、对标关联、具体假设与实际复盘分开；缺证据标待验证，不预设命中门槛。新卡沿用现有66字段；已有卡整篇保留，重评独立归档。

## 统一版本与后续扩展

`VERSION`是唯一发行版本真源；`catalog.json`及总入口目录随版本同步。使用`MAJOR.MINOR.PATCH`：修复升PATCH，兼容新增Skill/功能升MINOR，不兼容字段或安装协议变更升MAJOR。子Skill原文中的研究v0.8、评分v0.3等是方法沿革，不是发行号。

新增Skill放到`skills/<name>/`，补齐SKILL.md、目录条目、来源说明和必要测试。修改后运行：

```sh
python3 release.py --set-version <更高版本号> --build
python3 install.py --list
python3 skills/eden-topic-research/scripts/test_import_obsidian.py
python3 skills/eden-topic-research/scripts/test_history_audit.py
python3 skills/wechat-ai-content/scripts/test_package_guard.py
```

更新CHANGELOG，确认测试和文件检查通过后提交、创建对应`vX.Y.Z`标签并发布Release；每个版本生成整包及各Skill单独ZIP。仓库不自动推送或自动升级已安装Skill。

## 开源许可

Eden 原创总入口、选题研究与公众号内容 Skill、安装与发行工具采用 [MIT License](LICENSE)，允许使用、修改和再分发，保留版权及许可声明即可。第三方 Skill 保留原作者权利及来源，不因本仓库公开而自动适用 MIT；具体范围和待核实项见 [THIRD_PARTY.md](THIRD_PARTY.md)。公开代码不包含红狐 API 服务额度，也不包含私人选题库。
