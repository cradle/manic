import pstats
p = pstats.Stats("listenClient-profile.txt")
p.stream = open("listenClient-stats.txt","w+")
p.strip_dirs().sort_stats('time').print_stats(30)
p.strip_dirs().sort_stats('cumulative').print_stats(30)
p.stream.close()
