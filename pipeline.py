import random
from augmentor.rotate import rotate_image
from augmentor.flip import flip_image
from augmentor.noise import add_noise
from augmentor.shift import shift_image
from augmentor.brightness import change_brightness
from config.augmentation_config import augmentation_config


def apply_augmentation(image, augmentation_type):
    """Применяет одну случайную аугментацию к изображению"""
    if augmentation_type == 'rotate' and augmentation_config['rotate']['enabled']:
        angle = random.uniform(*augmentation_config['rotate']['params']['angle_range'])
        return rotate_image(image, angle=angle)

    elif augmentation_type == 'flip' and augmentation_config['flip']['enabled']:
        mode = random.choice(augmentation_config['flip']['params']['mode_options'])
        return flip_image(image, mode=mode)

    elif augmentation_type == 'noise' and augmentation_config['noise']['enabled']:
        noise_type = random.choice(augmentation_config['noise']['types'])

        if noise_type == 'gaussian':
            std = random.uniform(*augmentation_config['noise']['params']['gaussian']['std_range'])
            return add_noise(image.convert('L'), noise_type='gaussian', std=std)

        elif noise_type == 'salt_pepper':
            amount = random.uniform(*augmentation_config['noise']['params']['salt_pepper']['amount_range'])
            return add_noise(
                image.convert('L'),
                noise_type='salt_pepper',
                amount=amount,
                salt_vs_pepper=augmentation_config['noise']['params']['salt_pepper']['salt_vs_pepper']
            )

    elif augmentation_type == 'shift' and augmentation_config['shift']['enabled']:
        max_shift = random.uniform(*augmentation_config['shift']['params']['max_shift_range'])
        return shift_image(image, max_shift=max_shift)

    elif augmentation_type == 'brightness' and augmentation_config['brightness']['enabled']:
        factor = random.uniform(*augmentation_config['brightness']['params']['factor_range'])
        return change_brightness(image, factor=factor)

    return image


def process_images(image, target_size, volume_level='low'):
    """
    Генерирует N аугментированных версий изображения
    на основе случайных комбинаций доступных аугментаций.
    """

    available = [a for a in augmentation_config['available_augmentations']
                 if augmentation_config[a]['enabled']]

    num_images = augmentation_config['volume_presets'].get(volume_level, 25)

    results = []

    for _ in range(num_images):

        num_augs = random.randint(1, 3)
        augs = random.choices(available, k=num_augs)

        img = image.copy().resize(target_size)

        for aug in augs:
            img = apply_augmentation(img, aug)

        results.append(img)

    return results