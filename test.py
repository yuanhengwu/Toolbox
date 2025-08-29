import os
import sys


if __name__ == "__main__":

    print ('%s debug log. Python version = %s' % (os.path.basename(sys.argv[0]), sys.version))
    print (sys.argv)
