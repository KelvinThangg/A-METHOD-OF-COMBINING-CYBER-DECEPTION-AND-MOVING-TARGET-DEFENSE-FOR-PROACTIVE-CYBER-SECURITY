#!/bin/bash

# --- CẤU HÌNH ---
INTERFACE="ens33"
GATEWAY="172.16.0.1"
DNS_SERVERS="8.8.8.8 1.1.1.1"
SUBNET_PREFIX="172.16"
IP_START=100
IP_END=254
MAX_ATTEMPTS=5
LOG_FILE="/var/log/ip_shuffle.log"

# --- CẤU HÌNH THỜI GIAN ---
MANUAL_INTERVAL=30
CRON_INTERVAL=300
COUNTER_FILE="/tmp/ip_shuffle_time"

# --- CẤU HÌNH NÂNG CAO ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEND_IP_SCRIPT="${SCRIPT_DIR}/send_ip_to_controller.sh"

# Hàm ghi log
log_message() {
    local timestamp=$(date '+%Y/%m/%d %H:%M:%S')
    echo "[$timestamp] [$$] $1" | tee -a "$LOG_FILE"
}

# --- CÁC HÀM CHỨC NĂNG ---

# Hàm kiểm tra xem có cần shuffle hay không (LOGIC MỚI ĐÁNG TIN CẬY)
need_shuffle() {
    local run_mode=$1

    if [ ! -f "$COUNTER_FILE" ]; then
        log_message "[INFO] Không tìm thấy file đếm thời gian. Thực hiện shuffle lần đầu."
        return 0
    fi

    local last_time=$(cat "$COUNTER_FILE")
    local current_time=$(date +%s)
    local elapsed=$((current_time - last_time))
    local interval
    local mode

    # ================== THAY ĐỔI QUAN TRỌNG TẠI ĐÂY ==================
    # Kiểm tra xem tham số đầu tiên có phải là '--cron' hay không
    if [ "$run_mode" == "--cron" ]; then
        interval=$CRON_INTERVAL
        mode="crontab"
    else
        interval=$MANUAL_INTERVAL
        mode="manual"
    fi
    # ===============================================================

    if [ "$elapsed" -ge "$interval" ]; then
        log_message "[INFO] [$mode] Đã $elapsed giây (yêu cầu $interval giây) kể từ lần shuffle cuối. Cần shuffle."
        return 0
    else
        local remaining=$((interval - elapsed))
        log_message "[INFO] [$mode] Chưa đến lúc shuffle. Còn lại $remaining giây."
        return 1
    fi
}

# (Các hàm get_current_ips_with_prefix, generate_random_ip, is_ip_available, change_ip, perform_shuffle giữ nguyên như phiên bản trước)
# ...
# Hàm lấy TẤT CẢ các IP và prefix hiện tại của interface
get_current_ips_with_prefix() {
    ip -4 addr show "$INTERFACE" | grep -oP 'inet \K[\d./]+'
}
# Hàm tạo IP ngẫu nhiên
generate_random_ip() {
    local octet3=$((RANDOM % 256))
    local octet4=$((RANDOM % (IP_END - IP_START + 1) + IP_START))
    echo "$SUBNET_PREFIX.$octet3.$octet4"
}
# Hàm kiểm tra IP có đang được sử dụng hay không
is_ip_available() {
    local ip_to_check=$1
    if ping -c 1 -W 1 "$ip_to_check" &>/dev/null; then
        log_message "[INFO] IP $ip_to_check đã có người dùng."
        return 1
    else
        log_message "[INFO] IP $ip_to_check khả dụng."
        return 0
    fi
}
# Hàm thay đổi IP một cách an toàn
change_ip() {
    local new_ip=$1
    local current_ips
    current_ips=$(get_current_ips_with_prefix)
    log_message "[ACTION] Bắt đầu thay đổi IP..."
    log_message "[INFO] Đang dừng k3s-agent..."
    systemctl stop k3s-agent
    if [ -n "$current_ips" ]; then
        log_message "[INFO] Đang xóa các IP cũ trên interface $INTERFACE..."
        while IFS= read -r ip_prefix; do
            log_message "       - Xóa IP: $ip_prefix"
            ip addr del "$ip_prefix" dev "$INTERFACE"
        done <<< "$current_ips"
    fi
    log_message "[INFO] Đang gán IP mới: $new_ip/16"
    ip addr add "$new_ip/16" dev "$INTERFACE" || return 1
    ip route del default &>/dev/null
    log_message "[INFO] Đang cấu hình gateway: $GATEWAY"
    ip route add default via "$GATEWAY" || return 1
    log_message "[INFO] Đang cấu hình DNS: $DNS_SERVERS"
    echo "" > /etc/resolv.conf
    for dns in $DNS_SERVERS; do
        echo "nameserver $dns" >> /etc/resolv.conf
    done
    log_message "[INFO] Đang khởi động lại k3s-agent..."
    systemctl start k3s-agent
    sleep 5
    if systemctl is-active --quiet k3s-agent; then
        local final_ip
        final_ip=$(ip -4 addr show "$INTERFACE" | grep -oP 'inet \K[\d.]+' | head -n 1)
        if [[ "$final_ip" == "$new_ip" ]]; then
            log_message "[SUCCESS] Cấu hình mạng mới thành công với IP: $final_ip"
            return 0
        else
            log_message "[ERROR] IP không được thay đổi đúng cách. IP hiện tại là $final_ip"
            return 1
        fi
    else
        log_message "[ERROR] k3s-agent khởi động lại thất bại."
        return 1
    fi
}
# Hàm thực hiện toàn bộ quá trình shuffle
perform_shuffle() {
    for ((attempt=1; attempt<=MAX_ATTEMPTS; attempt++)); do
        log_message "[INFO] Lần thử $attempt/$MAX_ATTEMPTS..."
        local NEW_IP
        NEW_IP=$(generate_random_ip)
        if is_ip_available "$NEW_IP"; then
            if change_ip "$NEW_IP"; then
                log_message "[SUCCESS] Hoàn tất shuffle, IP mới là $NEW_IP."
                log_message "[INFO] Cập nhật timestamp cho lần shuffle tiếp theo."
                date +%s > "$COUNTER_FILE"
                if [ -f "$SEND_IP_SCRIPT" ]; then
                    log_message "[INFO] Đang gửi IP mới đến controller..."
                    bash "$SEND_IP_SCRIPT" "$NEW_IP"
                fi
                return 0
            else
                log_message "[WARNING] Không thể cấu hình mạng với IP $NEW_IP. Thử lại với IP khác..."
            fi
        fi
    done
    log_message "[ERROR] Shuffle IP thất bại sau $MAX_ATTEMPTS lần thử. Cần can thiệp thủ công."
    return 1
}

# --- LOGIC CHÍNH ---

# Kiểm tra quyền root trước tiên
if [ "$EUID" -ne 0 ]; then
  echo "Lỗi: Script này cần được chạy với quyền root (sudo)."
  exit 1
fi

log_message "================== KIỂM TRA IP SHUFFLE =================="

# Chỉ thực hiện shuffle nếu đã đến lúc
# Truyền tham số đầu tiên ($1) vào hàm need_shuffle
if need_shuffle "$1"; then
    perform_shuffle
else
    log_message "[INFO] Bỏ qua."
fi