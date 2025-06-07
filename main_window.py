import os
import subprocess

from PySide6.QtWidgets import QPushButton, QMessageBox, QFileDialog, QProgressBar, QScrollArea, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PySide6.QtGui import QPixmap
from PIL import Image
from PIL.ImageQt import ImageQt
from core.pipeline import process_images
from utils.helpers import resize_with_padding
from ui.window import AugmentationWindow
from config.augmentation_config import augmentation_config
from ui.augmentation_selector import AugmentationSelectorDialog

TARGET_SIZE = (128, 128)


class MainWindow(AugmentationWindow):
    def __init__(self):
        super().__init__()

        self.output_dir = None
        self.image_paths = []



        self.progress_bar = QProgressBar()
        self.scroll_area = QScrollArea()
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout()


        style = super()._get_button_style()
        self.load_button.setStyleSheet(style)
        self.select_output_button.setStyleSheet(style)
        self.augment_button.setStyleSheet(style)
        self.open_output_button.setStyleSheet(style)

        self.select_augs_button = QPushButton("Настроить аугментации")
        self.select_augs_button.setFixedHeight(40)
        self.select_augs_button.setStyleSheet(style)
        self.select_augs_button.clicked.connect(self.open_augmentation_selector)

        self.load_button.clicked.connect(self.load_images)
        self.select_output_button.clicked.connect(self.select_output_folder)
        self.augment_button.clicked.connect(self.apply_selected_augmentation)
        self.open_output_button.clicked.connect(self.open_output_directory)


        self.preview_container.setLayout(self.preview_layout)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.preview_container)

        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
            }
        """)

        layout = self.centralWidget().layout()
        layout.addWidget(QLabel("Результаты аугментации:"))
        layout.addWidget(self.scroll_area)
        layout.addWidget(self.progress_bar)
        layout.insertWidget(layout.count() - 1, self.select_augs_button)

    def load_images(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с изображениями")
        if folder_path:
            self.image_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))]
            self.image_count = len(self.image_paths)

            if self.image_count == 0:
                QMessageBox.warning(self, "Ошибка", "Нет изображений в выбранной папке.")
            else:
                self.label.setText(f"Изображений загружено: {self.image_count}")
                self.show_image_preview(self.image_paths[0])
                self.preview_label.clear()
                self.preview_label.setText("После")

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения результатов")
        if folder:
            self.output_dir = folder
            self.info_label.setText(f"Сохранение: {self.output_dir}")

    def open_output_directory(self):
        if self.output_dir and os.path.exists(self.output_dir):
            if os.name == 'nt':
                os.startfile(self.output_dir)
            elif os.name == 'posix':
                subprocess.run(['xdg-open', self.output_dir])
        else:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения результатов.")

    def show_image_preview(self, path):
        image = Image.open(path).convert("L")
        resized = resize_with_padding(image, TARGET_SIZE)
        qimage = ImageQt(resized)
        pixmap = QPixmap.fromImage(qimage)
        self.image_label.setPixmap(pixmap)

    def show_augmented_preview(self, pil_image):
        qimage = ImageQt(pil_image)
        pixmap = QPixmap.fromImage(qimage)
        self.preview_label.setPixmap(pixmap)

    def apply_selected_augmentation(self):
        if not self.image_paths:
            QMessageBox.warning(self, "Ошибка", "Сначала загрузите изображения.")
            return

        if not self.output_dir:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите папку для сохранения результатов.")
            return


        volume_level = self.level_combo.currentText()
        print(f"[DEBUG] Selected volume level: {volume_level}")  # ✅ Отладка

        total_images = len(self.image_paths)
        total_aug_per_image = augmentation_config['volume_presets'].get(volume_level, 25)
        print(f"[DEBUG] Will generate {total_aug_per_image} images per input")  # ✅ Отладка

        self.progress_bar.setMaximum(total_images * total_aug_per_image)
        self.progress_bar.setValue(0)


        for i in reversed(range(self.preview_layout.count())):
            widget = self.preview_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()


        for i, image_path in enumerate(self.image_paths):
            try:
                image = Image.open(image_path).convert("L")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл {image_path}: {e}")
                continue

            resized = resize_with_padding(image, TARGET_SIZE)
            augmented_images = process_images(resized, TARGET_SIZE, volume_level=volume_level)

            base_name = os.path.splitext(os.path.basename(image_path))[0]

            for idx, aug_image in enumerate(augmented_images):
                output_filename = f"{base_name}_aug_{idx:03d}.png"
                output_path = os.path.join(self.output_dir, output_filename)

                try:
                    aug_image.save(output_path)
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл {output_path}: {e}")


                if i == 0 and idx == 0:
                    self.show_augmented_preview(aug_image)


                thumb = aug_image.resize((64, 64))
                qimg = ImageQt(thumb)
                pixmap = QPixmap.fromImage(qimg)
                label = QLabel()
                label.setPixmap(pixmap)
                label.setFixedSize(68, 68)
                label.setStyleSheet("border: 1px solid #ccc; margin: 2px;")
                self.preview_layout.addWidget(label)

                self.progress_bar.setValue(self.progress_bar.value() + 1)

        self.progress_bar.setValue(self.progress_bar.maximum())
        QMessageBox.information(self, "Готово", "Аугментация завершена для всех изображений.")

    def open_augmentation_selector(self):
        available = augmentation_config['available_augmentations']
        selected = [a for a in available if augmentation_config[a]['enabled']]

        dialog = AugmentationSelectorDialog(available, selected)
        if dialog.exec():
            selected_augs = dialog.get_selected_augmentations()

            for aug in available:
                augmentation_config[aug]['enabled'] = aug in selected_augs
