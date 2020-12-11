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
from scipy import misc
import math
import abel
from scipy.stats import mode
from scipy.stats import moment
from scipy.stats import skew
from scipy.stats import kurtosis
from skimage.transform import resize
from skimage.transform import rescale
from seabreeze.spectrometers import Spectrometer

################################################adquisicion de imagenes#################################################################

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

################################################adquisicion de espectros#################################################################
def save_spect(ruta_intensidad,ruta_longitud,logger):
  try:
      spec = Spectrometer.from_first_available()
      spec.integration_time_micros(20000)
  
      wavelengths = spec.wavelengths() #lee longitudes de onda wavelengths in (nm)
      intensities = spec.intensities() #lee intensidades measured intensity array in (a.u.)

      f = open (ruta_longitud,'wb')
      np.savetxt(f, np.array(wavelengths))
      f.close()
      f = open (ruta_intensidad,'wb')
      np.savetxt(f, intensities)
      f.close()
      return True
      
  except: #excepcion en caso de que el espectrometro no este conectada
      logger.error("Error conectando el espectrometro") 
      return False  
 
################################################calculo de radg y TF#################################################################      

def algoritmos_radg_TF(ruta_img,ruta_intensidad,ruta_longitud,ruta_calibracion,ruta_buffet,logger):
  try:
    completed = subprocess.run(['./calculo_Tf',ruta_img,ruta_intensidad,ruta_longitud,ruta_calibracion,ruta_buffet], check=True, cwd="/home/ubuntu/calculo_temperatura/") 
  except subprocess.CalledProcessError as err:
      logger.error('Error en la ejecucion del algoritmo:', err)
      
      
################################################calculo de soot propensity#################################################################      

def calculo_soot_propensity(grey,abel,vv,uu):
    SP=np.zeros((uu,vv))  # matriz para el soot
    kappa=np.zeros((uu,vv)) #matriz para el kappa
    for n1 in range(vv):
      for n2 in range(uu):
        if ((abel[n2,n1]>0)):
          kappa[n2,n1]=abel[n2,n1]/grey[n2,n1]
          SP[n2,n1]=550*kappa[n2,n1]/(6*math.pi*0.26)
        else:
          SP[n2,n1]=0           
    return SP    

def calculo_de_medidas_estadisticas(soot):
    #eliminamos el 2% de las muestras
    n=soot[np.nonzero(soot)]
    perc98_fv=np.percentile(n, 98, interpolation='midpoint') 
    perc2_fv=np.percentile(n, 2, interpolation='midpoint') 
    result = np.where(n <= perc98_fv)
    n1=n[result]
    result = np.where(n1 >= perc2_fv)
    Soot=n1[result]
    
    #crear lista de string
    medidas =['0','0','0','0','0','0','0','0','0','0','0','0']
    
    #variables de medida
    avg_fv=np.mean(Soot[np.nonzero(Soot)]) #media
    medidas[0]=str(avg_fv)
    median_fv=np.median(Soot[np.nonzero(Soot)]) #mediana
    medidas[1]=str(median_fv)
    std_fv=np.std(Soot[np.nonzero(Soot)]) #desviacion estandar
    medidas[2]=str(std_fv)
    moda_fv=float(mode(Soot[np.nonzero(Soot)]).mode) #moda
    medidas[3]=str(moda_fv)
    perc50_fv=np.percentile(Soot[np.nonzero(Soot)], 50, interpolation='midpoint')
    medidas[4]=str(perc50_fv)
  
    #momentos
    mom2_fv = moment(Soot[np.nonzero(Soot)], 2, axis=0)#momento de orden 2
    medidas[5]=str(mom2_fv)
    mom3_fv = moment(Soot[np.nonzero(Soot)], 3, axis=0)#momento de orden 3
    medidas[6]=str(mom3_fv)
    mom4_fv = moment(Soot[np.nonzero(Soot)], 4, axis=0)#momento de orden 4
    medidas[7]=str(mom4_fv)
 
    #simetria
    skew1_fv=3*(avg_fv-moda_fv)/std_fv #Primer coeficiente de asimetria de Pearson
    medidas[8]=str(skew1_fv)
    skew2_fv=3*(avg_fv-median_fv)/std_fv #Segundo momento de asimetria de Pearson
    medidas[9]=str(skew2_fv)
    skew3_fv=skew(Soot[np.nonzero(Soot)])#coeficiente de asimetria
    medidas[10]=str(skew3_fv)
  
    #curtosis
    kurt_fv=kurtosis(Soot[np.nonzero(Soot)])#coeficiente de curtosis
    medidas[11]=str(kurt_fv)
    
    return medidas
   
     

