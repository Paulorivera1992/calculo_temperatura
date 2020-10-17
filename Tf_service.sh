#!/bin/bash

# /etc/init.d/test

case "$1" in
   start)
      echo "Starting server"
      sudo python3 /home/ubuntu/calculo_temperatura/demonio.py start 
      ;;

   stop)
      echo "Stopping server"
      sudo python3 /home/ubuntu/calculo_temperatura/demonio.py stop
      ;;

   restart)
      echo "Restarting server"
      sudo python3 /home/ubuntu/calculo_temperatura/demonio.py restart
      ;;

   *)
      echo "Usage: /etc/init.d/Tf_service.sh {start|stop|restart}"
      exit 1
      ;;
esac
exit 0