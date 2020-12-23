
from PyQt5.QtGui import  QColor, QPalette

WHITE = QColor(255, 255, 255)
BLACK = QColor(0, 0, 0)
BRIGHT = QColor(255, 0, 0)
PRIMARY = QColor(53, 53, 53)
SECONDARY = QColor(35, 35, 35)
TERTIARY = QColor(142, 142, 180)

class QDarkPalette(QPalette):
    """Dark palette for a Qt application meant to be used with the Fusion theme."""
    def __init__(self, *__args):
        super().__init__(*__args)

        # Set all the colors based on the constants in globals
        self.setColor(QPalette.Window,          PRIMARY)
        self.setColor(QPalette.WindowText,      WHITE)
        self.setColor(QPalette.Base,            SECONDARY)
        self.setColor(QPalette.AlternateBase,   PRIMARY)
        self.setColor(QPalette.ToolTipBase,     WHITE)
        self.setColor(QPalette.ToolTipText,     WHITE)
        self.setColor(QPalette.Text,            WHITE)
        self.setColor(QPalette.Button,          PRIMARY)
        self.setColor(QPalette.ButtonText,      WHITE)
        self.setColor(QPalette.BrightText,      BRIGHT)
        self.setColor(QPalette.Link,            TERTIARY)
        self.setColor(QPalette.Highlight,       TERTIARY)
        # self.setColor(QPalette.Background,      TERTIARY)
        # self.setColor(QPalette.WindowText,          PRIMARY)
        # self.setColor(QPalette.Base, PRIMARY)
        self.setColor(QPalette.HighlightedText, BLACK)

def reset_colors(mdict):
    global WHITE, BLACK, PRIMARY, SECONDARY, TERTIARY
    for key in mdict.keys():
        globals()[key] = QColor(*mdict[key])
