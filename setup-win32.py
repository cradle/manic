from distutils.core import setup 
import py2exe

setup(
    console=[
        {
            "script" : "client.py",
            "icon_resources" : [(1, "avc.ico")]
            },
        {
            "script" : "server.py",
            "icon_resources" : [(1, "avs.ico")]
            }
        ]
    )
setup(
    windows=[
        {
            "script" : "listenClient.py",
            "icon_resources" : [(1, "av.ico")]
            }
        ]
    ) 
