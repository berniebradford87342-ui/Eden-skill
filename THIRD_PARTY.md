# 来源与使用范围

- `wechat-ai-content`：Eden 公众号生产实践整理的新原创工作流、模板和离线检查脚本；不包含第三方 Skill 的原文或实现。原流程能力对应关系见该 Skill 的 references/skill-map.md。外部服务和生成工具需用户自己的配置与权限。
- `eden-topic-research`：Eden项目本地规则与脚本，打包基线为v0.8。
- `xiaohongshu-darkhorse`、`xhs-follower-growth-chart`、`xiaohongshu-similar-account`：来源为 https://github.com/redfox-data/redfox-community/tree/main/skills ，保留原README及LOCAL_CHANGES。涨粉榜和相似账号包含本地传输及证据口径修正。
- `xiaohongshu-search`、`bilibili-keywords-search`：来自本机已安装的红狐服务Skill；保留原README和服务归属，精确上游提交版本尚未核定。

Eden 原创部分自 v0.1.1 起按根目录 LICENSE 中的 MIT 条款开放；原创 Skill 目录各附 LICENSE。第三方文件版权归原作者，本仓库不代其重新授权。

截至 2026-10-20，红狐上游仓库公开提供 Skill 源码和安装说明，但尚未核实到覆盖这些文件的标准开源许可证。涨粉榜 README 的“许可”段落仅说明服务归属和 API 计费，并非 MIT 授权。因此，第三方部分标为“许可待核实”，不能将本仓库整体宣传为全部 MIT；转载、商用或再分发第三方部分前应核对上游授权。上游来源：https://github.com/redfox-data/redfox-community 。

发行适配：移除本机绝对vault路径、运行缓存与安装机器记录；统一可发现的skill名称；增加Eden数据源角色说明。查询Skill提供的产品、数据范围、更新时刻等描述需以实际响应验证。

红狐服务需要用户自己的REDFOX_API_KEY，可能消耗服务积分。本仓库不包含密钥、浏览器登录态或私人选题卡片。
