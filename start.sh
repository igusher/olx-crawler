docker run -d --name postgres postgres:9.6
docker run --link postgres:pg olx
