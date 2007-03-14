#!/bin/bash
hdiutil create -imagekey zlib-level=9 -srcfolder dist/server.app dist/server.dmg
