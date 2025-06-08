#!/usr/bin/env python3
"""
MCP Web 反馈收集器 - Web服务器启动脚本
注意：此脚本只启动Web服务器，MCP服务器由Cursor自动管理
"""

import os
import sys
import asyncio
import socket
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def check_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True


def get_process_info_on_port(port):
    """获取占用端口的进程信息"""
    try:
        # 查找占用端口的进程详细信息
        result = subprocess.run(['lsof', '-i', f':{port}'],
                                capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            processes = []
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 2:
                        processes.append({
                            'command': parts[0],
                            'pid': parts[1],
                            'user': parts[2] if len(parts) > 2 else 'unknown'
                        })
            return processes
    except Exception as e:
        print(f"⚠️ 获取进程信息时发生错误: {e}")
    return []


def kill_process_on_port(port, force=False):
    """杀死占用指定端口的进程"""
    processes = get_process_info_on_port(port)

    if not processes:
        return True

    print(f"📋 发现以下进程占用端口 {port}:")
    for proc in processes:
        print(
            f"   - {proc['command']} (PID: {proc['pid']}, 用户: {proc['user']})")

    # 检查是否是我们自己的进程
    our_processes = [p for p in processes if 'python' in p['command'].lower() and (
        'run.py' in p['command'] or 'web_server' in p['command'])]

    if our_processes and not force:
        print("🔍 检测到可能是本项目的进程，尝试优雅关闭...")
        for proc in our_processes:
            try:
                # 先尝试 SIGTERM
                subprocess.run(['kill', '-15', proc['pid']], check=True)
                print(f"📤 向进程 {proc['pid']} 发送 SIGTERM 信号")
            except subprocess.CalledProcessError:
                print(f"⚠️ 无法向进程 {proc['pid']} 发送 SIGTERM 信号")

        # 等待进程退出
        import time
        time.sleep(2)

        # 检查进程是否还在
        remaining = get_process_info_on_port(port)
        if remaining:
            print("⚠️ 进程仍在运行，使用强制终止...")
            return kill_process_on_port(port, force=True)
        else:
            print("✅ 进程已优雅退出")
            return True

    # 对于非本项目进程，询问用户意见
    other_processes = [p for p in processes if not ('python' in p['command'].lower(
    ) and ('run.py' in p['command'] or 'web_server' in p['command']))]

    if other_processes:
        print("⚠️ 发现非本项目的进程占用端口，为了安全起见，不会自动终止这些进程")
        print("📋 占用端口的其他进程:")
        for proc in other_processes:
            print(
                f"   - {proc['command']} (PID: {proc['pid']}, 用户: {proc['user']})")

        print("\n🤔 请选择处理方式:")
        print("   1. 强制关闭这些进程（谨慎操作！）")
        print("   2. 退出启动程序，手动处理端口冲突")

        try:
            choice = input("请输入选择 (1/2): ").strip()
            if choice == "1":
                print("⚠️ 正在强制终止非本项目进程...")
                for proc in other_processes:
                    print(f"🔧 强制终止进程 {proc['pid']} ({proc['command']})")
                    subprocess.run(['kill', '-9', proc['pid']])
                return True
            else:
                print("👋 已取消启动，请处理端口冲突后重新运行")
                return False
        except (KeyboardInterrupt, EOFError):
            print("\n👋 已取消启动")
            return False

    # 如果只有本项目进程，直接强制终止（这种情况应该在前面已经处理了）
    try:
        for proc in processes:
            print(f"🔧 强制终止进程 {proc['pid']} ({proc['command']})")
            subprocess.run(['kill', '-9', proc['pid']])
        return True
    except Exception as e:
        print(f"❌ 强制终止进程时发生错误: {e}")
        return False


def find_available_port(start_port=9999, max_attempts=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        if not check_port_in_use(port):
            return port
    return None


def main():
    """主函数"""
    try:
        # 设置默认环境变量
        os.environ.setdefault('WEB_HOST', '0.0.0.0')
        os.environ.setdefault('WEB_PORT', '9999')

        port = int(os.environ['WEB_PORT'])

        print("🚀 启动 MCP Web 反馈收集器 - Web服务器...")
        print(f"📁 项目根目录: {project_root}")
        print(
            f"🌐 Web 地址: http://{os.environ['WEB_HOST']}:{os.environ['WEB_PORT']}")
        print("📝 注意：MCP服务器由Cursor自动管理，无需手动启动")

        # 检查端口是否被占用
        if check_port_in_use(port):
            print(f"⚠️ 端口 {port} 被占用，正在分析占用进程...")

            # 获取进程信息
            processes = get_process_info_on_port(port)
            if not processes:
                print("🤔 无法获取占用进程信息，可能是权限问题")
                print(f"💡 请手动运行: lsof -i :{port}")
                print(f"💡 然后运行: kill -9 <PID>")
                sys.exit(1)

            # 尝试清理端口
            if kill_process_on_port(port):
                print("✅ 端口清理成功")
                # 等待一下确保端口释放
                import time
                time.sleep(1)

                # 再次检查端口
                if check_port_in_use(port):
                    print(f"❌ 端口 {port} 仍被占用，请手动处理")
                    sys.exit(1)
            else:
                print(f"❌ 端口 {port} 清理失败或被用户取消")
                print("💡 请尝试以下解决方案:")

                # 尝试找到可用端口
                alternative_port = find_available_port(port + 1)
                if alternative_port:
                    print(f"   1. 使用其他端口启动:")
                    print(f"      WEB_PORT={alternative_port} python run.py")

                print("   2. 手动清理占用进程:")
                for proc in processes:
                    print(f"      kill -9 {proc['pid']}  # {proc['command']}")

                print("   3. 检查进程详情:")
                print(f"      lsof -i :{port}")

                sys.exit(1)

        print("=" * 50)

        # 导入并运行Web服务器
        from src.web_server import run_web_server
        run_web_server()

    except KeyboardInterrupt:
        print("\n👋 收到中断信号，正在关闭服务器...")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
