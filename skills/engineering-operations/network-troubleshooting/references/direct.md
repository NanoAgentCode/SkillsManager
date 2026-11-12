# 直连排查

## 确认走的是哪条直连

- **应用内 `DIRECT`** 是 FlClash/Mihomo 的出站策略。用运行中的「连接」记录核对目标域名、命中规则和完整代理链。`MATCH,DIRECT` 只覆盖此前规则均未匹配的流量。已命中的分流组需要有 `DIRECT` 选项，或通过它引用的选择组选择 `DIRECT`。
- **物理网络直连** 用于验证本机到目标或 VPS 公网入口。核对源地址、接口、下一跳及是否经过 TUN、VPN 或透明代理。`curl --noproxy '*'` 跳过 curl 自身的代理选择，系统接管仍需另查。若需要临时关闭接管功能作对照，先保留当前设置和可用管理通道；测试结束后恢复。Fake-IP 模式下核对实际拨号地址。

## 逐层验证

以下命令中的域名、端口及保留地址均为示例，替换成正在排查的目标。Windows PowerShell 检查系统解析与路由，然后发起请求：

```powershell
$target = 'example.com'
$targetIp = '192.0.2.10'
$targetPort = 443
Resolve-DnsName $target -Type A
Resolve-DnsName $target -Type AAAA
Test-NetConnection -ComputerName $targetIp -DiagnoseRouting
Test-NetConnection -ComputerName $targetIp -Port $targetPort -InformationLevel Detailed
curl.exe -q --noproxy '*' --connect-timeout 5 --max-time 15 -sS -o NUL -w 'remote=%{remote_ip} http=%{http_code}\n' "https://${target}:${targetPort}/"
```

Linux 上先设置同名 shell 变量，再用 `getent ahosts "$target"` 查看系统解析结果、`ip route get "$targetIp"` 或 `ip -6 route get "$targetIp"` 核对路由。将 curl 示例中的 `curl.exe` 改为 `curl`、`NUL` 改为 `/dev/null`，其余参数可沿用。系统解析只是基线，应用使用独立 DNS 时应检查应用解析记录。Windows 的 `-DiagnoseRouting` 与 `-Port` 是两个独立测试，分别回答选路和端口连接问题。

- **疑似 DNS**：用同一目标、端口和地址族对照正常域名访问与 `curl --resolve 'example.com:443:192.0.2.10'`（IPv6 地址用方括号）。从可信记录取得真实地址，保留原 URL、SNI 和证书校验。只有指定地址成功时，继续核对生效的解析器、域名规则与 DNS 缓存，再修复对应配置。
- **疑似 IPv4/IPv6 或本地路由**：分别用 `curl -4` 和 `curl -6` 测试，记录各自的目标地址。TCP 超时就用相同 IP 和端口换热点或另一独立网络对照，确认实际接口。只修复有证据的错误路由、系统代理或 DNS 设置。服务端可控时按 [VPS 双端抓包](vps.md#定位握手与回程) 追踪；只看到单端超时就保留故障范围。
- **TCP 已建立**：继续检查 TLS 证书链、主机名、系统时间和 HTTP 状态。`403`、`429` 等响应表明请求收到了应用层响应，业务是否恢复仍以预期页面或操作结果为准。

修复后用原应用、原域名和原网络复测。要求 FlClash `DIRECT` 时，用连接记录核对规则和链路；要求物理网络直连时，用接口和路由证据核对实际出站路径。

命令与配置参考：[curl 手册](https://curl.se/docs/manpage.html) · [Microsoft Test-NetConnection](https://learn.microsoft.com/en-us/powershell/module/nettcpip/test-netconnection) · [Mihomo 路由规则](https://wiki.metacubex.one/config/rules/) · [Mihomo Select 组](https://wiki.metacubex.one/en/config/proxy-groups/select/)
