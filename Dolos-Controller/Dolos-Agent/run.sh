#!/bin/bash
# Enable and start systemd-resolved and avahi-daemon
sudo systemctl enable systemd-resolved --now
sudo systemctl enable avahi-daemon --now

CONTAINER_NAME="agent"

endlessh_ports="$@"

IFS=' ' read -r -a endlessh_ports_array <<< "$endlessh_ports"

sudo docker rm -f agent

sudo docker build -t $CONTAINER_NAME .

sudo apparmor_parser -r -W docker-network

sudo touch /var/log/dolos.log

sudo docker run --cap-add=NET_ADMIN --net=host --privileged -d -it --security-opt apparmor=docker-network -v /var/log:/var/log --name $CONTAINER_NAME $CONTAINER_NAME

sudo docker exec $CONTAINER_NAME /bin/bash -c "cd $CONTAINER_NAME && ./run.sh ${endlessh_ports_array[@]}"
sudo docker exec $CONTAINER_NAME /bin/bash -c "cd $CONTAINER_NAME && ./run.sh ${endlessh_ports_array[@]}"
sudo docker exec $CONTAINER_NAME /bin/bash -c "cd $CONTAINER_NAME && python3 PacketAnalyzer.py"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IP_SHUFFLE_SCRIPT="$SCRIPT_DIR/ip_shuffle.sh"

sudo chmod +x "$IP_SHUFFLE_SCRIPT" 2>/dev/null

if ! sudo crontab -l 2>/dev/null | grep -q "$IP_SHUFFLE_SCRIPT"; then
    (sudo crontab -l 2>/dev/null; echo "* * * * * $IP_SHUFFLE_SCRIPT" --cron) | sudo crontab -
    echo "✅ Added IP shuffle crontab"
fi

sudo systemctl enable cron --now
