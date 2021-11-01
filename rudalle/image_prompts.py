import torch
import numpy as np


class ImagePrompts:

    def __init__(self, pil_image, borders, vae, device, crop_first=False):
        self.device = device
        self.vae = vae
        self.__init_image_prompts(pil_image, borders, crop_first)

    def __init_image_prompts(self, pil_image, borders, crop_first):
        img = self.preprocess_img(pil_image)
        self.image_prompts_idx, self.image_prompts = self.get_image_prompts(img, borders, crop_first)

    def preprocess_img(self, pil_img):
        img = torch.tensor(np.array(pil_img).transpose(2, 0, 1)) / 255.
        img = img.unsqueeze(0).to(self.device, dtype=torch.float32)

        return img

    def get_image_prompts(self, img, borders, crop_first=False):
        img = (2 * img) - 1
        if crop_first:
            assert borders['right'] + borders['left'] + borders['down'] == 0
            up_border = borders['up'] * 8
            _, _, [_, _, vqg_img] = self.vae.model.encode(img[:, :, :up_border, :])
        else:
            _, _, [_, _, vqg_img] = self.vae.model.encode(img)

        bs, vqg_img_w, vqg_img_h = vqg_img.shape
        mask = torch.zeros(vqg_img_w, vqg_img_h)
        if borders['up'] != 0:
            mask[:borders['up'], :] = 1.
        if borders['down'] != 0:
            mask[-borders['down']:, :] = 1.
        if borders['right'] != 0:
            mask[:, :borders['right']] = 1.
        if borders['left'] != 0:
            mask[:, -borders['left']:] = 1.
        mask = mask.reshape(-1).bool()

        image_prompts = vqg_img.reshape((bs, -1))
        image_prompts_idx = np.arange(vqg_img_w * vqg_img_h)
        image_prompts_idx = set(image_prompts_idx[mask])

        return image_prompts_idx, image_prompts
