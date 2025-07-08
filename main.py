import sys
exit = sys.exit
def check_one_third_party_dependencies(dependencies: str):
    try:
        __import__(dependencies)
    except ImportError:
        print(f"\033[31m没有第三方库: {dependencies}\033[0m")
        exit(1)

def check_third_party_dependencies(dependencies: list):
    for dependency in dependencies:
        check_one_third_party_dependencies(dependency)

check_third_party_dependencies(
    [
        "colorama"
    ]
)

import platform
import colorama
import os
import os.path
import http.client

colorama.init()

SYSTEM_SERVICE_STRING = '''[Unit]
Description=frps
After=network.target

[Service]
Type=simple
ExecStart=/opt/frps/frps -c /opt/frps/frps.toml
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target'''

def color_print(text: str, color: str):
    color = getattr(colorama.Fore, color.upper())
    reset = colorama.Fore.RESET
    print(f"{color}{text}{reset}")

def is_ubuntu() -> bool:
    if platform.system() == 'Linux':
        with open('/etc/os-release', 'rt', encoding="utf-8") as f:
            for line in f:
                if line.startswith('ID='):
                    return line.split('=')[1].strip().lower() == 'ubuntu'
    return False

def mkdir_if_not_exists(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def cp_frps():
    if not os.path.exists("./frps"):
        raise FileNotFoundError("frps 不存在")
    if not os.path.exists("/opt/frps/frps"):
        os.system("cp frps /opt/frps")

def install_service_and_start_and_add_startup():
    with open("/etc/systemd/system/frps.service", "wt", encoding="utf-8") as f:
        f.write(SYSTEM_SERVICE_STRING)
    os.system("systemctl daemon-reload")
    os.system("systemctl enable frps")
    os.system("systemctl start frps")

def input_color(text: str, change_function: type(lambda: 1) = str):
    return_val = change_function(input(f"{colorama.Fore.BLUE}{text}{colorama.Fore.CYAN}"))
    print(colorama.Fore.RESET, end="")
    return return_val

def ask_frps_toml_info():
    bindPort = input_color("请输入Frps服务端口: ", int)
    auth_token = input_color("请输入Frps身份验证令牌: ")
    webServer_port = input_color("请输入Frps后台管理端口: ", int)
    webServer_user = input_color("请输入Frps后台管理用户名: ")
    webServer_password = input_color("请输入Frps后台管理密码: ")

    toml_content = f'''bindPort = {bindPort}
auth.token = "{auth_token}"
webServer.addr = "0.0.0.0"
webServer.port = {webServer_port}
webServer.user = "{webServer_user}"
webServer.password = "{webServer_password}"'''

    with open("/opt/frps/frps.toml", "wt", encoding="utf-8") as f:
        f.write(toml_content)

def step_runner(steps: list):
    for i in range(len(steps)):
        color_print(f"将要执行步骤 {i + 1} , 描述: {steps[i][0]}", "magenta")
        try:
            return_value = steps[i][1]()
            color_print(f"步骤 {i + 1} 成功执行, 返回了 {return_value}。", "green")
        except Exception as e:
            color_print(f"步骤 {i + 1} 执行失败, 程序抛出错误 {e}。", "red")
            exit(1)

def check_frp_installion():
    color_print("正在检查 Frp 安装情况...", "magenta")
    for files in ["/opt/frps", "/opt/frps/frps", "/opt/frps/frps.toml", "/etc/systemd/system/frps.service"]:
        if not os.path.exists(files):
            color_print(f"文件(夹) {files} 不存在, Frp 未安装或安装不完整。", "red")
            return False
    color_print("Frp 安装情况检查成功, 已安装 Frp。", "green")
    return True

def delete_frp_directory():
    os.remove("/opt/frps/frps")
    os.remove("/opt/frps/frps.toml")
    os.rmdir("/opt/frps")

def ask_yes_no(prompt: str):
    color_print("输入 y 以同意, 输入其他以拒绝。", "yellow")
    user_input = input_color(f"{prompt} (y/其他) : ")
    return user_input.lower() == 'y'

if not is_ubuntu():
    print("\033[31m该脚本仅支持 Ubuntu 系统\033[0m")
    exit(1)

color_print("欢迎来到 Frp 快速部署器", "yellow")

def install():
    color_print("本次使用的 Frp 版本为 0.63.0 , 将要部署到系统的 /opt/frps\n", "green")
    step_runner([
        [
            "创建目录 /opt/frps",
            lambda: mkdir_if_not_exists("/opt/frps")
        ], [
            "检查复制文件到 /opt/frps",
            lambda: cp_frps()
        ], [
            "赋权给 /opt/frps/frps",
            lambda: os.system("chmod 777 /opt/frps/frps")
        ], [
            "询问用户输入 Frps 配置信息",
            lambda: ask_frps_toml_info()
        ], [
            "安装 Frps 服务",
            lambda: install_service_and_start_and_add_startup()
        ]
    ])
    color_print("\n部署完成。", "green")

def uninstall():
    color_print("正在卸载 Frp...", "yellow")
    step_runner([
        [
            "停止 Frps 服务",
            lambda: os.system("systemctl stop frps")
        ], [
            "禁用 Frps 服务",
            lambda: os.system("systemctl disable frps")
        ], [
            "删除 Frps 服务文件",
            lambda: os.remove("/etc/systemd/system/frps.service")
        ], [
            "删除 Frps 目录",
            lambda: delete_frp_directory()
        ], [
            "重新加载 systemd",
            lambda: os.system("systemctl daemon-reload")
        ]
    ])
    color_print("\n卸载完成。", "green")  

if check_frp_installion():
    color_print("检测到 Frp 安装。", "green")
    if ask_yes_no("是否确实要卸载 Frp ?"):
        uninstall()
        exit(0)
    
    exit(0)

color_print("未检测到 Frp 完整安装。", "red")

if ask_yes_no("是否确实要安装 Frp ?"):
    install()
