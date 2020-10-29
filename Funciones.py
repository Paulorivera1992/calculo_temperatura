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

################################################calculo de radg y TF#################################################################

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

def algoritmos(ruta,logger):
  try:
    completed = subprocess.run(['./calculo_Tf',ruta], check=True, cwd="/home/ubuntu/calculo_temperatura/") 
  except subprocess.CalledProcessError as err:
      logger.error('Error en la ejecucion del algoritmo:', err)

def cambiar_valor(server,nodo,tiemp,TFD,TFRS,RGTFD,RGTFRS,RGRS,RT,SP,EC,EE,logger):
  client = Client(server)
  try:
      client.connect()#conecta el servidor
      var=client.get_node("ns=1;s="+nodo)#se obtiene el primer nodo
      variable2=var.get_children()
      tamano=np.size(variable2)
      datetime_object = datetime.strptime(tiemp, '%d/%m/%Y %H:%M:%S')
      if tamano>0:
        variable2[0].set_value(datetime_object)
        variable2[1].set_value(TFD)
        variable2[2].set_value(TFRS)
        variable2[3].set_value(RGTFD)
        variable2[4].set_value(RGTFRS)
        variable2[5].set_value(RGRS)
        variable2[6].set_value(RT)
        variable2[7].set_value(SP)
        variable2[8].set_value(EC)
        variable2[9].set_value(EE)
      else:
        logger.warning("No se encuentra el nodo en el servidor opc")
      
      client.disconnect()
  
  except: 
      logger.error("No se puede conectar con el servidor opc")
      

def escribir_datos(server,archivo,nodo,status_camara,status_espectrometro,logger):
  f = open (archivo,'r')
  linea=f.readlines()[-1] 
  datos=linea.split()
  tiempo=datos[0]+' '+datos[1]
  cambiar_valor(server,nodo,tiempo,datos[2],datos[3],datos[4],datos[5],datos[6],datos[7],datos[8],status_camara,status_espectrometro,logger)
  f.close() 

def cargar_ip(archivo):
  f = open (archivo,'r')
  linea=f.readlines()[0]
  datos=linea.split()
  f.close()
  return datos[1]
  

def cargar_puerto(archivo):
  f = open (archivo,'r')
  linea=f.readlines()[1]
  datos=linea.split()
  f.close()
  return datos[1]
  
  
def cargar_nombre_sensor(archivo):
  nombre=""
  f = open (archivo,'r')
  linea=f.readlines()[2]
  datos=linea.split()
  if(np.size(datos)>2):
    for i in range(2,np.size(datos)):
      nombre=nombre+datos[i]+" "
  else:
    print("no se ha asignado nombre del sensor en el archivo de configuracion")
  f.close()
  return nombre
  

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
      
def crear_archivos_de_datos(archivo):
  f=open(archivo,"w")
  f.close()