#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Sub Converter Wrapper V2
name 用 subconverter 的，其他字段用原始的
保留分组，去除 emoji
"""

import urllib.request
import urllib.parse
import http.server
import socketserver
import re
import yaml
import io

# 小跟班在容器内部用 25501 端口监听
PROXY_PORT = 25501
# 原版 subconverter 在容器内部默认的 25500 端口
REAL_BACKEND_PORT = 25500


def remove_emoji(text):
    """去除文本中的 emoji，保留其他字符"""
    if not text or not isinstance(text, str):
        return text

    # 匹配 emoji 的正则表达式（包含国旗、符号等）
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F926-\U0001F937"
        "\U0001F918-\U0001F940"
        "\U00010000-\U0010FFFF"  # 补充平面
        "]+",
        flags=re.UNICODE
    )

    result = emoji_pattern.sub('', text)
    # 清理多余空格
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def extract_proxies_from_yaml(content):
    """从 YAML 内容中提取 proxies 列表，保留完整字段"""
    try:
        data = yaml.safe_load(content)
        if data and 'proxies' in data:
            return data['proxies']
    except Exception as e:
        print(f"[解析警告] 无法解析为 YAML: {e}")
    return None


def extract_dns_from_config(content):
    """从配置中提取动态 DNS 链接"""
    found_urls = re.findall(r"https://[^\s'\",\]]+/dns-query/[A-Za-z0-9-]+", content)
    return list(set(found_urls)) if found_urls else []


def match_proxy_by_server_port(original_proxies, server, port):
    """
    根据 server 和 port 匹配原始节点
    返回匹配的原始节点，如果没有则返回 None
    """
    for orig in original_proxies:
        if orig.get('server') == server and orig.get('port') == port:
            return orig
    return None


def merge_proxy_keep_name(conv_proxy, orig_proxy):
    """
    合并节点：name 用 subconverter 的，其他字段用原始节点的
    """
    if not orig_proxy:
        # 如果找不到原始节点，返回转换后的
        return dict(conv_proxy)

    # 创建新节点：以原始节点为基础（保留原始节点的所有字段）
    merged = dict(orig_proxy)

    # 只替换 name 为 subconverter 的
    merged['name'] = conv_proxy.get('name', '')

    return merged


class SmartSubHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # 1. 解析请求参数
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        target_urls = query_params.get('url', [])

        original_proxies = []  # 原始订阅中的节点列表
        extracted_dns = []
        raw_original = None

        if target_urls:
            airport_url = target_urls[0]

            # 添加 flag=clash 获取完整配置
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
                    raw_original = resp.read().decode('utf-8', errors='ignore')

                    # 提取 DNS
                    extracted_dns = extract_dns_from_config(raw_original)

                    # 解析原始订阅中的 proxies
                    proxies = extract_proxies_from_yaml(raw_original)
                    if proxies:
                        original_proxies = proxies
                        print(f"[小跟班提示] 从原始订阅提取了 {len(original_proxies)} 个节点")

            except Exception as e:
                print(f"[小跟班提示] 获取原始订阅失败: {e}")

        # 2. 请求 subconverter 后端获取转换后的配置（含分组）
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
                converted_config = resp.read().decode('utf-8', errors='ignore')

            # 3. 解析转换后的配置
            try:
                converted_data = yaml.safe_load(converted_config)
            except Exception as e:
                print(f"[小跟班提示] 无法解析转换后的配置: {e}")
                converted_data = None

            if converted_data and original_proxies:
                # 4. 合并节点：name 用 subconverter 的，其他字段用原始的
                merged_proxies = []
                matched_count = 0
                unmatched_count = 0

                for conv_proxy in converted_data.get('proxies', []):
                    server = conv_proxy.get('server', '')
                    port = conv_proxy.get('port', 0)

                    # 根据 server:port 匹配原始节点
                    orig_proxy = match_proxy_by_server_port(original_proxies, server, port)

                    if orig_proxy:
                        # 找到匹配的原始节点，合并
                        merged = merge_proxy_keep_name(conv_proxy, orig_proxy)
                        matched_count += 1
                    else:
                        # 找不到原始节点，使用转换后的（去除 emoji）
                        merged = dict(conv_proxy)
                        merged['name'] = remove_emoji(merged.get('name', ''))
                        unmatched_count += 1

                    merged_proxies.append(merged)

                # 更新 converted_data 中的 proxies
                converted_data['proxies'] = merged_proxies

                print(f"[小跟班提示] 节点合并完成: {matched_count} 个匹配, {unmatched_count} 个未匹配")

            # 5. 添加 DNS 配置
            if extracted_dns and converted_data:
                if 'dns' not in converted_data:
                    converted_data['dns'] = {}
                converted_data['dns']['enable'] = True
                converted_data['dns']['proxy-server-nameserver'] = extracted_dns
                print(f"[小跟班提示] 已添加 {len(extracted_dns)} 个动态 DNS")

            # 6. 序列化回 YAML
            output = io.StringIO()
            yaml.dump(
                converted_data,
                output,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
                width=float('inf')  # 防止自动换行
            )
            final_config = output.getvalue()

            self.send_response(200)
            self.send_header("Content-Type", "text/yaml; charset=utf-8")
            self.end_headers()
            self.wfile.write(final_config.encode('utf-8'))

        except Exception as e:
            print(f"[小跟班提示] 后端请求失败: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Subconverter Wrapper Error: {e}".encode('utf-8'))


if __name__ == "__main__":
    import sys
    
    # 读取版本号
    version = "未知"
    try:
        with open('/base/VERSION', 'r') as f:
            version = f.read().strip()
    except:
        pass
    
    with socketserver.TCPServer(("0.0.0.0", PROXY_PORT), SmartSubHandler) as httpd:
        print(f"[小跟班提示] 智能合并服务 v{version} 已就绪，正在监听 {PROXY_PORT} 端口...")
        sys.stdout.flush()
        httpd.serve_forever()
