#!/usr/bin/env python

import pigpio

class i2c_ssd1306:

   COMMAND = 0x00
   DATA    = 0x40

   I2C_ADDRESS = 0x3C

   # Fundamental commands
   SetContrastControl    = 0x81
   EntireDisplayOnRAMPix = 0xA4
   EntireDisplayOnAllPix = 0xA5
   SetNormalDisplay      = 0xA6
   SetInverseDisplay     = 0xA7
   SetDisplayOff         = 0xAE
   SetDisplayOn          = 0xAF

   # Scrolling commands
   RightHorizontalScroll            = 0x26
   LeftHorizontalScroll             = 0x27
   VerticalAndRightHorizontalScroll = 0x29
   VerticalAndLeftHorizontalScroll  = 0x2A
   DeactivateScroll                 = 0x2E
   ActivateScroll                   = 0x2F
   SetVerticalScrollArea            = 0xA3

   # Addressing setting commands
   SetLowerColumnStartAddress  = 0x00
   SetHigherColumnStartAddress = 0x10
   SetMemoryAddressingMode     = 0x20
   SetColumnAddress            = 0x21
   SetPageAddress              = 0x22
   SetPageStartAddress         = 0xB0

   # Hardware configuration commands
   SetDisplayStartLine = 0x40
   SetSegmentRemap     = 0xA0
   SetMultiplexRatio   = 0xA8
   SetCOMOutputInc     = 0xC0
   SetCOMOutputDec     = 0xC8
   SetDisplayOffset    = 0xD3
   SetCOMPinsCfg       = 0xDA

   # Timing & driving scheme setting commands
   SetDisplayClockCfg = 0xD5
   SetPrechargeCfg    = 0xD9
   SetVCOMDeselect    = 0xDB
   NOP                = 0xE3

   # Charge pump regulator commands
   ChargePumpCfg = 0x8D

   def clear_buffer(self):
      self.buffer = [0]*((self.width*self.height)>>3)

   def __init__(
      self, pi, bus, addr, width=128, height=64, use_charge_pump=True):

      self.pi = pi
      self.bus = bus
      self.addr = addr

      self.width = width
      self.height = height
      self.pages = height>>3

      self.use_charge_pump = use_charge_pump
      self.h = pi.i2c_open(bus, addr)

      self._initialise()

   def command(self, arg):

      if type(arg) is not list:
         arg = [arg]

      self.pi.i2c_write_device(self.h, [self.COMMAND] + arg)

   def data(self, arg):

      if type(arg) is not list:
         arg = [arg]

      while len(arg) > 512:
         self.pi.i2c_write_device(self.h, [self.DATA] + arg[:512])
         arg = arg[512:]

      if len(arg):
         self.pi.i2c_write_device(self.h, [self.DATA] + arg[:512])

   def _initialise(self):

      if self.height == 64:
         MultiplexRatio = 0x3F
         COMPinsCfg = 0x12
      else:
         MultiplexRatio = 0x1F
         COMPinsCfg = 0x02

      if self.use_charge_pump:
         Pump      = 0x14
         Precharge = 0xF1
         Contrast  = 0xCF
      else:
         Pump      = 0x10
         Precharge = 0x22
         Contrast  = 0x9F

      self.command([
         self.SetDisplayOff,
         self.SetMultiplexRatio,       MultiplexRatio,
         self.SetDisplayOffset,        0x00,
         self.SetDisplayStartLine|0x00,
         self.SetSegmentRemap|0x01,
         self.SetCOMOutputDec,
         self.SetCOMPinsCfg,           COMPinsCfg,
         self.SetContrastControl,      Contrast,
         self.EntireDisplayOnRAMPix,
         self.SetNormalDisplay,
         self.SetDisplayClockCfg,      0x80,

         self.ChargePumpCfg,           Pump,
         self.SetPrechargeCfg,         Precharge,

         self.SetMemoryAddressingMode, 0x00,
         self.SetVCOMDeselect,         0x00,

         self.SetDisplayOn])

   def set_contrast(self, contrast):
      self.command([self.SetContrastControl, contrast])

   def dim(self, dim):
      if dim:
         contrast = 0
      else:
         if self.use_charge_pump:
            contrast = 0x9F
         else:
            contrast = 0xCF

      self.set_contrast(contrast)

   def invert_display(self):
      self.command(self.SetInverseDisplay)

   def normal_display(self):
      self.command(self.SetNormalDisplay)

   def start_scroll_right(self, start, stop, speed):
      self.command([
         self.RightHorizontalScroll, 0x00, start, speed, stop, 0x01, 0xff,
         self.ActivateScroll])

   def start_scroll_left(self, start, stop, speed):
      self.command([
         self.LeftHorizontalScroll, 0x00, start, speed, stop, 0x01, 0xff,
         self.ActivateScroll])

   def stop_scroll(self):
      self.command(self.DeactivateScroll)

   def cancel(self):
      if self.h >= 0:
         self.pi.i2c_close(self.h)
         self.h = -1

   def display(self, screen=None):
      if screen is None:
         screen = self.buffer

      self.command([
         self.SetColumnAddress, 0, 127,
         self.SetPageAddress, 0, self.pages-1])

      self.data(screen)

   def image(self, image):

      if image.mode != '1':
         image = image.convert("1")

      (im_width, im_height) = image.size
      if im_width != self.width or im_height != self.height:
         image = image.resize((self.width, self.height))

      # Grab the raw data.

      flat = image.getdata()
      index = 0
      for page in range(self.pages):
         for x in range(self.width):
            bits = 0
            for bit in [0, 1, 2, 3, 4, 5, 6, 7]:
               bits = bits << 1
               if flat[((page*8+(7-bit))*self.width)+x] != 0:
                  bits = bits | 1
            self.buffer[index] = bits
            index += 1

      self.display()

   def draw_pixel(self, col, row, val):
      mem_row = row>>3
      mem_bit = row%8

      if row >= self.height:
         return

      p = (mem_row * self.width) + col

      if val:
         self.buffer[p] = self.buffer[p] | (1<<mem_bit)
      else:
         self.buffer[p] = self.buffer[p] & (~(1<<mem_bit))

   def clear_display(self):
      self.clear_buffer()
      self.display()
