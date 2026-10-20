# 原流程能力与可选适配

截至 2026-10-20 的实际生产记录：**1 个总流程 Skill＋8 个执行 Skill＝9 个独立 Skill**。同一 Skill 的多个阶段不重复计数；研究 API、图片工具、Python 助手、自动任务和子代理不另算 Skill。敏感词检查实际使用 wechat-creator 的 M5 模块，因此不单独加一。

| Skill | 实际职责 | 本子 Skill 中的对应位置 |
|---|---|---|
| miju-wechat-daily-publisher | 日更编排、栏目、检查点与恢复 | 入口、账号配置、恢复协议 |
| wechat-creator | M2 正文、M3 标题、M5 检测、M6 封面路由 | 选题到交付的主流程 |
| wechat-write | 关键词、参考文研究、规律判断、全文创作 | 研究和初稿 |
| eden-director | 账号语气、具体表达、人群和事实边界 | 当前账号配置与编辑判断 |
| aiwritex | 中文编辑 | draft → edited |
| humanizer | 去模板腔、假经历与审校记录 | edited → audit → final |
| wechat-cover | 参考封面、构图分析、方案选择 | 内容驱动的图片计划 |
| imagegen | 生成新图、配合逐张查看验收 | 配图执行 |
| wewrite | 微信 HTML、manifest、接口助手、草稿交付 | 交付包与上传 |

## 如何使用这些能力

本包是独立入口，已经写出基础研究、创作、审校和交付规则，不要求用户先安装上述全部 Skill。如果运行环境有这些 Skill，并且用户或项目路由要求应用，应读取其当前 SKILL.md 后实际执行。新包不复制、捆绑或重新授权它们的第三方实现。

外部研究、词表检测、图片生成和公众号上传依赖运行环境真实可用的工具。按需使用；没调用就记录 `not_run`，手工执行本包方法记 `method_applied`。特别是没有公众号连接器/API 助手时，只能交付本地包，不能声称已接通草稿箱。

M2/wechat-write 的同一参考查询和 M6/wechat-cover 的同一封面查询各复用一次结果。费用和权限遵循现有授权范围，不为“用了更多 Skill”重复查询。

## 实际使用记录

每篇 `skill_usage.json` 记录如下条目：

```json
{
  "skill": "wechat-ai-content",
  "stage": "editing",
  "status": "method_applied",
  "action": "把泛化的效率表述改为具体营销产物，保留测试边界",
  "inputs": ["draft.md"],
  "outputs": ["edited.md", "humanizer_report.md"]
}
```

状态使用 `success`、`method_applied`、`failed`、`not_run`；失败与未执行写清原因。API 成功应有真实响应文件，生成图片应有真实图，草稿成功应有真实 media_id 和读回记录。创建本包所用的 skill-creator 不计入日常生产 Skill 数量。
