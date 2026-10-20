# 交付包、接口适配与恢复

## 文件约定

运行产物保存在用户工作区，绝不放到 Skill 源码目录或 GitHub。单篇与多篇使用相同结构；文章数来自用户要求，不固定为两篇。

```text
run/
  manifest.json
  articles/<id>/{draft.md,edited.md,article.md,skill_usage.json}
  main.html / sub_01.html ...
  assets/...
  fact_ledger.md
  humanizer_report.md
  image_plan.md
  review_checklist.md
  skill_usage.json
  stage_checkpoint.json
  research/...
  wordcheck/...
  upload_attempt.json          # 第一次写入必须在远端创建请求之前
  upload_result.json           # 仅真实返回或已确认恢复出的结果
  remote_draft.json            # 真实草稿读取响应
  upload_verification.json
```

`manifest.json` 使用 assets 下模板。`content_html`、`cover_image` 和 HTML 图片必须是包内相对路径；不支持路径穿越、外部绝对路径、远端图片或 data URL。这样可校验资产齐全，避免上传时把不受控网页当作图片。先把合法素材保存到 assets，再上传。

来源既填写在每篇 `source_urls`，也作为可复制文字出现在对应 HTML 可见正文里。手机排版可从 16px 字号、1.9 行高开始，按预览调整；禁止脚本、表单、外部字体和复杂布局。图片有 alt 描述。

`review_checklist.md` 逐项记录事实、文字、敏感词、视觉和排版的实际结论，不只放空勾选框。`stage_checkpoint.json` 记录批次、当前阶段、文章列表、产物路径/哈希、已完成项目、缺项和下一步。任何正文变化都会使旧检测哈希和读回结果失效，必须重核受影响阶段。

本包 `package_guard.py validate` 只做机械检查；文件存在不表示内容审核通过。自动任务宣告完成前仍需执行 SKILL.md 中的人工/模型审核和远端检查。

## 公众号上传适配

本包不捆绑第三方上传 SDK，不自行读取本机的旧账号路径。优先使用用户环境现有的公众号连接器或已审阅的 CLI；部署时必须确认它支持以下能力：

1. 凭据检查（例如 `check-token`）。
2. 本地包校验（例如 `validate`）。
3. 分页获取草稿列表、读取指定草稿。
4. 上传封面和正文图片，创建草稿，返回真实响应。
5. 已有草稿修复时更新对应文章，保留原 media_id。

如果使用已有 `wechat_mp.py`，先读其 `--help` 与实现，确认当前参数及数据格式，再调用。不能把本文中的能力名直接当作所有适配器都存在的命令。

相关微信文档入口：[新增草稿](https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Add_draft.html)、[获取草稿](https://developers.weixin.qq.com/doc/offiaccount/Draft_Box/Get_draft.html)。接口限制、权限、素材大小和认证要求应按当前官方文档及真实响应确认。没有上传工具时仍可完成本地包，明确缺少连接能力，不能伪造响应。

凭据使用用户的密钥存储、私有 env 文件或环境变量，例如 `WECHAT_APPID`、`WECHAT_APPSECRET`、`WECHAT_ACCESS_TOKEN`。错误日志要去除 token、secret 和含凭据的请求 URL。40164 等 IP 白名单错误应记录实际错误及待处理动作；不要停用安全配置或反复重试同一失败。

## 去重、标准响应与读回

创建前分页扫描草稿，核对整组标题、顺序及正文。标题重合只是疑似重复，须读取候选确认；不能仅凭标题跳过，也不能未经确认就新增。已发布的稿件可能不再出现在草稿箱，因此本地历史成功记录同样参与判断。

保留上传器原始脱敏响应，并将校验所需字段标准化为：

```json
{
  "response": {"media_id": "真实草稿ID"},
  "package_hashes": {"manifest.json": "上传前的SHA256", "main.html": "上传前的SHA256", "assets/main_cover.jpg": "上传前的SHA256", "assets/main_01.jpg": "上传前的SHA256"},
  "upload_log": {
    "covers": [{"local": "assets/main_cover.jpg", "media_id": "真实封面素材ID"}],
    "inline_images": [{"local": "assets/main_01.jpg", "url": "https://mmbiz.qpic.cn/真实素材/0"}]
  }
}
```

`package_hashes` 必须保存上传前 validate 的完整 `asset_hashes`，不能在读回时为旧上传重新计算并冒充原记录。图片或 HTML 在同一路径改动也会使旧结果失效。

封面按 manifest 的文章顺序排列；本地素材路径标准化为包内相对路径。微信读取响应保存到 `remote_draft.json`，其 `news_item` 数组包含 `title`、`thumb_media_id`、`content`。适配器记录实际请求的 media_id 为顶层 `requested_media_id`，供校验草稿身份。

`verify` 重新做本地机械校验，再比对数量、顺序、标题、封面素材 ID、可见全文、来源网址和全部正文图。图片支持 `src` 或 `data-src`；仅允许同一 mmbiz.qpic.cn 资产的 http/https 与末尾 0/640 尺寸差异，其他路径和查询参数必须一致。遇到新的合法改写先查证，再扩展规则，不放松为“图片数量相等”。

## 恢复规则

- 本地没有尝试和结果：完成所有审核后，先查远端去重，再创建。
- `upload_result.json` 已有 media_id：只读回、核验或更新原草稿；不能再次创建。
- 已有 `upload_attempt.json` 但无确定结果：标 `outcome_unknown`，分页检查远端并核对正文；确认命中后恢复真实结果，保存恢复证据。仍不明确则保留阻塞状态，不自动重传。
- 校验失败：保留旧文件，修复缺项，重新检查受影响阶段。不要重新研究、重绘所有图片。
- 远端内容缺失：增量修正原草稿，复用已上传资产，重读回确认。

`resume` 命令只给下一步提示，不执行网络动作，也不会把超时当作未创建。即使远端列表暂时无匹配，也不能自动证明之前的创建请求失败。

外部读请求和明确失败的可重试操作最多自动重试两次；创建操作结果未知时直接进入上述核对流程。一个批次只保留一个上传执行者。

## 完成口径

`write`：交付约定的正文与事实/审校说明。

`package`：正文、真实图片、HTML、manifest 和约定审核全部完成。

`draft`：本地包合格、第三方检测满足账号要求、真实上传成功且远端读回通过。报告标题、篇数、路径和待审点；正式发布没有执行。

`resume`：恢复用户指定的批次，只报告真实补齐的阶段。不能因未完成批次超过一天就把它标成完成或悄悄丢弃。
