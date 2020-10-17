import subprocess
from time import time
from pypylon import pylon
from opcua import Client
from opcua.client.ua_client import UaClient
from opcua import ua
import numpy as np 
from datetime import datetime
import socket
import logging


def save_image(ruta,logger):
  img = pylon.PylonImage()
  tlf = pylon.TlFactory.GetInstance()
  try:
      cam = pylon.InstantCamera(tlf.CreateFirstDevice())     
      try:
          cam.Open()
          #configuracion de parametros de tamano
          cam.Width.SetValue(1920)
          cam.Height.SetValue(1200)
          cam.OffsetX=0 #debe ser multiplo de 2
          cam.OffsetY=0  #debe ser multiplo de 2
          #inicia captura de imagenes
          cam.StartGrabbing()
          result=cam.RetrieveResult(2000)
          #codigo para guardar la imagen
          img.AttachGrabResultBuffer(result)     
          img.Save(pylon.ImageFileFormat_Tiff, ruta)
          img.Release()
          cam.StopGrabbing()
          return True
      except: # excepcion en caso de que no se pueda generar la coneccion
          cam.Close()
          return False
      finally:#si finaliza la obtencion de la foto
          cam.Close()         
  except: #escepcion en caso de que la camara no este conectada
      logger.error("Error conectando la camara") 
      return False  

def Tf(ruta,logger):
  try:
    completed = subprocess.run(['./calculo_Tf',ruta], check=True, cwd="/home/ubuntu/calculo_temperatura/") 
  except subprocess.CalledProcessError as err:
      logger.error('Error en la ejecucion del algoritmo:', err)

def cambiar_nombre(server,nodo,nombre,logger):
  client = Client(server)
  try:
      client.connect()#conecta el servidor
      var=client.get_node("ns=1;s="+nodo)#se obtiene el primer nodo
      variable2=var.get_children()
      tamano=np.size(variable2)
      if tamano==5:
        nombre=variable2[0].set_value(nombre)
      else:
        logger.warning("No se encuentra el nodo en el servidor opc")
      client.disconnect()
  except:
	    #desconeccion
      logger.error("No se puede conectar con el servidor opc")
      #client.disconnect()


def cambiar_tipo(server,nodo,tipo,logger):
  client = Client(server)
  try:
      client.connect()
      #conecta el servidor
      var=client.get_node("ns=1;s="+nodo)#se obtiene el primer nodo
      variable2=var.get_children()
      tamano=np.size(variable2)
      if tamano==5:
        tipo=variable2[1].set_value(tipo)
        tiempo=variable2[2].get_value()
        val=variable2[3].get_value()
        status=variable2[4].get_value()
      else:
        logger.warning("No se encuentra el nodo en el servidor opc")
      client.disconnect()
  except:
	    #desconeccion
      logger.error("No se puede conectar con el servidor opc")
      #client.disconnect()

def cambiar_valor(server,nodo,tiemp,valor,estatus,logger):
  client = Client(server)
  try:
      client.connect()#conecta el servidor
      var=client.get_node("ns=1;s="+nodo)#se obtiene el primer nodo
      variable2=var.get_children()
      tamano=np.size(variable2)
      datetime_object = datetime.strptime(tiemp, '%d/%m/%Y %H:%M:%S')
      if tamano>0:
        tiempo=variable2[2].set_value(datetime_object)
        val=variable2[3].set_value(valor)
        status=variable2[4].set_value(estatus)
      else:
        logger.warning("No se encuentra el nodo en el servidor opc")
      client.disconnect()
  
  except: 
      logger.error("No se puede conectar con el servidor opc")
      #client.disconnect()

def escribir_datos(server,archivo,nodo,status,logger):
  f = open (archivo,'r')
  linea=f.readlines()[-1] 
  datos=linea.split()
  tiempo=datos[0]+' '+datos[1]
  valor=datos[2]
  cambiar_valor(server,nodo,tiempo,valor,status,logger)
  f.close() 

def cargar_ip(archivo):
  f = open (archivo,'r')
  linea=f.readlines()
  return linea[0][-14:-1]
  f.close()

def cargar_puerto(archivo):
  f = open (archivo,'r')
  linea=f.readlines()
  return linea[1][-5:-1]
  f.close()
  
def cargar_nombre_tf_direct(archivo):
  f = open (archivo,'r')
  linea=f.readlines()
  return linea[2][31:-1]
  f.close()

def cargar_nombre_tf_rec_spect(archivo):
  f = open (archivo,'r')
  linea=f.readlines()
  return linea[3][34:-1]
  f.close()

def comprobar_ip(addr,logger):
  try:
      #crea socket 
      socket_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      socket.setdefaulttimeout(1)
      result = socket_obj.connect_ex((addr,22)) #se escanea uno de los puertos estandar abiertos 22,80
      if(result):
        logger.error("El host/puerto no se encuentra disponible")
      else:
        logger.info("El host/puerto esta disponible")
      socket_obj.close()
  except:
      logger.error("Fallo el escaneo de ip/puertos")
      
def crear_archivos_de_datos(archivo,archivo1):
  f=open(archivo,"w")
  f.close()
  f=open(archivo1,"w")
  f.close()