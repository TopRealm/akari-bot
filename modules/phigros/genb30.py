import os

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

from core.constants.path import assets_path, noto_sans_demilight_path
from core.logger import Logger
from core.utils.cache import random_cache_path

pgr_assets_path = os.path.join(assets_path, "modules", "phigros")

levels = {"EZ": 0, "HD": 1, "IN": 2, "AT": 3}


def drawb30(username, rks_acc, p3data, b27data):
    card_w, card_h = 384, 240
    cols, rows = 3, 10
    margin_top = 100
    margin_bottom = 30
    gap_between_p3_b27 = 30

    width = card_w * cols + 30
    height = card_h * rows + margin_top + gap_between_p3_b27 + margin_bottom
    final_img = Image.new("RGBA", (width, height), "#1e2129")

    font = ImageFont.truetype(noto_sans_demilight_path, 20)
    font2 = ImageFont.truetype(noto_sans_demilight_path, 15)
    font3 = ImageFont.truetype(noto_sans_demilight_path, 25)

    drawtext = ImageDraw.Draw(final_img)
    text1_width = font.getbbox(username)[2]
    drawtext.text(
        (final_img.width - text1_width - 20, 30), username, "#ffffff", font=font
    )
    rks_text = f"Rks Avg: {rks_acc}"
    text2_width = font.getbbox(rks_text)[2]
    drawtext.text(
        (final_img.width - text2_width - 20, 52), rks_text, "#ffffff", font=font
    )

    def draw_card(song_, x, y, label):
        try:
            split_id = song_[0].split(".")
            song_id = split_id[1]
            song_level = split_id[0]
            song_score = song_[1]["score"]
            song_rks = song_[1]["rks"]
            song_acc = song_[1]["accuracy"]
            song_base_rks = song_[1]["base_rks"]

            if not song_id:
                cardimg = Image.new("RGBA", (card_w, card_h), "black")
            else:
                imgpath = os.path.join(
                    pgr_assets_path, "illustration", f"{song_id.split('.')[0].lower()}.png"
                )
                if not os.path.exists(imgpath):
                    imgpath = os.path.join(
                        pgr_assets_path, "illustration", f"{song_id.lower()}.png"
                    )
                if not os.path.exists(imgpath):
                    cardimg = Image.new("RGBA", (card_w, card_h), "black")
                else:
                    cardimg = Image.open(imgpath)
                    if cardimg.mode != "RGBA":
                        cardimg = cardimg.convert("RGBA")
                    downlight = ImageEnhance.Brightness(cardimg)
                    img_size = downlight.image.size
                    resize_multiplier = card_w / img_size[0]
                    img_h = int(img_size[1] * resize_multiplier)
                    if img_h < card_h:
                        resize_multiplier = card_h / img_size[1]
                        resize_img_w = int(img_size[0] * resize_multiplier)
                        resize_img_h = int(img_size[1] * resize_multiplier)
                        crop_start_x = int((resize_img_w - card_w) / 2)
                        crop_start_y = int((resize_img_h - card_h) / 2)
                        cardimg = (
                            downlight.enhance(0.5)
                            .resize((resize_img_w, resize_img_h))
                            .crop(
                                (
                                    crop_start_x,
                                    crop_start_y,
                                    card_w + crop_start_x,
                                    card_h + crop_start_y,
                                )
                            )
                        )
                    elif img_h > card_h:
                        crop_start_y = int((img_h - card_h) / 2)
                        cardimg = (
                            downlight.enhance(0.5)
                            .resize((card_w, img_h))
                            .crop((0, crop_start_y, card_w, card_h + crop_start_y))
                        )
                    else:
                        cardimg = downlight.enhance(0.5).resize((card_w, img_h))

            triangle_img = Image.new("RGBA", (100, 100), "rgba(0,0,0,0)")
            draw = ImageDraw.Draw(triangle_img)
            draw.polygon(
                [(0, 0), (0, 100), (100, 0)],
                fill=["#11b231", "#0273b7", "#cd1314", "#383838"][levels[song_level]],
            )
            text_img = Image.new("RGBA", (70, 70), "rgba(0,0,0,0)")
            text_draw = ImageDraw.Draw(text_img)
            text1 = ["EZ", "HD", "IN", "AT"][levels[song_level]]
            text2 = str(round(song_base_rks, 1))
            text_size1 = font.getbbox(text1)
            text_size2 = font2.getbbox(text2)
            text_draw.text(
                (
                    (text_img.width - text_size1[2]) / 2,
                    (text_img.height - text_size1[3]) / 2,
                ),
                text1,
                font=font,
                fill="#FFFFFF",
            )
            text_draw.text(
                (
                    (text_img.width - text_size2[2]) / 2,
                    (text_img.height - text_size2[3]) / 2 + 20,
                ),
                text2,
                font=font2,
                fill="#FFFFFF",
            )
            triangle_img.alpha_composite(text_img.rotate(45, expand=True), (-25, -25))
            cardimg.alpha_composite(triangle_img.resize((75, 75)), (0, 0))

            draw_card = ImageDraw.Draw(cardimg)
            draw_card.text((20, 155), song_id, "#ffffff", font=font3)
            draw_card.text(
                (20, 180),
                f"Score: {song_score} Acc: {song_acc:.2f}%\nRks: {song_rks:.2f}",
                "#ffffff",
                font=font,
            )

            text_w, text_h = font.getbbox(label)[2:]
            draw_card.text(
                (card_w - text_w - 10, 10),
                label,
                "#ffffff",
                font=font,
            )

            final_img.alpha_composite(cardimg, (x, y))
        except Exception:
            Logger.exception()

    for idx, song in enumerate(p3data):
        x = 15 + card_w * idx
        y = margin_top
        label = f"φ{idx+1}"
        draw_card(song, x, y, label)

    for idx, song in enumerate(b27data):
        row = idx // cols
        col = idx % cols
        x = 15 + card_w * col
        y = margin_top + card_h + gap_between_p3_b27 + row * card_h
        label = f"#{idx+1}"
        draw_card(song, x, y, label)

    generated_text = "Generated by Teahouse Studios \"AkariBot\""
    text_width, text_height = font2.getbbox(generated_text)[2:]
    drawtext.text(
        (20, final_img.height - text_height - 5),
        generated_text,
        "#ffffff",
        font=font2
    )

    if __name__ == "__main__":
        final_img.show()
    else:
        savefilename = f"{random_cache_path()}.png"
        final_img.convert("RGB").save(savefilename)
        return savefilename
