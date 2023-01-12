import fking2.preferences as fkprefs
from fking2.app import FkApp
from fking2.ui import FkFrame

preferences = fkprefs.load_preferences()

app = FkApp(preferences)
ui = FkFrame(app)

ui.show()
