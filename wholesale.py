import streamlit as st

import catalog
import db
import layout
import ui

version = ui.version()
s = db.get_settings(version)
products = db.load_products(version)

layout.section_title("Weekly Markaz savings", "Wholesale deals",
                     "This week's discounted items at cash & carry rates. Prices update live.")
deals = products[products.is_deal].copy() if not products.empty else products
if deals.empty:
    st.info("No deals running right now. Check back soon.")
else:
    deals = deals.assign(_save=(deals.mrp - deals.price).clip(lower=0), _in=(deals.stock > 0).astype(int)) \
                 .sort_values(["_in", "_save"], ascending=[False, False])
    catalog.grid(deals, "deal")

st.html('<div style="height:20px"></div>')
layout.section_title("Bulk orders", "Schools, offices, hostels & restaurants",
                     "Buying by the carton? Ask for a bulk quote.")
layout.bulk_request(s)
