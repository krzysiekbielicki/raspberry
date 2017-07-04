#!/usr/bin/env python

if __name__ == "__main__":

   import PIL.Image
   import glob
   import i2c_ssd1306
   import pigpio
   import time

   pi = pigpio.pi() # Connect to local Pi.

   ssd = i2c_ssd1306.i2c_ssd1306(pi, 1, 0x3c, 128, 32)

   ssd.stop_scroll()

   screen = [0]*1024

   for i in range(1024):
      screen[i] = i & 255

   ssd.display(screen)

   time.sleep(5)

   ssd.clear_display()

   for i in range(64):
      ssd.draw_pixel(i, i, 1)

   ssd.display()

   time.sleep(1)

   #ssd.start_scroll_left(0, 3, 0)

   for img in glob.glob("/usr/share/pixmaps/*"):
      print(img)
      try:
         f=PIL.Image.open(img)
         ssd.image(f)
         time.sleep(2)
      except:
         pass

   ssd.cancel()

   pi.stop()
