import db
import layout
import ui

version = ui.version()
layout.delivery_rates(db.get_settings(version), db.load_sectors(version))