def Soot_propensity(ruta,logger):
  try:
      img = misc.imread(ruta) # Leemos la imagen  #ruta 'imagenes_llama/Llama (1).tiff'
      img= rescale(img/255, 0.5,mode='constant')#reescalar la imagen, nomalizacion de 0-1

      img_mono = img[:,:,0]*0.2989 + img[:,:,1]*0.5870 + img[:,:,2]*0.1140#transformacion rgb-grey
      foreground= (img_mono >= 0.02)#obtencion de la mascara
      img_mono2 = img_mono*foreground/1000e-6 #aplicamos mascara y reescalamos por tiempo de exposicion
   
      inverse_abel = abel.Transform(img_mono2, direction='inverse', method='three_point').transform
      inverse_abel=inverse_abel*foreground #aplicamos mascara a abel
    
      [uu,vv]=inverse_abel.shape #calculamos tamano de abel
      fv_temp=calculo_soot_propensity(img_mono ,inverse_abel,vv,uu)#calculamos fraccion de hollin.
      medi=calculo_de_medidas_estadisticas(fv_temp)
      return medi #fin de la funcion
  
  except: #excepcion en caso de que el algoritmo falle
      medi=['0','0','0','0','0','0','0','0','0','0','0','0']
      logger.error("Error calculando soot propensity") 
      #print("error en el calculo de soot propensity")
      return medi
      
def escribir_soot_en_bufer(bufer,soot): #funcion que escribe las variables en el archivo buffet
  f=open(bufer,"a")
  f.write(soot[0])
  f.write(" ")
  f.write(soot[1])
  f.write(" ")
  f.write(soot[2])
  f.write(" ")
  f.write(soot[3])
  f.write(" ")
  f.write(soot[4])
  f.write(" ")
  f.write(soot[5])
  f.write(" ")
  f.write(soot[6])
  f.write(" ")
  f.write(soot[7])
  f.write(" ")
  f.write(soot[8])
  f.write(" ")
  f.write(soot[9])
  f.write(" ")
  f.write(soot[10])
  f.write(" ")
  f.write(soot[11])
  f.write("\n")
  f.close()


      

################################################Escritura en servidor#################################################################

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

def cambiar_valor2(server,nodo,avg_fv,median_fv,std_fv,moda_fv,perc50_fv,mom2_fv,mom3_fv,mom4_fv,skew1_fv,skew2_fv,skew3_fv,kurt_fv,logger):
  client = Client(server)
  try:
      client.connect()#conecta el servidor
      var=client.get_node("ns=1;s="+nodo)#se obtiene el primer nodo
      variable2=var.get_children()
      tamano=np.size(variable2)
      #datetime_object = datetime.strptime(tiemp, '%d/%m/%Y %H:%M:%S')
      if tamano>0:
        variable2[10].set_value(avg_fv)
        variable2[11].set_value(median_fv)
        variable2[12].set_value(std_fv)
        variable2[13].set_value(moda_fv)
        variable2[14].set_value(perc50_fv)
        variable2[15].set_value(mom2_fv)
        variable2[16].set_value(mom3_fv)
        variable2[17].set_value(mom4_fv)
        variable2[18].set_value(skew1_fv)
        variable2[19].set_value(skew2_fv)
        variable2[20].set_value(skew3_fv)
        variable2[21].set_value(kurt_fv)
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

def escribir_datos2(server,archivo,nodo,logger):
  f = open (archivo,'r')
  linea=f.readlines()[-1] 
  datos=linea.split()
  cambiar_valor2(server,nodo,datos[0],datos[1],datos[2],datos[3],datos[4],datos[5],datos[6],datos[7],datos[8],datos[9],datos[10],datos[11],logger)
  f.close() 

################################################carga de datos desde archivo de configuracion#################################################################

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

################################################comprobacion de ip y puerto#################################################################  

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

################################################creacion de archivos buffet#################################################################
      
def crear_archivos_de_datos(archivo):
  f=open(archivo,"w")
  f.close()