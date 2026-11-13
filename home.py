import db
import layout
import ui

version = ui.version()
layout.home_shortcuts(db.get_settings(version), db.load_products(version), db.load_sectors(version))
