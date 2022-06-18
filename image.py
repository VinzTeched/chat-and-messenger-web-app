from turtle import width
from PIL import Image, ImageDraw, ImageFont
import random


def get_initials(fullname):
  xs = (fullname)
  name_list = xs.split()

  initials = ""

  for name in name_list:  # go through each name
    initials += name[0].upper()  # append the initial

  return initials

def createImage(name):
    width = 512
    height = 512
    message = get_initials(name)
    message = message
    font = ImageFont.truetype("arial.ttf", size=250)
    

    img = Image.new('RGB', (width, height), color=(10, 10, 90))

    imgDraw = ImageDraw.Draw(img)

    textWidth, textHeight = imgDraw.textsize(message, font=font)
    xText = (width - textWidth) / 2.2
    yText = (height - textHeight) / 2.8

    imgDraw.text((xText, yText), message, font=font, fill=(240, 240, 240))

    n = random.randint(10,99999999)

    img.save(f"static/images/users/result{n}.png", "PNG")

    return f"result{n}.png"
