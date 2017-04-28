
Build the Docker image

```
cd docker
sudo docker build -t alarmserver .
```

Run the image

`sudo docker run -p 9443:8111 -it -v /host/path/config:/config alarmserver
