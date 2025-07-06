#!/bin/bash

ENDLESSH_PORTS=("$@")

ENDLESSH_JOBS=()

for PORT in "${ENDLESSH_PORTS[@]}"; do
    endlessh -p $PORT &
    ENDLESSH_JOBS+=($!)
done

echo "Starting PacketAnalyzer.py with Python 3.8"
python3.8 PacketAnalyzer.py 
#sudo docker exec $CONTAINER_NAME /bin/bash -c "cd $CONTAINER_NAME && python3 PacketAnalyzer.py"


for PID in "${ENDLESSH_JOBS[@]}"; do
    kill $PID
done
exit 0



