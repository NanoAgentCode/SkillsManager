# FlClash 机场订阅与自动转移

## 先用原生订阅作对照

1. 从 FlClash 确认当前 profile、运行中的配置和内核版本。记录故障组是否加载了节点、节点是否都测速超时、其他机场能否通过同一个检测地址。节点缺失时优先查订阅更新、过滤表达式和组引用。
2. 对照机场的原生 profile 与自动转移配置实际加载的节点，检查协议、传输、入口域名和端口、SNI 与认证参数。允许组名前缀等预期差异。若节点参数一致，继续比较原生 profile 的 `dns.proxy-server-nameserver`、节点解析策略和生效配置中的覆写。只合并 `proxy-providers` 时，原生 profile 的顶层 DNS 配置可能未被带入。
3. 对照两套解析器对同一节点入口的 A/AAAA 结果，并用真实返回地址在相同物理接口、相同端口和地址族下测试 TCP。TUN 开启时，系统解析可能得到 Fake-IP，手动发出的请求也可能经另一个机场成功。用实际接口、目标地址和 FlClash 连接日志核对路径。[物理直连排查](direct.md)

## 只修复受影响的节点解析

如果证据指向节点入口解析，且原生 profile 提供了适用于这些入口的解析器，保留现有 `dns.proxy-server-nameserver`，在活动 profile 中将受影响的节点域名加入 `dns.proxy-server-nameserver-policy`。合并已有策略条目。使用当前订阅中核对过的域名和原生解析器，保留节点协议、全局 DNS 与自动转移规则。遇到订阅轮换入口域名时，按新的原生配置复核策略覆盖范围。

```yaml
dns:
  proxy-server-nameserver:
    - 223.5.5.5
  proxy-server-nameserver-policy:
    "node.example.com":
      - "https://resolver.example.com/dns-query"
```

示例仅表示字段位置。节点解析策略需要启用节点解析器，即 `proxy-server-nameserver` 非空。生效值还可能受 FlClash DNS 覆写影响。[Mihomo DNS 配置](https://wiki.metacubex.one/en/config/dns/#proxy-server-nameserver-policy)

## 精简重复订阅和健康检查

1. 同一机场的总组和地区组使用同一订阅 URL 时，先比较请求头、节点覆写、缓存节点及过滤条件。若差异只有地区过滤和展示前缀，每个机场保留一个 `proxy-provider`，地区组共用它并在组内设置 `filter`。组级过滤匹配加载后的节点名，应用前逐组比较节点名单和顺序，并核对固定节点选择是否引用了旧前缀。[Mihomo 代理组筛选](https://wiki.metacubex.one/en/config/proxy-groups/#filter)
2. 检测地址预期返回 HTTP 204 时，在订阅源的 `health-check` 和使用该地址的代理组中设置 `expected-status: "204"`。先用代表性节点确认检测地址确实返回 204。订阅源检测它加载的节点，使用 `proxies` 引用其他组的策略组还需核对自身的检测设置。[订阅源健康检查](https://wiki.metacubex.one/en/config/proxy-providers/#health-checkexpected-status) · [代理组预期状态码](https://wiki.metacubex.one/en/config/proxy-groups/#expected-status)
3. 保留手动地区 `select`、当前选中的地区及地区内 `fallback` 顺序。保留原跨机场 `url-test` 或 `fallback` 模式。地区内可在多个机场之间切换，切换后出口 IP 可能变化。[Mihomo 自动测速](https://wiki.metacubex.one/en/config/proxy-groups/url-test/) · [Mihomo 故障转移](https://wiki.metacubex.one/en/config/proxy-groups/fallback/)

## 验证并保存

- 备份活动 profile。重新应用后检查运行时确实用了新策略。若用临时配置试验，验证通过后把修复保存到实际生成运行配置的 profile 或覆写，再重新应用。验证失败时恢复并复测原默认出口。
- 对受影响的总组、地区组逐组作 HTTPS 测速，记录通过数和总节点数。确认恢复的节点仍在自动转移组的候选列表里，再经默认代理重做原请求并核对实际出口。
- 优化订阅时，重载后核对生效的订阅源数量、地区组名单与顺序、手动地区选项、当前选择和测速状态码。用连接日志分别确认普通境外、AI 和需直连的目标命中了预期策略。只对检测地址重复发请求时，先确认它有没有被业务分流规则导向另一个策略组。
- 分别报告节点恢复、默认出口可用及真实故障切换的验证结果。若只验证了测速和候选资格，注明是否实际做过切换。订阅 URL、节点凭据、控制器密钥和私有解析器地址应留在本地配置。
- 短时测速和实际请求用于验证当前可达性。故障切换耗时、掉线频率和出口 IP 稳定性分别需要模拟故障或持续观测。
