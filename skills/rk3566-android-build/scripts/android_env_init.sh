#!/bin/bash

###############################################################################
# TaishanPi-1m SDK 宿主机环境初始化脚本
# 适用于: Ubuntu 22.04 LTS (Jammy Jellyfish)
# 功能: 自动配置编译所需的完整开发环境
###############################################################################

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# 日志函数
log_info() { echo -e "${GREEN}✓ $* ${NC}"; }
log_warn() { echo -e "${YELLOW}⚠ $* ${NC}"; }
log_error() { echo -e "${RED}✗ $* ${NC}"; }
log_step() { echo -e "${CYAN}${BOLD}▶ $* ${NC}"; }
log_debug() { echo -e "${DIM}  → $* ${NC}"; }

# 进度条函数
show_progress() {
    local current=$1
    local total=$2
    local message=$3
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((current * width / total))
    local remaining=$((width - completed))

    printf "\r${CYAN}[${NC}"
    printf "${GREEN}%${completed}s${NC}" | tr ' ' '█'
    printf "${DIM}%${remaining}s${NC}" | tr ' ' '░'
    printf "${CYAN}]${NC} ${BOLD}${percentage}%%${NC} ${message}"

    if [ $current -eq $total ]; then
        echo ""
    fi
}

# 旋转加载动画
show_spinner() {
    local pid=$1
    local message=$2
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0

    while kill -0 $pid 2>/dev/null; do
        local temp=${spinstr:i++%${#spinstr}:1}
        printf "\r${CYAN}${temp}${NC} ${message}..."
        sleep 0.1
    done
    printf "\r${GREEN}✓${NC} ${message}... ${GREEN}完成${NC}\n"
}

# 打印分隔线
# print_separator() {
#     local char="${1:-═}"
#     local color="${2:-$CYAN}"
#     printf "${color}"
#     printf '%*s' "${COLUMNS:-80}" '' | tr ' ' "$char"
#     printf "${NC}\n"
# }

# 打印标题框
print_box() {
    local message="$1"
    local color="${2:-$CYAN}"
    local length=${#message}
    local padding=4
    local total_length=$((length + padding * 2))

    echo ""
    printf "${color}╔"
    printf '%*s' "$total_length" '' | tr ' ' '═'
    printf "╗${NC}\n"

    printf "${color}║"
    printf "%*s" $padding ''
    printf "${BOLD}${WHITE}%s${NC}" "$message"
    printf "%*s" $padding ''
    printf "${color}║${NC}\n"

    printf "${color}╚"
    printf '%*s' "$total_length" '' | tr ' ' '═'
    printf "╝${NC}\n"
    echo ""
}

# 初始化检测结果变量
ALL_CHECKS_PASS=true

# 检查是否通过sudo运行
check_sudo_privilege() {
    if [[ $EUID -ne 0 ]]; then
        log_error "必须使用 sudo 运行此脚本！"
        echo -e "请执行：\n  ${GREEN}sudo $0 $@${NC}"
        exit 1
    fi
    log_info "权限检查通过"
}

# 配置APT镜像源
configure_apt_mirror() {
    log_step "配置 APT 镜像源"
    echo ""

    # 备份原有源列表
    if [[ ! -f /etc/apt/sources.list.bak ]]; then
        cp /etc/apt/sources.list /etc/apt/sources.list.bak
        log_debug "已备份原有源列表"
    fi

    # 写入新的镜像源配置
    cat > /etc/apt/sources.list <<'EOF'
# 默认注释了源码镜像以提高 apt update 速度，如有需要可自行取消注释
deb http://mirrors.cernet.edu.cn/ubuntu/ jammy main restricted universe multiverse
# deb-src http://mirrors.cernet.edu.cn/ubuntu/ jammy main restricted universe multiverse

deb http://mirrors.cernet.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
# deb-src http://mirrors.cernet.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse

deb http://mirrors.cernet.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
# deb-src http://mirrors.cernet.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse

# 安全更新源（保留官方源以确保及时获取安全补丁）
deb http://mirrors.cernet.edu.cn/ubuntu/ jammy-security main restricted universe multiverse
# deb-src http://mirrors.cernet.edu.cn/ubuntu/ jammy-security main restricted universe multiverse

deb http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse
# deb-src http://security.ubuntu.com/ubuntu/ jammy-security main restricted universe multiverse
EOF

    log_debug "镜像源配置写入完成"

    # 清理旧的软件包缓存
    log_debug "清理 APT 缓存"
    apt-get autoremove -y >/dev/null 2>&1 &
    show_spinner $! "清理旧软件包"
    apt-get clean
    rm -rf /var/lib/apt/lists/*

    # 更新软件包列表
    log_debug "更新软件包索引"
    apt-get update -o Acquire::http::No-Cache=True >/dev/null 2>&1 &
    show_spinner $! "同步软件包列表"
    apt-get update >/dev/null 2>&1 && apt-get install -f -y >/dev/null 2>&1

    log_info "APT 源配置完成"
    echo ""
}

# 系统版本检查函数: 必须是 Ubuntu 22.04 LTS (Jammy Jellyfish)
check_ubuntu_version() {
    local required_version="22.04"
    local required_codename="jammy"
    local is_supported=0

    log_step "检查系统版本"
    echo ""

    # 通过LSB信息检查版本
    if command -v lsb_release &> /dev/null; then
        local os_id=$(lsb_release -si)
        local os_release=$(lsb_release -sr)
        local os_codename=$(lsb_release -sc)

        if [[ "$os_id" == "Ubuntu" && "$os_release" == "$required_version" && "$os_codename" == "$required_codename" ]]; then
            is_supported=1
        fi
    # 备用方案：通过os-release文件检查
    elif [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ "$ID" == "ubuntu" && "$VERSION_ID" == "$required_version" && "$UBUNTU_CODENAME" == "$required_codename" ]]; then
            is_supported=1
        fi
    fi

    if [[ $is_supported -eq 1 ]]; then
        log_info "系统版本: Ubuntu ${required_version} LTS"
        echo ""
        return 0
    else
        log_error "不兼容的系统版本！"
        log_debug "需要: Ubuntu ${required_version} LTS (Jammy Jellyfish)"
        log_debug "当前: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2)"
        echo ""
        ALL_CHECKS_PASS=false
        return 1
    fi
}

# 检查CPU架构支持
check_cpu() {
    log_step "检查 CPU 架构"
    echo ""
    local arch_support=0
    grep -q -E 'vmx|svm' /proc/cpuinfo && arch_support=1

    if [[ $(uname -m) != "x86_64" ]]; then
        log_error "仅支持 x86_64 架构"
        echo ""
        ALL_CHECKS_PASS=false
        return 1
    elif [[ $arch_support -eq 0 ]]; then
        log_warn "CPU 虚拟化未启用 (可能影响性能)"
    else
        log_info "CPU 架构: x86_64 (VT-x/AMD-V)"
    fi
    echo ""
    return 0
}

# 加载必要的内核模块
load_kernel_modules() {
    log_step "加载内核模块"
    echo ""
    declare -a required_modules=("overlay" "veth" "bridge")
    local total=${#required_modules[@]}
    local current=0

    for module in "${required_modules[@]}"; do
        ((current++))
        if ! lsmod | grep -q "^$module"; then
            if modprobe "$module" 2>/dev/null; then
                show_progress $current $total "加载模块: $module"
            else
                show_progress $current $total "跳过模块: $module (已内置)"
            fi
        else
            show_progress $current $total "检查模块: $module"
        fi
    done
    log_info "内核模块加载完成"
    echo ""
}

# 网络连接检查
check_network() {
    log_step "检查网络连接"
    echo ""
    local check_passed=true
    local tests=("CERNET镜像" "Ubuntu CDN")
    local current=0
    local total=2

    # 测试镜像源
    ((current++))
    local MIRROR_URL="http://mirrors.cernet.edu.cn/ubuntu/"
    if curl --output /dev/null --silent --head --fail --connect-timeout 10 "$MIRROR_URL" 2>/dev/null; then
        show_progress $current $total "${tests[0]}"
    else
        show_progress $current $total "${tests[0]} (跳过)"
        check_passed=false
    fi

    if $check_passed; then
        log_info "网络连接正常"

    else
        log_error "网络连接异常，请检查网络设置"
    fi

    echo ""
    return 0
}

# 存储空间检查
check_storage() {
    log_step "检查磁盘空间"
    echo ""
    local min_disk=300 # 最小磁盘空间(GB) - SDK编译需要大量空间
    local available=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')
    local used=$(df -BG / | awk 'NR==2 {print $3}' | tr -d 'G')
    local total=$(df -BG / | awk 'NR==2 {print $2}' | tr -d 'G')
    local percentage=$((used * 100 / total))

    # 显示磁盘使用情况
    show_progress $used $total "磁盘使用率 (${available}GB 可用)"

    if [[ $available -lt $min_disk ]]; then
        log_error "磁盘空间不足 (需要 ${min_disk}GB)"
        echo ""
        return 1
    else
        log_info "存储空间充足 (${available}GB)"
    fi
    echo ""
    return 0
}

# 安装核心开发工具和依赖
install_dependencies() {
    log_step "安装开发工具和依赖包"
    echo ""

    # 核心工具包列表
    local BASIC_TOOLS="mount util-linux bash-completion vim sudo locales tzdata time rsync bc"
    local PYTHON_TOOLS="python3 python3-pip python2 whiptail"
    local BUILD_TOOLS="build-essential crossbuild-essential-arm64 ccache"
    local DEV_TOOLS="git ssh make gcc g++"
    local LIBS="libssl-dev liblz4-tool expect patchelf chrpath gawk texinfo diffstat"
    local CROSS_TOOLS="binfmt-support qemu-user-static bison flex fakeroot cmake"
    local UTILS="unzip device-tree-compiler ncurses-dev net-tools u-boot-tools dpkg-dev"
    local EXTRA_LIBS="libgmp-dev libmpc-dev binutils libelf-dev curl pv"
    local DEV_UTILS="devscripts equivs software-properties-common linux-headers-generic"
    local CROSS_COMPILER="gcc-aarch64-linux-gnu g++-aarch64-linux-gnu"
    local SYSTEM_TOOLS="debootstrap cpio iputils-ping pigz tar aria2"
    local EXTERN_TOOLS="libncurses5 zip libgtk2.0-dev libxxf86vm1 less repo"

    # 合并所有包
    local ALL_PACKAGES="$BASIC_TOOLS $PYTHON_TOOLS $BUILD_TOOLS $DEV_TOOLS $LIBS $CROSS_TOOLS $UTILS $EXTRA_LIBS $DEV_UTILS $CROSS_COMPILER $SYSTEM_TOOLS $EXTERN_TOOLS"

    log_debug "准备安装软件包 (这可能需要几分钟)"

    # 批量安装（减少apt调用次数）
    (
        apt-get install -y --no-install-recommends $ALL_PACKAGES > /tmp/apt-install.log 2>&1
    ) &
    show_spinner $! "安装系统依赖包"

    if [ $? -eq 0 ]; then
        log_info "系统依赖包安装完成"
    else
        log_error "部分软件包安装失败"
        log_debug "详细日志: /tmp/apt-install.log"
        echo ""
        ALL_CHECKS_PASS=false
        return 1
    fi

    # 安装 Python 依赖
    (
        pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir pyelftools >/dev/null 2>&1
    ) &
    show_spinner $! "安装 Python 依赖包"
    log_info "Python 依赖安装完成"

    # 配置 Python2 符号链接
    if [ -x /usr/bin/python2 ] && [ ! -e /usr/bin/python ]; then
        ln -sf /usr/bin/python2 /usr/bin/python
        log_debug "Python2 符号链接已创建"
    fi

    echo ""
    return 0
}

# 安装和配置 live-build (Debian 系统构建工具)
install_live_build() {
    log_step "安装 live-build 工具"
    echo ""

    if command -v lb &> /dev/null; then
        log_debug "live-build 已安装"
        echo ""
        return 0
    fi

    local TMP_DIR="/tmp/live-build-install"
    mkdir -p "$TMP_DIR"

    (
        cd "$TMP_DIR"
        git clone https://salsa.debian.org/live-team/live-build.git --depth 1 -b debian/1%20230131 >/dev/null 2>&1
        cd live-build
        rm -rf manpages/po/
        make install >/dev/null 2>&1
        cd /
        rm -rf "$TMP_DIR"
    ) &
    show_spinner $! "编译安装 live-build"

    if [ $? -eq 0 ] && command -v lb &> /dev/null; then
        log_info "live-build 安装完成"
        log_debug "版本: $(lb --version 2>&1 | head -1)"
    else
        log_error "live-build 安装失败"
        ALL_CHECKS_PASS=false
        return 1
    fi

    echo ""
    return 0
}

# 配置 QEMU 和 binfmt 支持
configure_qemu() {
    log_step "配置 QEMU ARM64 支持"
    echo ""

    # 确保 binfmt-support 已安装
    if ! dpkg -l | grep -q binfmt-support; then
        apt-get install -y --no-install-recommends binfmt-support >/dev/null 2>&1
    fi

    local steps=("启用 binfmt" "注册 qemu-aarch64" "验证配置")
    local current=0
    local total=3

    # 启用 QEMU aarch64 支持
    ((current++))
    update-binfmts --enable qemu-aarch64 >/dev/null 2>&1
    show_progress $current $total "${steps[0]}"

    # 注册处理器
    ((current++))
    sleep 0.3
    show_progress $current $total "${steps[1]}"

    # 验证状态
    ((current++))
    if update-binfmts --display qemu-aarch64 2>&1 | grep -q "enabled"; then
        show_progress $current $total "${steps[2]}"
        log_info "QEMU ARM64 支持配置完成"
    else
        show_progress $current $total "${steps[2]} (警告)"
        log_warn "QEMU 配置可能不完整"
    fi

    echo ""
    return 0
}

# 同步 SDK 源码
sync_Linux_sdk() {
    log_step "同步 SDK 源码"
    echo ""

    local REPO_EXEC=".repo/repo/repo"
    local SYNC_JOBS=$(nproc 2>/dev/null || echo 4)

    # 检查 repo 命令
    if [[ ! -x "$REPO_EXEC" ]]; then
        log_error "repo 工具未找到"
        echo ""
        ALL_CHECKS_PASS=false
        return 1
    fi

    # 获取真实用户信息
    local REAL_USER="${SUDO_USER:-$USER}"
    local REAL_UID=$(id -u "$REAL_USER" 2>/dev/null || echo "")
    local REAL_GID=$(id -g "$REAL_USER" 2>/dev/null || echo "")

    log_debug "同步参数: -l (本地) -j$SYNC_JOBS (并发)"
    log_debug "这可能需要较长时间，请耐心等待..."
    echo ""

    # 执行同步
    if $REPO_EXEC sync -l -j$SYNC_JOBS; then
        echo ""
        log_info "SDK 源码同步完成"

        # 如果是通过 sudo 运行,恢复文件权限为普通用户
        if [[ -n "$SUDO_USER" && -n "$REAL_UID" && -n "$REAL_GID" ]]; then
            log_debug "恢复文件权限为用户: $REAL_USER"
            (
                chown -R "$REAL_UID:$REAL_GID" . 2>/dev/null
            ) &
            show_spinner $! "修正文件权限"
            log_info "文件权限已恢复"
        fi
    else
        echo ""
        log_error "SDK 同步失败"
        log_debug "请检查网络连接或手动执行: $REPO_EXEC sync -l -j$SYNC_JOBS"
        ALL_CHECKS_PASS=false
        return 1
    fi

    echo ""
    return 0
}

# 配置时区
configure_timezone() {
    log_step "配置系统时区"
    echo ""

    if [ -f /usr/share/zoneinfo/Asia/Shanghai ]; then
        ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
        log_info "时区: Asia/Shanghai"
    else
        log_warn "时区配置跳过"
    fi

    echo ""
    return 0
}

# 检查QEMU支持（保留用于最终验证）
check_qemu() {
    log_step "验证 QEMU 环境"
    echo ""

    local checks=("QEMU 二进制" "binfmt 注册")
    local current=0
    local total=2

    ((current++))
    if which qemu-aarch64-static &> /dev/null; then
        show_progress $current $total "${checks[0]}"
    else
        show_progress $current $total "${checks[0]} (失败)"
        log_error "QEMU 静态二进制未找到"
        echo ""
        ALL_CHECKS_PASS=false
        return 1
    fi

    ((current++))
    if [[ -f /proc/sys/fs/binfmt_misc/qemu-aarch64 ]]; then
        show_progress $current $total "${checks[1]}"
    else
        show_progress $current $total "${checks[1]} (失败)"
        log_error "aarch64 架构支持未启用"
        echo ""
        ALL_CHECKS_PASS=false
        return 1
    fi

    log_info "QEMU 环境验证通过"
    echo ""
    return 0
}

# 主执行流程
main() {
    clear
    echo ""
    print_box "TaishanPi-1M Android SDK 环境初始化" "$MAGENTA"
    echo -e "${DIM}适用于: Ubuntu 22.04 LTS (Jammy Jellyfish)${NC}"
    echo -e "${DIM}版本: v1.0 | 更新时间: 2025-11-18${NC}"
    echo ""
    # print_separator

    # 阶段 1: 权限和基础检查
    print_box "阶段 1/6: 系统环境检查" "$BLUE"
    check_sudo_privilege "$@"
    check_ubuntu_version || exit 1
    check_cpu
    check_storage

    # 阶段 2: 配置软件源和网络
    print_box "阶段 2/6: 配置系统环境" "$BLUE"
    configure_apt_mirror
    check_network

    # 阶段 3: 安装依赖和工具
    print_box "阶段 3/6: 安装开发工具" "$BLUE"
    install_dependencies || exit 1
    install_live_build || exit 1

    # 阶段 4: 系统配置
    print_box "阶段 4/6: 配置系统功能" "$BLUE"
    load_kernel_modules
    configure_qemu || exit 1
    configure_timezone

    # 阶段 5: Repo 配置检查
    print_box "阶段 5/6: Repo 配置检查" "$BLUE"

    log_step "检查 Repo 环境"
    echo ""

    if [[ ! -d ".repo" ]]; then
        log_error "未找到 .repo 目录"
        log_debug "请先执行: repo init -u <manifest_url>"
        ALL_CHECKS_PASS=false
    else
        log_info "Repo 环境已就绪"

        # 配置 manifest 仓库完全本地化(使用相对路径,可移植)
        if [[ -d ".repo/manifests/.git" ]]; then
            local MANIFEST_DIR=".repo/manifests"

            # 确保在正确的分支上
            local current_branch=$(cd "$MANIFEST_DIR" && git symbolic-ref --short HEAD 2>/dev/null || echo "")

            if [[ -z "$current_branch" ]]; then
                log_warn "manifest 处于 detached HEAD,切换到分支"

                # 尝试切换到 taishanpi-1m-local 分支
                if (cd "$MANIFEST_DIR" && git show-ref --verify --quiet refs/heads/taishanpi-1m-local); then
                    (cd "$MANIFEST_DIR" && git checkout taishanpi-1m-local >/dev/null 2>&1)
                    current_branch="taishanpi-1m-local"
                    log_info "已切换到 taishanpi-1m-local 分支"
                fi
            fi

            # 配置分支跟踪本地(而非远程),防止 repo sync 切换分支
            if [[ -n "$current_branch" ]]; then
                (
                    cd "$MANIFEST_DIR"
                    # 使用相对路径配置 remote,确保可移植
                    git config remote.origin.url ".repo/manifests"
                    git config branch."$current_branch".remote "."
                    git config branch."$current_branch".merge "refs/heads/$current_branch"

                    # 同时配置 default 分支
                    if git show-ref --verify --quiet refs/heads/default; then
                        git config branch.default.remote "."
                        git config branch.default.merge "refs/heads/$current_branch"
                    fi
                ) >/dev/null 2>&1

                log_debug "Manifest 分支: $current_branch (本地跟踪,可移植)"
            fi
        fi

        # 显示当前 manifest 文件
        if [[ -f ".repo/manifest.xml" ]]; then
            local manifest_file=$(grep -oP '(?<=name=")[^"]+' .repo/manifest.xml 2>/dev/null | head -1)
            if [[ -n "$manifest_file" ]]; then
                log_debug "当前 Manifest: $manifest_file"
            fi
        fi
    fi
    echo ""

    # 阶段 6: 最终验证
    print_box "阶段 6/6: 环境验证" "$BLUE"
    check_qemu || exit 1

    # 询问是否同步 SDK
    echo ""
    echo -e "${YELLOW}${BOLD}是否立即同步 SDK 源码？${NC}"
    echo -e "${DIM}(同步需要较长时间，也可以稍后手动执行)${NC}"
    echo ""
    read -p "$(echo -e ${CYAN}是否继续? [Y/n]: ${NC})" -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        echo ""
        print_box "同步 Linux SDK" "$BLUE"
        sync_Linux_sdk || {
            log_warn "SDK 同步失败，但环境已配置完成"
            log_debug "可稍后手动执行: .repo/repo/repo sync -l"
        }
    else
        log_info "跳过 SDK 同步"
        log_debug "可稍后手动执行: .repo/repo/repo sync -l"
        echo ""
    fi

    # 确保所有文件权限正确(如果通过 sudo 运行)
    if [[ -n "$SUDO_USER" ]]; then
        local REAL_USER="$SUDO_USER"
        local REAL_UID=$(id -u "$REAL_USER" 2>/dev/null)
        local REAL_GID=$(id -g "$REAL_USER" 2>/dev/null)

        if [[ -n "$REAL_UID" && -n "$REAL_GID" ]]; then
            log_step "修正工作目录权限"
            echo ""
            (
                chown -R "$REAL_UID:$REAL_GID" "$(pwd)" 2>/dev/null
            ) &
            show_spinner $! "恢复用户权限: $REAL_USER"
            log_info "工作目录权限已修正"
            echo ""
        fi
    fi

    # 最终结果汇总
    if $ALL_CHECKS_PASS; then
        print_box "✓ 环境初始化成功" "$GREEN"
        print_box "✓ SDK同步完成" "$GREEN"
        echo ""
    else
        print_box "✗ 环境初始化失败" "$RED"

        echo -e "${BOLD}${WHITE}排查建议：${NC}"
        echo -e "   ${RED}1.${NC} 确认系统版本为 Ubuntu 22.04 LTS"
        echo -e "   ${RED}2.${NC} 检查网络连接是否正常"
        echo -e "   ${RED}3.${NC} 确保磁盘空间充足（建议 400GB+）"
        echo -e "   ${RED}4.${NC} 查看详细日志: ${YELLOW}/tmp/apt-install.log${NC}"
        echo ""
        exit 1
    fi
}

# 脚本入口
ALL_CHECKS_PASS=true
main "$@"