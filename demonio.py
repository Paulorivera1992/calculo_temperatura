#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import logging.handlers
import os
import time
from daemon import runner
import Funciones 


class App():
   def __init__(self):
      self.stdin_path      = '/dev/null'
      self.stdout_path     = '/dev/tty'
      self.stderr_path     = '/dev/tty'
      self.pidfile_path    =  '/var/run/test.pid'
      self.pidfile_timeout = 1

   def run(self):
      estatus_c=False;
      estatus_e=False;
      nombre_archivo_imagen='/home/ubuntu/calculo_temperatura/imagenes_llama/Llama.tiff'
      nombre_archivo_intensidad='/home/ubuntu/calculo_temperatura/espectro/intensidad.txt'
      nombre_archivo_wavelengths='/home/ubuntu/calculo_temperatura/espectro/longitud.txt'
      nombre_archivo_configuracion='/home/ubuntu/calculo_temperatura/configuracion.txt'
      nombre_archivo_buffet='/home/ubuntu/calculo_temperatura/archivos_buffet/Bufet.txt'
      nombre_archivo_buffet_soot='/home/ubuntu/calculo_temperatura/archivos_buffet/Bufet_soot.txt'
      Funciones.crear_archivos_de_datos(nombre_archivo_buffet)
      ip=Funciones.cargar_ip(nombre_archivo_configuracion)
      puerto=Funciones.cargar_puerto(nombre_archivo_configuracion)
      Funciones.comprobar_ip(ip,logger)
      servidor="opc.tcp://"+ip+":"+puerto  
      nombre_sensor=Funciones.cargar_nombre_sensor(nombre_archivo_configuracion)
      while True:
         estatus_c=Funciones.save_image(nombre_archivo_imagen,logger)#estado camara
         estatus_e=Funciones.save_spect(nombre_archivo_intensidad,nombre_archivo_wavelengths,logger) #False#estado espectrometro
         Funciones.algoritmos_radg_TF(nombre_archivo_imagen,logger)
         d_soot=Funciones.Soot_propensity(nombre_archivo_imagen,logger)
         Funciones.escribir_soot_en_bufer(nombre_archivo_buffet_soot,d_soot) #liena de paso mientras se establecen las variables para soot_propensity
         Funciones.escribir_datos(servidor,nombre_archivo_buffet,nombre_sensor,estatus_c,estatus_e,logger)  
         Funciones.escribir_datos2(servidor,nombre_archivo_buffet_soot,nombre_sensor,logger)  

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