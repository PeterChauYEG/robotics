import matplotlib.pyplot as plt
from transformers import pipeline
from PIL import Image

img_raw = plt.imread("/Users/peterchau/robotics/jetbot-ros/src/img.jpg")
img = Image.fromarray(img_raw)

classifier = pipeline("object-detection", model="hustvl/yolos-small")
prediction = classifier(img)
print(prediction)
