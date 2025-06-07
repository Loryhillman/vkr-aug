import numpy as np
from PIL import Image

def add_noise(image, noise_type='gaussian', **kwargs):
    """Добавление шума к изображению (в градациях серого)"""
    if image.mode != 'L':
        raise ValueError("Ожидается изображение в градациях серого (mode='L')")

    img_array = np.array(image)

    if noise_type == 'gaussian':
        stddev = kwargs.get('stddev', 10)
        noise = np.random.normal(0, stddev, img_array.shape)
        noised = img_array + noise
        noised = np.clip(noised, 0, 255).astype(np.uint8)

    elif noise_type == 'salt_pepper':
        amount = kwargs.get('amount', 0.05)
        s_vs_p = kwargs.get('salt_vs_pepper', 0.5)
        noised = img_array.copy()

        num_salt = np.ceil(amount * img_array.size * s_vs_p)
        num_pepper = np.ceil(amount * img_array.size * (1.0 - s_vs_p))

        coords = [np.random.randint(0, i - 1, int(num_salt)) for i in img_array.shape]
        noised[coords[0], coords[1]] = 255

        coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in img_array.shape]
        noised[coords[0], coords[1]] = 0

    else:
        raise ValueError(f"Неизвестный тип шума: {noise_type}")

    return Image.fromarray(noised)