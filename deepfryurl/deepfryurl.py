import io
import math
import os
import time
import urllib.error
from sys import stdout
from urllib.request import urlopen

import cv2
import numpy as np
import progressbar
from PIL import Image

# return the length of vector v


def length(v):
    return np.sqrt(np.sum(np.square(v)))

# returns the unit vector in the direction of v


def normalise(v):
    return v/length(v)


def download_to_ram(url):
    # try to open url for n tries
    n = 10
    headers = {}
    headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"
    for i in range(n):
        try:
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req)
            break
        except urllib.error.HTTPError:
            time.sleep(1)
        except urllib.error.URLError:
            time.sleep(1)
    # save retrieved data to PIL image
    img = None
    try:
        img_bytes = response.read()
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except OSError as e:
        print("URL is not an image, skipping.\n")
    except UnboundLocalError as e:
        print(str(e))
    return img


def fry(img):
    # bulge at random coordinates
    [w, h] = [img.width - 1, img.height - 1]
    w *= np.random.random(1)
    h *= np.random.random(1)
    r = int(((img.width + img.height) / 10) * (np.random.random(1)[0] + 1))
    img = bulge(img, np.array([int(w), int(h)]), r, 3, 5, 1.8)

    # some finishing touches
    #print("Adding some finishing touches... ", end='')
    stdout.flush()
    img = add_noise(img, 0.2)
    img = change_contrast(img, 175)
    print("Done")

    return img


# Downloads image from url to RAM, fries it and saves to disk
def fry_url(url, n):
    # download image and check if image was downloaded successfully
    img = download_to_ram(url)
    if img is None:
        return

    # fry image n times
    for i in range(n):
        img = fry(img)

    print("Saving temporarily to disk for uploading...")
    home = os.path.expanduser('~')
    img.save(home+'/supreme-pybot/images/tmp.jpg')
    return True


def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))

    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)


def add_noise(img, factor):
    def noise(c):
        return c*(1+np.random.random(1)[0]*factor-factor/2)
    return img.point(noise)


# creates a bulge like distortion to the image
# parameters:
#   img = PIL image
#   f   = np.array([x, y]) coordinates of the centre of the bulge
#   r   = radius of the bulge
#   a   = flatness of the bulge, 1 = spherical, > 1 increases flatness
#   h   = height of the bulge
#   ior = index of refraction of the bulge material
def bulge(img, f, r, a, h, ior):
    # print("Creating a bulge at ({0}, {1}) with radius {2}... ".format(f[0], f[1], r))

    # load image to numpy array
    width = img.width
    height = img.height
    img_data = np.array(img)

    # ignore too large images
    if width*height > 3000*3000:
        return img

    # determine range of pixels to be checked (square enclosing bulge), max exclusive
    x_min = int(f[0] - r)
    if x_min < 0:
        x_min = 0
    x_max = int(f[0] + r)
    if x_max > width:
        x_max = width
    y_min = int(f[1] - r)
    if y_min < 0:
        y_min = 0
    y_max = int(f[1] + r)
    if y_max > height:
        y_max = height

    # make sure that bounds are int and not np array
    if isinstance(x_min, type(np.array([]))):
        x_min = x_min[0]
    if isinstance(x_max, type(np.array([]))):
        x_max = x_max[0]
    if isinstance(y_min, type(np.array([]))):
        y_min = y_min[0]
    if isinstance(y_max, type(np.array([]))):
        y_max = y_max[0]

    # array for holding bulged image
    bulged = np.copy(img_data)
    bar = progressbar.ProgressBar()
    for y in bar(range(y_min, y_max)):
        for x in range(x_min, x_max):
            ray = np.array([x, y])

            # find the magnitude of displacement in the xy plane between the ray and focus
            s = length(ray - f)

            # if the ray is in the centre of the bulge or beyond the radius it doesn't need to be modified
            if 0 < s < r:
                # slope of the bulge relative to xy plane at (x, y) of the ray
                m = -s/(a*math.sqrt(r**2-s**2))

                # find the angle between the ray and the normal of the bulge
                theta = np.pi/2 + np.arctan(1/m)

                # find the magnitude of the angle between xy plane and refracted ray using snell's law
                # s >= 0 -> m <= 0 -> arctan(-1/m) > 0, but ray is below xy plane so we want a negative angle
                # arctan(-1/m) is therefore negated
                phi = np.abs(np.arctan(1/m) - np.arcsin(np.sin(theta)/ior))

                # find length the ray travels in xy plane before hitting z=0
                k = (h+(math.sqrt(r**2-s**2)/a))/np.sin(phi)

                # find intersection point
                intersect = ray + normalise(f-ray)*k

                # assign pixel with ray's coordinates the colour of pixel at intersection
                if 0 < intersect[0] < width-1 and 0 < intersect[1] < height-1:
                    bulged[y][x] = img_data[int(
                        intersect[1])][int(intersect[0])]
                else:
                    bulged[y][x] = [0, 0, 0]
            else:
                bulged[y][x] = img_data[y][x]
    img = Image.fromarray(bulged)
    return img
