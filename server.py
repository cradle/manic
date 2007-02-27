import engine
import os

class Server(engine.Engine):
    pass
    

if __name__ == "__main__":
    engine = Server()
    engine.go()
    os._exit(0)
