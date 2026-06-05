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

            # 自动安全拼接 &flag=clash 确保机场向小跟班返回包含加密 DNS 的完整配置
            if "flag=" not in airport_url:
                if "?" in airport_url:
                    airport_url += "&flag=clash"
                else:
                    airport_url += "?flag=clash"

            try:
                req = urllib.request.Request(
                    airport_url,
                    headers={
                        'User-Agent': 'Mihomo',
                        'User-agent': 'Mihomo'
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw_text = resp.read().decode('utf-8', errors='ignore')
                    # 精准匹配包含端口号的动态加密 DoH 链接
                    found_urls = re.findall(r"https://[^\s'\",\]]+/dns-query/[A-Za-z0-9-]+", raw_text)
                    if found_urls:
                        extracted_dns = list(set(found_urls))
            except Exception as e:
                print(f"[小跟班提示] 提前提取机场动态 DNS 失败: {e}")

        # 3. 构造完整请求，无损转发给内部真正的 subconverter 工作核心（本地 25500 端口）
        backend_url = f"http://127.0.0.1:{REAL_BACKEND_PORT}{parsed_url.path}"
        if parsed_url.query:
            backend_url += f"?{parsed_url.query}"

        try:
            backend_req = urllib.request.Request(
                backend_url,
                headers={
                    'User-Agent': 'Mihomo',
                    'User-agent': 'Mihomo'
                }
            )

            with urllib.request.urlopen(backend_req, timeout=15) as resp:
                clash_config = resp.read().decode('utf-8', errors='ignore')

            # 自动无损缝合被 Subconverter 意外截断换行的长行代理节点（针对 Reality 节点的多行保护）
            raw_lines = clash_config.split('\n')
            fixed_lines = []
            for line in raw_lines:
                if fixed_lines and line.strip() and not line.strip().startswith('-') and not line.strip().startswith('proxy-groups:') and not line.strip().startswith('rules:') and (fixed_lines[-1].strip().endswith(',') or fixed_lines[-1].strip().endswith('{')):
                    fixed_lines[-1] = fixed_lines[-1].rstrip() + " " + line.strip()
                else:
                    fixed_lines.append(line)
            clash_config = '\n'.join(fixed_lines)

            # =====================================================================
            # 【高阶精准缝合】利用行首锚点，确保只替换最顶层的主 Key，绝不污染策略组内部
            # =====================================================================
            if extracted_dns:
                dns_block = "  proxy-server-nameserver:\n"
                for dns_url in extracted_dns:
                    dns_block += f"    - '{dns_url}'\n"

                # 使用 re.M (多行模式) 和 ^ 锚点，确保只匹配最左边、无缩进的顶级配置项
                if re.search(r"^dns:\s*$", clash_config, re.M):
                    # 如果原配置已经有最顶层的 dns: 块，直接在下方插入最新的加密 DoH 列表
                    clash_config = re.sub(r"^(dns:\s*)$", f"\\1\n{dns_block.rstrip()}", clash_config, flags=re.M)
                elif re.search(r"^proxies:\s*$", clash_config, re.M):
                    # 如果原配置没有 dns: 块，在顶级 proxies: 的正上方创建最纯净的 dns 主模块
                    dns_module = f"dns:\n  enable: true\n{dns_block}"
                    clash_config = re.sub(r"^(proxies:\s*)$", f"{dns_module}\\1", clash_config, flags=re.M)
                print("[小跟班提示] 动态加密 DNS 已精准缝合至顶级主配置中！")
            # =====================================================================

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