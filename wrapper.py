#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import http.server
import socketserver
import re

# 小跟班在容器内部用 25501 端口监听
PROXY_PORT = 25501
# 原版 subconverter 在容器内部默认的 25500 端口
REAL_BACKEND_PORT = 25500

class DynamicDNSHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 1. 解析 OpenClash 发送给本容器的完整请求网址和参数
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # 2. 尝试从请求参数中抓取机场的原始订阅链接
        target_urls = query_params.get('url', [])

        extracted_dns = []
        if target_urls:
            airport_url = target_urls[0]
            try:
                # 3. 小跟班代替路由先访问一次机场，把里面最新变动的加密 DNS 抓出来
                # 【核心伪装】直接在构造函数中锁定 headers，阻断 Python 悄悄塞入自动化 bot 标识
                req = urllib.request.Request(
                    airport_url,
                    headers={
                        'User-Agent': 'Mihomo',
                        'User-agent': 'Mihomo' # 双重大小写锁定，彻底洗掉 Python 默认标识
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw_text = resp.read().decode('utf-8', errors='ignore')
                    found_urls = re.findall(r"https://[^\s'\",\]]+/dns-query/[A-Za-z0-9-]+", raw_text)
                    if found_urls:
                        extracted_dns = list(set(found_urls))
            except Exception as e:
                print(f"[小跟班提示] 提前提取机场动态 DNS 失败: {e}")

        # 4. 构造请求准备转发给内部真正的 subconverter 工作核心（本地 25500 端口）
        backend_url = f"http://127.0.0.1:{REAL_BACKEND_PORT}{parsed_url.path}"
        if parsed_url.query:
            backend_url += f"?{parsed_url.query}"

        try:
            # 【核心伪装】转发给本地核心时同样直接在字典里锁死 Mihomo 身份
            # 这样 subconverter 内部发起 C++ curl 请求时会 100% 携带清纯的 Mihomo 标识，绕过机场拦截墙
            backend_req = urllib.request.Request(
                backend_url,
                headers={
                    'User-Agent': 'Mihomo',
                    'User-agent': 'Mihomo'
                }
            )

            # 拿到原版 subconverter 翻译好的标准 Clash 配置文件文本
            with urllib.request.urlopen(backend_req, timeout=15) as resp:
                clash_config = resp.read().decode('utf-8', errors='ignore')

            # 5. 【核心缝合】如果成功抓到了最新的加密电话本，强行把它塞进配置中
            if extracted_dns:
                if "dns:" in clash_config:
                    proxy_ns_block = "  proxy-server-nameserver:\n"
                    for dns_url in extracted_dns:
                        proxy_ns_block += f"    - '{dns_url}'\n"
                    clash_config = clash_config.replace("dns:\n", f"dns:\n{proxy_ns_block}")
                else:
                    dns_block = "dns:\n  enable: true\n  proxy-server-nameserver:\n"
                    for dns_url in extracted_dns:
                        dns_block += f"    - '{dns_url}'\n"
                    clash_config = clash_config.replace("proxies:\n", f"{dns_block}proxies:\n")
                print("[小跟班提示] 成功把最新的动态加密 DNS 缝合进出厂配置！")

            # 6. 把这班经过完美加工的终极配置文件发送回路由器的 OpenClash
            self.send_response(200)
            self.send_header("Content-Type", "text/yaml; charset=utf-8")
            self.end_headers()
            self.wfile.write(clash_config.encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Subconverter Wrapper Error: {e}".encode('utf-8'))

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PROXY_PORT), DynamicDNSHandler) as httpd:
        print(f"[小跟班提示] 动态拦截服务已就绪，正在监听 {PROXY_PORT} 端口...")
        httpd.serve_forever()