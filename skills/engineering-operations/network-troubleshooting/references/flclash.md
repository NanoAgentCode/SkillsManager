# FlClash / Mihomo 排查与配置

## 核对生效状态

1. 确认当前启用的 profile、客户端和内核版本、系统代理、TUN、规则模式和实际监听。FlClash 可能合并界面设置、覆写和脚本。对照源 profile 与生成的生效配置。在 Windows 上可从 `%APPDATA%/com.follow/clash/` 查找 `config.yaml` 和 `profiles/`，以实际安装与控制器返回为准。
2. `mixed-port` 接收 HTTP/SOCKS 代理流量，`external-controller` 提供管理 API。常见示例分别是 `7890` 和 `127.0.0.1:9090`，以系统监听与当前配置为准。已启用密钥时，控制器返回 HTTP 401 表明端口有响应，带 Bearer 认证后用 `/version` 和 `/configs` 核对状态。管理接口保持在环回地址，密钥只在本机读取和使用。日志、连接信息和 Provider 错误可能包含订阅令牌，分享前只提取脱敏摘要。

## 定位连接慢或超时

| 现象 | 对照与判断 |
| --- | --- |
| 首次导入慢，部分 Provider 为空 | 从 `/providers/proxies` 核对各 Provider 节点数、本地缓存、更新时间。把重复引用归到实际订阅 URL，逐个检查订阅域名的内核 DNS、HTTPS 状态和响应格式。已有缓存的 Provider 可在更新失败时继续显示节点。HTTP 200 后还要确认内容可解析以及筛选后有节点。 |
| 怀疑 DoH 上游卡住 | 用 `/dns/query?name=<域名>&type=A` 计时，结合 `/logs?level=debug` 确认实际选中的上游。对照测试同一网络下上游的 TCP/TLS 和有效 DNS 应答。`--noproxy '*'` 会跳过应用代理，TUN 仍可能接管。需要验证物理网络时，结合[直连排查](direct.md)核对接口和实际路由。 |
| 内核 DNS 和网页访问结果不同 | 用 `curl` 显式走实际的 mixed 端口访问目标，并用 `/connections` 或日志核对命中规则与出站链。部分节点能在远端解析域名，可出现控制器 DNS 超时而实际请求成功。分别报告 DNS 和业务结果。 |
| DNS 返回正常但请求仍失败 | 检查规则顺序、选组、节点握手与目标 HTTP 状态。遇到 `DIRECT` 和代理路径差异时固定同一域名、地址族和网络做对照。若故障发生在到节点的连接或握手，继续[节点和 VPS 排查](vps.md)。 |

一次 Windows 实测中，物理 Wi‑Fi 到 Cloudflare 和 Google 的 IP 型 DoH 均在 TCP 阶段超时。四个订阅域名的内核查询约 5 秒失败，16 个 Provider 中仅 6 个已有节点。给这四个域名单独指定经本机验证可达的 `https://223.5.5.5/dns-query` 后，订阅解析通过，16 个 Provider 均加载并生成缓存。普通域名的 DNS 路径需要单独验收。把该地址视为对照实例，换网络时重测上游。

## 编辑、应用和回滚

1. 先确认现有分流和要修改的范围。备份启用的源 profile 与生效配置到本机受限目录。现有配置做最小改动，例如只给超时的订阅域名增加 `dns.nameserver-policy`。`default-nameserver` 用于解析 DNS 服务器域名，`proxy-server-nameserver` 用于解析节点服务器域名。若订阅下载通过某个代理组，核对该组启动时已有可用节点。
2. 检查 YAML、Provider 缓存路径、组和规则的引用，再用同版本内核校验。可在 PowerShell 或 POSIX shell 中执行 `mihomo -t -d "<独立测试目录>" -f "<配置文件>"`。用 FlClash 重新应用源 profile，或用环回 API 的 `PUT /configs` 应用已核对的完整生效配置。保留持久化的源配置，避免客户端重启后覆盖手动改动。
3. 重载后复测订阅域名解析、Provider 缓存和节点数，以及原业务请求和代理链。冷启动测试使用独立配置和空缓存，保留运行中的缓存。若重载导致现有服务退化，恢复备份，重新应用并复测。

## 从模板创建 profile

复制[四订阅配置模板](../assets/flclash-profile.example.yaml)。把四条 `.invalid` URL 换成自己的订阅地址，把 `nameserver-policy` 的键换成实际的订阅主机名。同一主机名保留一条规则。只用部分订阅时，删除未用的 Provider 和组内 `use` 引用。DNS 上游按当前网络实测选择。填写了真实订阅的副本保存在本机私有目录。

模板用每条订阅一个 Provider。新增地区组时，通过 `use` 复用已定义的 Provider，并在分组上按实际节点名加 `filter`。模板使用手动选组，验证基本连通后可按需为 Provider 增加延迟检查。原 profile 有地区分流、TUN 或规则集时，按需将模板片段合并到源 profile。控制器和 TUN 在模板中由用户按需配置。

模板把 ChatGPT、Claude、Gemini、Google AI Studio、Grok、Meta AI、Google 搜索和 Play 商店放在同一个 `AI` 分组。默认跟随 `订阅节点`，也可以手动选择可用节点，一次切换即可让这些服务走同一出口。合并到现有 profile 时，优先复用已有的 `AI地区选择` 等同用途分组，并把服务规则放在可能先命中的通用规则及 `MATCH` 之前。需要为 Google 服务长期选择独立地区时，可单独建组。

Grok 的规则覆盖 `grok.com` 和 `x.ai`，Meta AI 的规则覆盖 `meta.ai`。嵌在 X、Facebook、Instagram 或 WhatsApp 内的 AI 入口可能使用各平台的共享主机名，Mihomo 对共享主机名统一选路。[Grok 官方说明](https://x.ai/legal/faq) · [Meta AI 官方说明](https://about.fb.com/ja/news/2025/11/meta-ai-gradual-rollout-begins-in-japan/)

Google 搜索的 AI 模式（`google.com/ai`、`google.com/aimode`）与普通搜索共用主机名，这些入口都命中 `AI`。Mihomo 的域名规则仅按主机名匹配。[Google 搜索 AI 模式](https://support.google.com/websearch/answer/16011537) · [Chrome AI 模式](https://support.google.com/chrome/answer/16704170)

`AI` 同时覆盖 Google Play 商店、应用下载、更新和连通性检查。实际设备验收时，在商店打开应用详情，发起一次下载或更新，并在连接记录中核对商店 API 与下载域名走同一出口。[Google Android 网络要求](https://support.google.com/work/android/answer/10513641?hl=en)

参考 [Mihomo DNS](https://wiki.metacubex.one/en/config/dns/) · [Provider](https://wiki.metacubex.one/en/config/proxy-providers/) · [策略组](https://wiki.metacubex.one/en/config/proxy-groups/) · [控制器 API](https://wiki.metacubex.one/en/api/)
