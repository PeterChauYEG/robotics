import matplotlib.pyplot as plt
from transformers import pipeline
import numpy as np
from PIL import Image

img_raw = plt.imread("/Users/peterchau/robotics/jetbot-ros/src/img.jpg")
# print(img_raw.shape)
# img_np = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
# #
img = Image.fromarray(img_raw)

classifier = pipeline("object-detection")
prediction = classifier(img)
print(prediction)
