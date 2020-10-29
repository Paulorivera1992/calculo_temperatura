from opcua import Client
from opcua.client.ua_client import UaClient
from opcua import ua
import numpy as np 
from datetime import datetime
import time
from os import system

def leer_valor(server,nodo):
  client = Client("opc.tcp://192.168.1.107:4840")
  try:
      client.connect()#conecta el servidor
      var=client.get_node("ns=1;s="+nodo)#se obtiene el primer nodo
      variable2=var.get_children()
      tamano=np.size(variable2)
      if tamano>0:
        tiempo=variable2[0].get_value()#tiempo
        #date_time = tiempo.strftime('%d/%m/%Y %H:%M:%S')
        tfd=variable2[1].get_value()#tf_direct
        tfrs=variable2[2].get_value()#tf_rec_spect
        rgtfd=variable2[3].get_value()#rg_tf_direct
        rgtfrs=variable2[4].get_value()#rg_tf_rec_spect
        rgrs=variable2[5].get_value()#rg_rec_spect
        rt=variable2[6].get_value()#rt
        sp=variable2[7].get_value()#soot propensity
        ec=variable2[8].get_value()#status camara
        ee=variable2[9].get_value()#status espectrometro
        system("clear")
        print("\n\n\n Tiempo:              ",tiempo,"\n tf_direct:           ",tfd,"\n tf_rec_spect:        ",tfrs,"\n Rg_tf_direc:         ",rgtfd)
        print(" Rg_tf_rec_spec:      ",rgtfrs,"\n RG_rec_spect:        ",rgrs,"\n Rt:                  ",rt,"\n hollin:              ",sp)
        print(" Estado camara:       ",ec,"\n Estado Espectrometro:",ee,"\n")
      else:
        print("No se encuentra el nodo en el servidor opc")
      
      client.disconnect()
  
  except: 
      print("No se puede conectar con el servidor opc")

while(True):
  leer_valor("opc.tcp://192.168.1.107:4840","sensor 10")     
  time.sleep(1) 
  