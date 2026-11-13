import db
import layout
import ui

layout.store_page(db.get_settings(ui.version()))
