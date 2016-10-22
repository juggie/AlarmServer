FROM python:2.7

RUN git clone https://github.com/juggie/AlarmServer
RUN cd AlarmServer && git checkout master

RUN pip install tornado

CMD [ "python", "AlarmServer/alarmserver.py", "-c", "config/alarmserver.cfg" ]

EXPOSE 8111
