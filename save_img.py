from pypylon import pylon
import platform
import time

def save_image(ruta):
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
  
          # codigo para obtener la matriz RGB sin guardar la imagen
          #converter = pylon.ImageFormatConverter()
          #converter.OutputPixelFormat = pylon.PixelType_RGB8packed
          #converted = converter.Convert(result)
          #image_rgb = converted.GetArray()
          #print("el tamano de la matriz es", image_rgb.shape)
  
          #codigo para guardar la imagen
          img.AttachGrabResultBuffer(result)     
          img.Save(pylon.ImageFileFormat_Tiff, ruta)

          img.Release()
          print("foto obtenida") 
      except:
          cam.StopGrabbing()
          cam.Close()
          
      finally:
          cam.StopGrabbing()
          cam.Close()
          
  except: 
      print("error de coneccion")   
      

filename = "imagenes_llama/saved_pypylon_img_1.tiff"

#while True:
save_image(filename)
time.sleep(2)