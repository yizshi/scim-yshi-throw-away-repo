#!/usr/bin/env bash
(
	cd sync_app || return
	export QUART_APP=app:app
	quart --debug run -p 13289 -h 0.0.0.0
)
