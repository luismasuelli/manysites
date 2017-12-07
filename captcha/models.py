from django.db import models
from django.core.files.base import ContentFile
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.six import StringIO
from PIL import Image, ImageFont, ImageDraw
from .utils import encode_solution
import random
import os


SOLUTION_LENGTH = 6
SOLUTION_CHARS = 'abcdefhkmnprtuvwxyABCDEFGHJKLMNPRTUVWXY3468'
BACKGROUND_SIZE = (180, 40)
BACKGROUND_PATH = os.path.join(os.path.dirname(__file__), 'resources', 'images', 'background.png')
BASE_FONT_PATH = os.path.join(os.path.dirname(__file__), 'resources', 'fonts')
FONTS = ['DejaVuSans.ttf', 'DejaVuSansMono.ttf', 'DejaVuSerif.ttf']
FONT_MIN = 30
FONT_MAX = 35
BASE_TEXT_OFFSET = 7
OFFSET_MIN = -2
OFFSET_MAX = 8
ROTATION_MIN = -30
ROTATION_MAX = 31
YPOS_MIN = 8
YPOS_MAX = 12


class CaptchaImage(models.Model):
    """
    Holds a captcha image and its result, encrypted in SHA256
    """
    image = models.ImageField(upload_to='captcha', null=False, editable=False)
    key = models.CharField(max_length=40, null=False, editable=False, unique=True)

    @staticmethod
    def generate(salt):
        # Get a solution not being used right now
        while True:
            solution = ''.join(random.choice(SOLUTION_CHARS) for _ in range(SOLUTION_LENGTH))
            key = encode_solution(salt, solution)
            try:
                CaptchaImage.objects.get(key=key)
            except CaptchaImage.DoesNotExist:
                break

        bg_image = Image.open(BACKGROUND_PATH)
        offset = BASE_TEXT_OFFSET

        for character in solution:
            # Random font
            font_file = os.path.join(BASE_FONT_PATH, random.choice(FONTS))
            font = ImageFont.truetype(font_file, random.randrange(FONT_MIN, FONT_MAX))

            # Text image
            ch_image = Image.new('L', font.getsize(' %s ' % character), '#000000')
            draw = ImageDraw.Draw(ch_image)
            draw.text((0,0), ' %s ' % character, font=font, fill='#ffffff')
            ch_image = ch_image.rotate(random.randrange(ROTATION_MIN, ROTATION_MAX),
                                       expand=1, resample=Image.BILINEAR)
            ch_image = ch_image.crop(ch_image.getbbox())

            # Mask image
            mk_image = Image.new('L', BACKGROUND_SIZE)
            ypos = random.randrange(YPOS_MIN, YPOS_MAX)
            mk_image.paste(ch_image, (offset, ypos, ch_image.size[0] + offset, ch_image.size[1] + ypos))

            # Pasting image
            fg_image = Image.new('RGBA', BACKGROUND_SIZE, '#a6a6a6')
            bg_image = Image.composite(fg_image, bg_image, mk_image)

            # Changing offset
            offset += ch_image.size[0] + random.randrange(OFFSET_MIN, OFFSET_MAX)

        # Now we have bg_image and solution, we save it and return it.
        img_io = StringIO()
        bg_image.save(img_io, format='PNG')
        fn_image = ContentFile(img_io.getvalue(), '%s.jpg' % solution)
        return CaptchaImage.objects.create(key=key, image=fn_image)


@receiver(post_delete, sender=CaptchaImage)
def after_delete(sender, instance, *more, **stuff):
    """
    Cleanup of captcha images
    """
    path = instance.image.path
    if os.path.isfile(path):
        os.remove(path)