#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import logging.handlers
import os
import time
from daemon import runner
import Funciones_Tf 

class App():
   def __init__(self):
      self.stdin_path      = '/dev/null'
      self.stdout_path     = '/dev/tty'
      self.stderr_path     = '/dev/tty'
      self.pidfile_path    =  '/var/run/test.pid'
      self.pidfile_timeout = 1

   def run(self):
      estatus=False;
      Funciones_Tf.crear_archivos_de_datos('/home/ubuntu/calculo_temperatura/archivos_temperatura/Tf_direct.txt','/home/ubuntu/calculo_temperatura/archivos_temperatura/Tf_rec_spect.txt')
      ip=Funciones_Tf.cargar_ip('/home/ubuntu//calculo_temperatura/configuracion.txt')
      puerto=Funciones_Tf.cargar_puerto('/home/ubuntu/calculo_temperatura/configuracion.txt')
      Funciones_Tf.comprobar_ip(ip,logger)
      servidor="opc.tcp://"+ip+":"+puerto  
      nombre_tf_direct=Funciones_Tf.cargar_nombre_tf_direct('/home/ubuntu/calculo_temperatura/configuracion.txt')
      nombre_tf_rec_spect=Funciones_Tf.cargar_nombre_tf_rec_spect('/home/ubuntu/calculo_temperatura/configuracion.txt')
      Funciones_Tf.cambiar_tipo(servidor,nombre_tf_direct,"Tf_direct",logger)
      Funciones_Tf.cambiar_tipo(servidor,nombre_tf_rec_spect,"Tf_rec_spect",logger)
      Funciones_Tf.cambiar_nombre(servidor,nombre_tf_direct,"quemador1",logger)
      Funciones_Tf.cambiar_nombre(servidor,nombre_tf_rec_spect,"quemador1",logger)
      while True:
         nombre_archivo='/home/ubuntu/calculo_temperatura/imagenes_llama/Llama.tiff'
         estatus=Funciones_Tf.save_image(nombre_archivo,logger)
         logger.info('Procesando nueva imagen')
         Funciones_Tf.Tf(nombre_archivo,logger)
         Funciones_Tf.escribir_datos(servidor,'/home/ubuntu/calculo_temperatura/archivos_temperatura/Tf_direct.txt',nombre_tf_direct,estatus,logger)  
         Funciones_Tf.escribir_datos(servidor,'/home/ubuntu/calculo_temperatura/archivos_temperatura/Tf_rec_spect.txt',nombre_tf_rec_spect,estatus,logger) 

if __name__ == '__main__':
   app = App()
   logger = logging.getLogger("TFlog")
   logger.setLevel(logging.DEBUG)
   formatter = logging.Formatter("%(levelname)s:%(asctime)s - %(message)s")
   handler = logging.FileHandler("/home/ubuntu/calculo_temperatura/TF.log")
   handler = logging.handlers.RotatingFileHandler(filename='TF.log', mode='a', maxBytes=10000000, backupCount=1)
   handler.setFormatter(formatter)
   logger.addHandler(handler)
  
   serv = runner.DaemonRunner(app)
   serv.daemon_context.files_preserve=[handler.stream]
   serv.do_action()