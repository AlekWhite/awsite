from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from model import FishOfTheWeek as fishBowl
import threading
import shutil
import time
import pytz
import os

"""
from PIL import ImageFont, ImageDraw, Image
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import random
import time
import PIL
import os
import re
"""

class FishOfTheWeek(threading.Thread):

    def __init__(self, app):
        super(FishOfTheWeek, self).__init__()
        self.app = app
        self.daemon = True
        self.public_dir = os.path.join(self.app.static_folder, 'fish', 'public')
        self.private_dir = os.path.join(self.app.static_folder, 'fish', 'private')
        if (not os.path.isdir(self.public_dir)) or (not os.path.isdir(self.private_dir)):
            print("MISSING FISH FILES")
        self.make_fish_img_public()
        
    # pick a new random fish from the db
    def pick_new_fish(self):
        time.sleep(0.6)
        with self.app.app_context():
            for i in range(100):
                fish = fishBowl.get_random_fish()
                if os.path.isfile(os.path.join(self.private_dir, fish.fish_name + ".png")):
                    fish.mark_as_chosen()
                    time.sleep(0.2)
                    self.make_fish_img_public()
                    return
        
    # copy 12 recent fish img to public directory 
    def make_fish_img_public(self):

        # clear old public files 
        public_files = set(os.listdir(self.public_dir))
        for file in public_files:
            if os.path.isfile(file):
                os.remove(file)

        # read db, make chosen fish public
        with self.app.app_context():
            fish_list = fishBowl.get_fish()
        for fish in fish_list:
            filename = fish.fish_name + ".png"
            if os.path.isfile(os.path.join(self.private_dir, fish.fish_name + ".png")):
                print(f"Image for {fish.fish_name} is public")
                shutil.copy2(os.path.join(self.private_dir, filename), os.path.join(self.public_dir, filename))

    # schedule the selection of a new fish (once a week)
    def run(self):
        scheduler = BackgroundScheduler(timezone=pytz.timezone('America/New_York'))
        scheduler.add_job(
            func=self.pick_new_fish,
            trigger=CronTrigger(
                day_of_week='sun',  
                hour=23,            
                minute=59,          
                second=59,          
                timezone=pytz.timezone('America/New_York')
            ),
            id='weekly_fish_update',
            name='Update fish of the week',
            replace_existing=True)
        scheduler.start()
        print(f"Next run: {scheduler.get_job('weekly_fish_update').next_run_time}")
        try:
            while True:
                threading.Event().wait(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()

    """
    Functions for generating fish images 

    # gets image link from wiki html
    def getImageLink(self, wikiLink):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
        page = requests.get(wikiLink, stream=False, headers=headers)
        if page.status_code != 200:
            print(f"error {page.status_code}")
            return None
        soup = BeautifulSoup(page.content, 'html.parser')
        dataStr = soup.prettify
        relHtmlData = [exp.group() for exp in re.finditer(r"<a.*>", str(dataStr))]
        img_link = None
        for elm in relHtmlData:
            if "class=\"mw-file-description\"" in elm:
                link = [exp.group() for exp in re.finditer(r"src=\".*\" s", str(elm))][0][5:][:-3]
                if ".png" not in link:
                    img_link = "http:" + link
                    break
        if not img_link:
            return None
        try:
            return [exp.group() for exp in re.finditer(r".+(.jpg/)", img_link)][0][:-1].replace("/thumb", "")
        except Exception as e:
            print(f"failed to find a large image: {e} {img_link}")
            return img_link

    # generates display image for a fish
    def makeFishImg(self, fish):
        
        # download wiki image
        imageLink = self.getImageLink(fish.wiki_url)
        if not imageLink:
            return False
        print(imageLink)
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'}
            img_data = requests.get(imageLink, stream=False, headers=headers)
        except Exception as e:
            print(f"image request failed: {e}")
            return False
        if not img_data.ok:
            print("image request returns error")
            return "nc"
        image_path = os.path.join(self.app.root_path, 'static', 'fish_img', 'inputImg.jpg')
        with open(image_path, 'wb') as handler:
            handler.write(img_data.content)

        # open image with PIL
        MAX_DIM = 500
        inputImage = Image.open(image_path)

        # scale the image
        factor = MAX_DIM / max(inputImage.size)
        pixels = inputImage.load()
        newImg = PIL.Image.new(mode="RGB", size=(int(inputImage.size[0] * factor), int(inputImage.size[1] * factor)), )
        newPix = newImg.load()
        for i in range(newImg.size[0]):
            for j in range(newImg.size[1]):
                newPix[i, j] = pixels[int(i/factor), int(j/factor)]

        # find smaller side
        side = 0
        if (MAX_DIM - newImg.size[side]) < (MAX_DIM - newImg.size[1]):
            side = 1

        # find colors for bg
        pixels = newImg.load()
        colors = []
        color = [0, 0, 0, 0]
        for i in range(newImg.size[0]):
            for j in range(newImg.size[1]):
                color = [color[0]+pixels[i, j][0], color[1]+pixels[i, j][1], color[2]+pixels[i, j][2], color[3]+1]
                if ((i, j)[side] == newImg.size[side]-1) and ((i, j)[1-side] % 50 == 0):
                    colors.append((int(color[0]/color[3]), int(color[1]/color[3]), int(color[2]/color[3])))

        # copy scaled image to final canvas
        finalImg = PIL.Image.new(mode="RGB", size=(MAX_DIM, MAX_DIM))
        finPix = finalImg.load()
        offset = 0
        if MAX_DIM-newImg.size[side] != 0:
            offset = int((MAX_DIM-newImg.size[side])/2)
        for i in range(newImg.size[0]):
            for j in range(newImg.size[1]):
                if side == 0:
                    finPix[i+offset, j] = newPix[i, j]
                else:
                    finPix[i, j+offset-1] = newPix[i, j]

        # add bg
        for i in range(0, finalImg.size[0], 4):
            for j in range(0, finalImg.size[1], 4):
                if ((i, j)[side] < offset) or ((i, j)[side] >= newImg.size[side] + offset + 4):
                    color = colors[random.randint(0, len(colors)-1)]
                    for x in range(3):
                        for y in range(3):
                            if (i+x < MAX_DIM) and (j+y < MAX_DIM):
                                finPix[i+x, j+y] = color

        # add border
        for j in range(5):
            for i in range(MAX_DIM):
                finPix[j, i] = (35, 35, 35)
                finPix[MAX_DIM-1-j, i] = (35, 35, 35)
        for j in range(5):
            for i in range(MAX_DIM):
                finPix[i, j] = (35, 35, 35)
                finPix[i, MAX_DIM-1-j] = (35, 35, 35)

        # add text and save 
        draw = ImageDraw.Draw(finalImg)
        file_path = os.path.join(self.app.root_path, 'static', 'fish_img', 'Consolas.ttf')
        font = ImageFont.truetype(file_path, 24)
        draw.rectangle(((0, 0), (MAX_DIM, 30)), fill="black")
        draw.text((15, 5), fish.fish_name + ":", (255, 255, 255), font=font)
        file_path = os.path.join(self.app.root_path, 'static', 'fish_img', fish.fish_name + ".png")
        print(f"saving {file_path} {finalImg}")
        finalImg.save(file_path)
        return True

    # generates a display image for each fish
    def generate_all_fish_img(self):
        pass_count = 0
        run_count = 0
        with self.app.app_context():
            all_fish = fishBowl.get_all()
            for i in range(0, len(all_fish)):
                fish = all_fish[i]
                if os.path.isfile( os.path.join(self.app.root_path, 'static', 'fish_img', fish.fish_name + ".png")):
                    continue
                time.sleep(2)                
                run_count += 1
                while True:
                    try:
                        res = self.makeFishImg(fish)
                        if res == True:
                            pass_count += 1
                            print(f"DONE: [{fish.fish_name}] (i={i}) ({pass_count}/{run_count})")
                            break
                        elif res == "nc":
                            print(f"CON-FAILED [{fish.fish_name}] (i={i}) ({pass_count}/{run_count})")
                            time.sleep(120)
                        else:
                            print(f"FAILED-ABOVE [{fish.wiki_url}] (i={i}) ({pass_count}/{run_count})")
                            break
                    except Exception as e:
                        if "Max retries exceeded with url" in str(e):
                            print(f"CON-FAILED [{fish.fish_name}] (i={i}) ({pass_count}/{run_count})")
                            time.sleep(120)
                        else:
                            print(f"FAILED-NON-NORMAL [{fish.fish_name}] (i={i}) ({pass_count}/{run_count}) \n {e}")
                            break
    """             
