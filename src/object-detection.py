import matplotlib.pyplot as plt
from transformers import pipeline
from PIL import Image
import time

img_raw = plt.imread("/Users/peterchau/robotics/jetbot-ros/src/img.jpg")
img = Image.fromarray(img_raw)

classifier = pipeline("image-classification", model="microsoft/resnet-50")

start_time = time.time()
prediction = classifier(img)
print('took ', time.time() - start_time, ' seconds')
print(prediction)
