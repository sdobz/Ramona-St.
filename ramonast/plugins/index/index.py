#!/usr/bin/env python
# The main index page of the system

from page import page
from plugin_manager import depends_on
depends_on(["theme"])

import applications as apps

urls = (
	"/", "index",
)

class index(page):
	def GET(self):
		app_html=""
		for app in apps.applications:
			app_html += self.render("app_button",
				app.get_pretty_name(),
				app.get_name(),
				app.get_description(),
				app.get_url(),
				app.get_image_url()
			)
		return self.html([],[app_html])

applications = [
apps.BaseApplication(
	pretty_name="Sabnzbd",
	name="sabnzbd",
	description="Usnet downloader extraordinare!"
),
apps.BaseApplication(
	pretty_name="CouchPotato",
	name="couchpotato",
	description="Pirate ALL of the movies"
),
apps.BaseApplication(
	pretty_name="SickBeard",
	name="sickbeard",
	description="Fastest way to fill a hard drive"
),
apps.BaseApplication(
	pretty_name="ruTorrent",
	name="rutorrent",
	description="Torrents? Feh, who needs 'em"
),
apps.BaseApplication(
	pretty_name="Subsonic",
	name="subsonic",
	description="Music streaming, Anywhere"
),
apps.BaseApplication(
	pretty_name="Media",
	name="media",
	description="Media listing"
)
]