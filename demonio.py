#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import logging.handlers
import os
import time
from daemon import runner
import Funciones 
from time import time
from time import sleep


class App():
   def __init__(self):
      self.stdin_path      = '/dev/null'
      self.stdout_path     = '/dev/tty'
      self.stderr_path     = '/dev/tty'
      self.pidfile_path    =  '/var/run/test.pid'
      self.pidfile_timeout = 1

   def run(self):
      estatus_c=False
      estatus_e=False
      nombre_archivo_imagen='/home/ubuntu/calculo_temperatura/imagenes_llama/Llama.tiff'
      nombre_archivo_intensidad='/home/ubuntu/calculo_temperatura/espectro_llama/espectro.txt'
      nombre_archivo_wavelengths='/home/ubuntu/calculo_temperatura/espectro_llama/wavelength.txt'
      nombre_archivo_calibracion='/home/ubuntu/calculo_temperatura/espectro_llama/calib.txt'
      nombre_archivo_configuracion='/home/ubuntu/calculo_temperatura/configuracion.txt'
      nombre_archivo_buffet='/home/ubuntu/calculo_temperatura/archivos_buffet/Bufet.txt'
      nombre_archivo_buffet_soot='/home/ubuntu/calculo_temperatura/archivos_buffet/Bufet_soot.txt'
      nombre_archivo_buffet_tiempo='/home/ubuntu/calculo_temperatura/archivos_buffet/Bufet_tiempo.txt'
      Funciones.crear_archivos_de_datos(nombre_archivo_buffet)
      Funciones.crear_archivos_de_datos(nombre_archivo_buffet_soot)
      ip=Funciones.cargar_ip(nombre_archivo_configuracion)
      puerto=Funciones.cargar_puerto(nombre_archivo_configuracion)
      t_exposicion=Funciones.cargar_tiempo_exposicion(nombre_archivo_configuracion)
      f_adquisicion=Funciones.cargar_frecuencia_adquicision(nombre_archivo_configuracion)
      ganancia=Funciones.cargar_ganancia(nombre_archivo_configuracion)
      p_ancho=Funciones.cargar_ancho(nombre_archivo_configuracion)
      p_alto=Funciones.cargar_alto(nombre_archivo_configuracion)
      offset_x=Funciones.cargar_offsetx(nombre_archivo_configuracion)
      offset_y=Funciones.cargar_offsety(nombre_archivo_configuracion)
      t_integracion=Funciones.cargar_tiempo_integracion(nombre_archivo_configuracion)
      Funciones.comprobar_ip(ip,logger)
      servidor="opc.tcp://"+ip+":"+puerto  
      nombre_sensor=Funciones.cargar_nombre_sensor(nombre_archivo_configuracion)
      f1=open(nombre_archivo_buffet_tiempo,"w")
      f1.write('|tiempo_camara | tiempo_espectrometro | tiempo_algoritmo | tiempo_soot | tiempo_opc |\n')
      f1.close()
      asd=Funciones.open_spect(t_integracion,logger)#conexion de espectrometro
      camara=Funciones.conectar_camara(logger)#conexion de camara
      #Funciones.configurar(camara)
      Funciones.configurar(camara,t_exposicion,f_adquisicion,ganancia,p_ancho,p_alto,offset_x,offset_y)#configuracion de camara
      while True:
         f1=open(nombre_archivo_buffet_tiempo,"a")
         
         #adquisicion de imagenes
         start_time = time()
         #estatus_c=Funciones.save_image(nombre_archivo_imagen,logger)#estado camara
         camara=Funciones.obtener_imagen(camara,nombre_archivo_imagen,t_exposicion,f_adquisicion,ganancia,p_ancho,p_alto,offset_x,offset_y,logger)
         estatus_c=camara!=0
         tiempo_camara= time() - start_time
         
         #adquisicion de espectro
         start_time = time()
         #estatus_e=Funciones.save_spect(nombre_archivo_intensidad,nombre_archivo_wavelengths,logger) #False#estado espectrometro
         asd=Funciones.obtener_espectro(asd,nombre_archivo_intensidad,nombre_archivo_wavelengths,t_integracion,logger)
         estatus_e=asd!=0
         tiempo_espectrometro= time() - start_time
         
         #calculo de variables TF
         start_time = time()
         Funciones.algoritmos_radg_TF(nombre_archivo_imagen,nombre_archivo_intensidad,nombre_archivo_wavelengths,nombre_archivo_calibracion,nombre_archivo_buffet,logger)
         tiempo_algoritmo= time() - start_time
         
         #calculo de variables sootpropensity
         start_time = time()
         d_soot=Funciones.Soot_propensity(nombre_archivo_imagen,logger)
         tiempo_soot= time() - start_time
         
         #Escritura en servidor OPC
         start_time = time()
         Funciones.escribir_soot_en_bufer(nombre_archivo_buffet_soot,d_soot) #linea de paso mientras se establecen las variables para soot_propensity
         Funciones.escribir_datos(servidor,nombre_archivo_buffet,nombre_sensor,estatus_c,estatus_e,logger)  
         Funciones.escribir_datos2(servidor,nombre_archivo_buffet_soot,nombre_sensor,logger)  
         tiempo_opc= time() - start_time
         
        #tiempos de ejecucion de secciones de codigo
         f1.write('| '+str(tiempo_camara)+' | '+str(tiempo_espectrometro)+' | '+str(tiempo_algoritmo)+' | '+str(tiempo_soot)+' | '+str(tiempo_opc)+'|\n')
         f1.close()
         sleep(0.1)

         

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