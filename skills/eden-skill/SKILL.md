---
name: eden-skill
description: Eden技能库总入口。按任务路由选题研究、公众号AI内容生产、小红书与B站采集、历史增长验证；查看子Skill目录，按需安装或升级。支持统一版本，保护已有选题与复盘。
---

# Eden Skill 总入口

先读[技能目录](references/catalog.json)，再读取任务对应子Skill的SKILL.md，按其工作流程执行。子Skill默认是本文件夹的同级目录；不要一次加载所有Skill。

## 路由

- 完整选题、定位适配、原题重评、三个月验证、Obsidian入库 → `eden-topic-research`。它是选题判断主流程。
- 公众号 AI 行业、营销实操、GitHub 精选、产品稿的写作配图、排版、草稿交付或补传 → `wechat-ai-content`。已有题卡直接创作，不强制先跑选题研究；按公众号自己的账号配置执行。
- 小红书关键词作品 → `xiaohongshu-search`；黑马榜 → `xiaohongshu-darkhorse`。
- 账号日／周／月涨粉榜 → `xhs-follower-growth-chart`；三个月结论交给主流程核验。
- B站关键词作品 → `bilibili-keywords-search`。
- `xiaohongshu-similar-account`是实验工具，默认停用，只有用户明确要求重测时才调用。

完整研究不是把各采集工具都跑一遍。根据用户目标与已授权计划选择必要来源，明确收费查询范围，不静默扩大请求量，不自动订阅或发送消息。

## 下载、安装和升级

仓库：https://github.com/berniebradford87342-ui/Eden-skill 。发行版本统一见仓库VERSION与GitHub Release。

若子Skill缺失，先读安装时生成的`SOURCE.json`，使用其中的本地仓库位置和根目录`install.py`按需安装。路径已失效时，可以从公开仓库下载同一发行版ZIP或clone后再安装，无需仓库授权。不能把下载成功当作API已可用。

```sh
python3 <仓库目录>/install.py --skill eden-topic-research --target <Skills目录>
```

默认已有目录跳过，不覆盖。只有用户要求升级时才使用`--upgrade`；旧版本与本地改动先备份。依赖Skill会一并安装；API Key从环境变量读取。`EDEN_VAULT`指向用户本地知识库，私有资料不从GitHub获取。

## 行为约定

各平台以自己的当前账号说明和用户选择为准，不把其他账号定位自动迁入。选题研究沿用对标分工、两条内容线、66个选题字段。原题保留，不强改育儿标题；科普不因非热点被天然降分。具体假设、评分强项与实际效果分开；无命中门槛；缺证据标待验证；不覆盖已有卡片、选择或复盘。

调用示例：“用eden-skill跑一轮选题，按Eden定位保留至少15条评分与取舍，补具体假设，追加新卡，已有选择与复盘保持不变。”
