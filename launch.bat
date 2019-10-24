@echo off
call env.bat
docker build -t pypow .
docker rm -f pypow
docker run -d -e MINER_NAME=%MINER_NAME% --name pypow pypow -k %KAFKA_ENDPOINT%
