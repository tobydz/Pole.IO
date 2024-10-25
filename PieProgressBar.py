from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import Qt

class ProgressPie(QWidget):
    def __init__(self, parent=None, total_images=100):
        super().__init__(parent)
        self.value = 0  # Initial value for the progress
        self.total_images = total_images
        self.setMinimumSize(100, 100)

    def setValue(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Define colors
        outer_ring_color = QColor(80, 80, 80)  # Slightly darker than the background
        inner_circle_color = QColor(100, 100, 100)  # The inner color (even darker)
        border_color = QColor(50, 50, 50)  # Border color

        # Get widget dimensions
        rect = self.rect()
        width = min(rect.width(), rect.height())
        outer_radius = width // 2 - 10  # Outer radius (with some padding)
        inner_radius = outer_radius - 10  # Inner radius to create the ring effect

        # Draw the outer ring
        painter.setPen(Qt.NoPen)
        painter.setBrush(outer_ring_color)
        painter.drawEllipse(rect.center(), outer_radius, outer_radius)

        # Draw the inner circle (empty part of the ring)
        painter.setBrush(inner_circle_color)
        painter.drawEllipse(rect.center(), inner_radius, inner_radius)

        # Draw border (optional, for a subtle modern look)
        pen = QPen(border_color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(rect.center(), outer_radius, outer_radius)

        # Calculate the percentage based on total images
        if self.value > 0:
            progress_percentage = self.value / self.total_images * 100
            
            # Ensure the progress percentage is valid and clamp the span angle
            progress_percentage = max(0, min(progress_percentage, 100))  # Clamp between 0 and 100
            start_angle = 90 * 16  # Start at 90 degrees
            span_angle = -int(progress_percentage / 100 * 360 * 16)  # Span based on percentage
            
            # Ensure span_angle doesn't exceed range
            span_angle = max(-5760, min(span_angle, 5760))  # Clamping to ensure it's within a valid range
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.green)
            painter.drawPie(rect.center().x() - outer_radius, rect.center().y() - outer_radius,
                            2 * outer_radius, 2 * outer_radius, start_angle, span_angle)


        painter.end()