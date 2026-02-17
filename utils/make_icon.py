from PIL import Image

img = Image.open("/Users/nishant/VSCodeProjects/youtube-to-mp3/assets/app_icon.png")

img.save("app_icon.icns", format="ICNS")
print("Success! Created app_icon.icns")