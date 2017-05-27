id=$(docker run -d postgres:9.6)
sleep 10s
docker run --link $id:pg olx
